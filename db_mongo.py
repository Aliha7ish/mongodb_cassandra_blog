"""MongoDB access: users, posts, comments."""

from datetime import datetime
from typing import Any, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING

from config import MONGODB_DB, MONGODB_URI


def get_mongo_client() -> MongoClient:
    return MongoClient(MONGODB_URI)


def get_db():
    return get_mongo_client()[MONGODB_DB]


# --- Users (authors / commenters) ---

def mongo_create_user(name: str, email: str) -> dict:
    db = get_db()
    doc = {"name": name, "email": email, "created_at": datetime.utcnow()}
    r = db.users.insert_one(doc)
    doc["_id"] = r.inserted_id
    doc["id"] = str(r.inserted_id)
    return doc


def mongo_list_users() -> list[dict]:
    users = []
    for doc in get_db().users.find():
        doc["id"] = str(doc["_id"])
        users.append(doc)
    return users


def mongo_get_user(user_id: str) -> Optional[dict]:
    from bson import ObjectId
    try:
        doc = get_db().users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    return doc


def mongo_count_posts_by_user(user_id: str) -> int:
    return get_db().posts.count_documents({"user_id": user_id})


# --- Posts ---

def mongo_create_post(user_id: str, title: str, content: str) -> dict:
    db = get_db()
    doc = {
        "user_id": user_id,
        "title": title,
        "content": content,
        "created_at": datetime.utcnow(),
    }
    r = db.posts.insert_one(doc)
    doc["_id"] = r.inserted_id
    doc["id"] = str(r.inserted_id)
    return doc


def mongo_get_post(post_id: str) -> Optional[dict]:
    from bson import ObjectId
    try:
        doc = get_db().posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    return doc


def mongo_list_posts_sort_by_date(limit: int = 50) -> list[dict]:
    db = get_db()
    cursor = db.posts.find().sort("created_at", DESCENDING).limit(limit)
    posts = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        posts.append(doc)
    return posts


def mongo_list_posts_sort_by_content(limit: int = 50) -> list[dict]:
    db = get_db()
    cursor = db.posts.find().sort("content", ASCENDING).limit(limit)
    posts = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        posts.append(doc)
    return posts


# --- Comments ---

def mongo_create_comment(post_id: str, user_id: str, content: str) -> dict:
    db = get_db()
    doc = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "created_at": datetime.utcnow(),
    }
    r = db.comments.insert_one(doc)
    doc["_id"] = r.inserted_id
    doc["id"] = str(r.inserted_id)
    return doc


def mongo_get_comments_for_post(post_id: str) -> list[dict]:
    cursor = get_db().comments.find({"post_id": post_id}).sort("created_at", ASCENDING)
    comments = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        comments.append(doc)
    return comments


# --- Main feed helpers ---

def mongo_feed_posts(sort_by: str = "date", limit: int = 50) -> list[dict]:
    if sort_by == "content":
        posts = mongo_list_posts_sort_by_content(limit=limit)
    else:
        posts = mongo_list_posts_sort_by_date(limit=limit)
    for p in posts:
        p["author_post_count"] = mongo_count_posts_by_user(p["user_id"])
        author = mongo_get_user(p["user_id"])
        p["author_name"] = author["name"] if author else "Unknown"
        p["user_name"] = p["author_name"]
    return posts
