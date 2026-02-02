"""
Migration script: copy existing data from MongoDB to Cassandra.

Run after Cassandra is set up and schema is created.
Usage:
  python migrate_mongo_to_cassandra.py

Requires: MongoDB running (with existing data), Cassandra running.
"""

import sys
from pathlib import Path

# Add project root
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import db_mongo
import db_cassandra
from config import MONGODB_DB, MONGODB_URI


def main():
    # Init Cassandra schema (creates keyspace + tables, sets session for db_cassandra)
    db_cassandra.cassandra_init_schema()

    # Map MongoDB _id (ObjectId) -> Cassandra id (we use new UUIDs and map by order or by storing mapping)
    user_id_map = {}  # mongo_id_str -> cassandra_id
    post_id_map = {}

    # 1. Users
    db = db_mongo.get_db()
    for doc in db.users.find():
        mongo_id = str(doc["_id"])
        name = doc.get("name", "")
        email = doc.get("email", "")
        cassandra_user = db_cassandra.cassandra_create_user(name, email)
        user_id_map[mongo_id] = cassandra_user["id"]
    print(f"Migrated {len(user_id_map)} users")

    # 2. Posts
    for doc in db.posts.find():
        mongo_id = str(doc["_id"])
        user_id = user_id_map.get(doc.get("user_id", ""), doc.get("user_id", ""))
        title = doc.get("title", "")
        content = doc.get("content", "")
        cassandra_post = db_cassandra.cassandra_create_post(user_id, title, content)
        post_id_map[mongo_id] = cassandra_post["id"]
    print(f"Migrated {len(post_id_map)} posts")

    # 3. Comments (post_id and user_id mapped to Cassandra ids)
    count = 0
    for doc in db.comments.find():
        post_id = post_id_map.get(str(doc.get("post_id", "")), str(doc.get("post_id", "")))
        user_id = user_id_map.get(str(doc.get("user_id", "")), str(doc.get("user_id", "")))
        content = doc.get("content", "")
        db_cassandra.cassandra_create_comment(post_id, user_id, content)
        count += 1
    print(f"Migrated {count} comments")

    print("Migration done. Set READ_SOURCE=read_migration to read from Cassandra.")


if __name__ == "__main__":
    main()
