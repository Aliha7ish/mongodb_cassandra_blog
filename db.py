"""Unified DB layer: routes to MongoDB or Cassandra based on config (migration strategy)."""

from config import (
    read_from_mongodb,
    read_from_cassandra,
    write_to_mongodb,
    write_to_cassandra,
)
import db_mongo
import db_cassandra


# --- Users ---

def create_user(name: str, email: str) -> dict:
    out = None
    if write_to_mongodb():
        out = db_mongo.mongo_create_user(name, email)
    if write_to_cassandra():
        c_out = db_cassandra.cassandra_create_user(name, email)
        if out is None:
            out = c_out
        else:
            db_cassandra.cassandra_create_user(name, email)
    return out or db_cassandra.cassandra_create_user(name, email)


def list_users() -> list:
    if read_from_mongodb():
        return db_mongo.mongo_list_users()
    return db_cassandra.cassandra_list_users()


def get_user(user_id: str):
    if read_from_mongodb():
        u = db_mongo.mongo_get_user(user_id)
        if u:
            return u
    if read_from_cassandra():
        return db_cassandra.cassandra_get_user(user_id)
    return None


def count_posts_by_user(user_id: str) -> int:
    if read_from_mongodb():
        return db_mongo.mongo_count_posts_by_user(user_id)
    return db_cassandra.cassandra_count_posts_by_user(user_id)


# --- Posts ---

def create_post(user_id: str, title: str, content: str) -> dict:
    out = None
    if write_to_mongodb():
        out = db_mongo.mongo_create_post(user_id, title, content)
    if write_to_cassandra():
        c_out = db_cassandra.cassandra_create_post(user_id, title, content)
        if out is None:
            out = c_out
        else:
            db_cassandra.cassandra_create_post(user_id, title, content)
    return out or db_cassandra.cassandra_create_post(user_id, title, content)


def get_post(post_id: str):
    if read_from_mongodb():
        p = db_mongo.mongo_get_post(post_id)
        if p:
            return p
    if read_from_cassandra():
        return db_cassandra.cassandra_get_post(post_id)
    return None


# --- Comments ---

def create_comment(post_id: str, user_id: str, content: str) -> dict:
    out = None
    if write_to_mongodb():
        out = db_mongo.mongo_create_comment(post_id, user_id, content)
    if write_to_cassandra():
        c_out = db_cassandra.cassandra_create_comment(post_id, user_id, content)
        if out is None:
            out = c_out
        else:
            db_cassandra.cassandra_create_comment(post_id, user_id, content)
    return out or db_cassandra.cassandra_create_comment(post_id, user_id, content)


def get_comments_for_post(post_id: str) -> list:
    if read_from_mongodb():
        c = db_mongo.mongo_get_comments_for_post(post_id)
        if c is not None:
            return c
    if read_from_cassandra():
        return db_cassandra.cassandra_get_comments_for_post(post_id)
    return []


# --- Main feed ---

def get_post_with_comments(post_id: str) -> dict | None:
    """Return post in Iteration 2 shape: user_name, user_id, created_at, id, content, comments (user_name, user_id, content)."""
    post = get_post(post_id)
    if not post:
        return None
    author = get_user(post["user_id"])
    post["user_name"] = author["name"] if author else "Unknown"
    post["author_name"] = post["user_name"]
    post["author_post_count"] = count_posts_by_user(post["user_id"])
    comments = get_comments_for_post(post_id)
    post["comments"] = []
    for c in comments:
        u = get_user(c["user_id"])
        post["comments"].append({
            "user_id": c["user_id"],
            "user_name": u["name"] if u else "Unknown",
            "content": c["content"],
        })
    return post


def feed_posts(sort_by: str = "date", limit: int = 50) -> list:
    if read_from_mongodb():
        return db_mongo.mongo_feed_posts(sort_by=sort_by, limit=limit)
    return db_cassandra.cassandra_feed_posts(sort_by=sort_by, limit=limit)
