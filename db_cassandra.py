"""Cassandra access: same schema as MongoDB for migration."""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

from config import CASSANDRA_HOSTS, CASSANDRA_KEYSPACE

_session = None


def get_cassandra_session():
    global _session
    if _session is None:
        cassandra_init_schema()
    return _session


def cassandra_init_schema(session=None):
    """Create keyspace and tables if not exist."""
    global _session
    if session is None and _session is None:
        cluster = Cluster(CASSANDRA_HOSTS)
        _session = cluster.connect()
    s = session or _session
    s.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)
    s.set_keyspace(CASSANDRA_KEYSPACE)
    s.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id text PRIMARY KEY,
            name text,
            email text,
            created_at timestamp
        )
    """)
    s.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id text PRIMARY KEY,
            user_id text,
            title text,
            content text,
            created_at timestamp
        )
    """)
    s.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id text PRIMARY KEY,
            post_id text,
            user_id text,
            content text,
            created_at timestamp
        )
    """)
    try:
        s.execute(f"CREATE INDEX IF NOT EXISTS ON {CASSANDRA_KEYSPACE}.comments (post_id)")
    except Exception:
        pass
    try:
        s.execute(f"CREATE INDEX IF NOT EXISTS ON {CASSANDRA_KEYSPACE}.posts (user_id)")
    except Exception:
        pass


# --- Users ---

def cassandra_create_user(name: str, email: str) -> dict:
    s = get_cassandra_session()
    uid = str(uuid4())
    s.execute(
        "INSERT INTO users (id, name, email, created_at) VALUES (%s, %s, %s, %s)",
        (uid, name, email, datetime.utcnow()),
    )
    return {"id": uid, "name": name, "email": email}


def cassandra_list_users() -> list[dict]:
    s = get_cassandra_session()
    rows = list(s.execute("SELECT id, name, email, created_at FROM users"))
    return [{"id": r.id, "name": r.name, "email": r.email} for r in rows]


def cassandra_get_user(user_id: str) -> Optional[dict]:
    s = get_cassandra_session()
    row = s.execute("SELECT id, name, email, created_at FROM users WHERE id = %s", (user_id,)).one()
    if not row:
        return None
    return {"id": row.id, "name": row.name, "email": row.email, "created_at": row.created_at}


def cassandra_count_posts_by_user(user_id: str) -> int:
    s = get_cassandra_session()
    rows = list(s.execute("SELECT id FROM posts WHERE user_id = %s ALLOW FILTERING", (user_id,)))
    return len(rows)


# --- Posts ---

def cassandra_create_post(user_id: str, title: str, content: str) -> dict:
    s = get_cassandra_session()
    pid = str(uuid4())
    s.execute(
        "INSERT INTO posts (id, user_id, title, content, created_at) VALUES (%s, %s, %s, %s, %s)",
        (pid, user_id, title, content, datetime.utcnow()),
    )
    return {"id": pid, "user_id": user_id, "title": title, "content": content}


def cassandra_get_post(post_id: str) -> Optional[dict]:
    s = get_cassandra_session()
    row = s.execute(
        "SELECT id, user_id, title, content, created_at FROM posts WHERE id = %s",
        (post_id,),
    ).one()
    if not row:
        return None
    return {
        "id": row.id,
        "user_id": row.user_id,
        "title": row.title,
        "content": row.content,
        "created_at": row.created_at,
    }


def cassandra_list_posts_sort_by_date(limit: int = 50) -> list[dict]:
    s = get_cassandra_session()
    rows = s.execute(
        "SELECT id, user_id, title, content, created_at FROM posts LIMIT %s",
        (limit,),
    )
    posts = list(rows)
    posts.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    return [
        {"id": r.id, "user_id": r.user_id, "title": r.title, "content": r.content, "created_at": r.created_at}
        for r in posts[:limit]
    ]


def cassandra_list_posts_sort_by_content(limit: int = 50) -> list[dict]:
    s = get_cassandra_session()
    rows = list(s.execute("SELECT id, user_id, title, content, created_at FROM posts"))
    rows.sort(key=lambda r: (r.content or "").lower())
    return [
        {"id": r.id, "user_id": r.user_id, "title": r.title, "content": r.content, "created_at": r.created_at}
        for r in rows[:limit]
    ]


# --- Comments ---

def cassandra_create_comment(post_id: str, user_id: str, content: str) -> dict:
    s = get_cassandra_session()
    cid = str(uuid4())
    s.execute(
        "INSERT INTO comments (id, post_id, user_id, content, created_at) VALUES (%s, %s, %s, %s, %s)",
        (cid, post_id, user_id, content, datetime.utcnow()),
    )
    return {"id": cid, "post_id": post_id, "user_id": user_id, "content": content}


def cassandra_get_comments_for_post(post_id: str) -> list[dict]:
    s = get_cassandra_session()
    rows = list(s.execute(
        "SELECT id, post_id, user_id, content, created_at FROM comments WHERE post_id = %s",
        (post_id,),
    ))
    rows.sort(key=lambda r: r.created_at or datetime.min)
    return [
        {"id": r.id, "post_id": r.post_id, "user_id": r.user_id, "content": r.content, "created_at": r.created_at}
        for r in rows
    ]


def cassandra_feed_posts(sort_by: str = "date", limit: int = 50) -> list[dict]:
    if sort_by == "content":
        posts = cassandra_list_posts_sort_by_content(limit=limit)
    else:
        posts = cassandra_list_posts_sort_by_date(limit=limit)
    for p in posts:
        p["author_post_count"] = cassandra_count_posts_by_user(p["user_id"])
        author = cassandra_get_user(p["user_id"])
        p["author_name"] = author["name"] if author else "Unknown"
        p["user_name"] = p["author_name"]
    return posts
