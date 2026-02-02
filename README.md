# Blog – MongoDB & Cassandra Migration

A blog with different authors/commenters, main feed (sort by date or content, author post count), and a **migration strategy** from MongoDB to Cassandra.

## Entity structure (task)

- **user**: id, name, email (authors/commenters)
- **post**: id, user_id, title, content, created_at
- **comment**: id, post_id, user_id, content

**Iteration 2 shape** (API / feed):  
Post: `user_name`, `user_id`, `created_at`, `id`, `content`, **comments**: `[{ user_name, user_id, content }]`.  
News feed: list of posts in that shape; each post shows author (user_name), author’s post count, and (optionally) comments.

**No Docker.** Use local MongoDB and Cassandra (install and run them on your machine).

---

## Setup (no Docker)

### 1. Install MongoDB and Cassandra locally

- **MongoDB**: [Install MongoDB Community](https://www.mongodb.com/docs/manual/installation/) – default port `27017`.
- **Cassandra**: [Apache Cassandra](https://cassandra.apache.org/doc/latest/cassandra/getting_started/installing.html) – default port `9042`.

### 2. Python env

```bash
cd mongodb_cassandra_blog
pip install -r requirements.txt
```

---

## Run the blog

```bash
# Default: read and write MongoDB only
python app.py
```

Open http://127.0.0.1:5000

- **Main feed** – sort by **date** (newest first) or **content** (A–Z). Each post shows **author name** and **author’s number of posts**.
- **Users** – add authors/commenters.
- **New post** – create a post (need a user id from Users).
- **Post page** – view post and add comments.

---

## Migration strategy

Control behaviour with env vars (or edit `config.py`):

| Phase              | READ_SOURCE     | WRITE_BOTH | Behaviour |
|--------------------|-----------------|------------|-----------|
| 1. MongoDB only    | `mongodb_only`  | -          | Read/write MongoDB only (default). |
| 2. Double writes   | `double_write`  | -          | Read from MongoDB; write to **both** MongoDB and Cassandra. |
| 3. Migration script| -               | -          | Run `python migrate_mongo_to_cassandra.py` to copy existing MongoDB data to Cassandra. |
| 4. Read migration  | `read_migration`| -          | Read from **Cassandra**; write to both. |
| 5. Cleanup         | `cassandra_only`| -          | Read/write **Cassandra** only; remove MongoDB code when done. |

### 1. Double writes

```bash
set READ_SOURCE=double_write
python app.py
```

All new writes go to both MongoDB and Cassandra. Reads still come from MongoDB.

### 2. Migration script (copy existing data to Cassandra)

Ensure Cassandra is running and schema exists (the app or script will create it when writing).

```bash
python migrate_mongo_to_cassandra.py
```

This copies users, posts, and comments from MongoDB to Cassandra (with id mapping for relations).

### 3. Read migration

```bash
set READ_SOURCE=read_migration
python app.py
```

Reads use Cassandra; writes still go to both. Verify feed, users, posts, comments.

### 4. Cleanup (Cassandra only)

```bash
set READ_SOURCE=cassandra_only
python app.py
```

Then remove MongoDB-related code (see `cleanup_remove_mongodb.py`):

- Delete `db_mongo.py`
- In `config.py`: drop MongoDB options and keep only Cassandra.
- In `db.py`: call only `db_cassandra.*`.
- In `requirements.txt`: remove `pymongo`.

---

## Config (env or `config.py`)

- `MONGODB_URI` – default `mongodb://localhost:27017/`
- `MONGODB_DB` – default `blog`
- `CASSANDRA_HOSTS` – default `127.0.0.1` (comma-separated for multiple)
- `CASSANDRA_KEYSPACE` – default `blog`
- `READ_SOURCE` – `mongodb_only` | `double_write` | `read_migration` | `cassandra_only`

---

## API (optional)

- `POST /api/users` – body `{"name":"...", "email":"..."}`
- `POST /api/posts` – body `{"user_id":"...", "title":"...", "content":"..."}`
- `GET /api/feed?sort=date|content` – main feed JSON

---

## Summary

- **Blog**: MongoDB (or Cassandra after migration); authors, commenters, posts, comments.
- **Main feed**: Sort by date or content; show author name and author’s post count.
- **Migration**: Double writes → migration script → read from Cassandra → cleanup MongoDB.
