"""Flask blog: authors, commenters, main feed (sort by date / content, author post count)."""

from flask import Flask, request, jsonify, render_template_string

import db

app = Flask(__name__)

NAV = """
  <h1>Blog</h1>
  <nav>
    <a href="/">Main feed (date)</a> |
    <a href="/?sort=content">Main feed (content A-Z)</a> |
    <a href="/users">Users</a> |
    <a href="/posts/new">New post</a>
  </nav>
  <hr>
"""

FEED_HTML = """
<!DOCTYPE html>
<html>
<head><title>Blog – Main feed</title></head>
<body>
""" + NAV + """
  <h2>Main feed (sorted by {{ sort_label }})</h2>
  {% for p in posts %}
  <article style="border:1px solid #ccc; margin:10px 0; padding:10px;">
    <h3>{{ p.title }}</h3>
    <p><strong>Author:</strong> {{ p.author_name }} ({{ p.author_post_count }} posts)</p>
    <p>{{ p.content }}</p>
    <p><small>Posted {{ p.created_at }}</small></p>
    <a href="/post/{{ p.id }}">View & comment</a>
  </article>
  {% endfor %}
</body>
</html>
"""

POST_HTML = """
<!DOCTYPE html>
<html>
<head><title>Blog – Post</title></head>
<body>
""" + NAV + """
  {% if post %}
  <article style="border:1px solid #ccc; padding:15px;">
    <h2>{{ post.title }}</h2>
    <p><strong>Author:</strong> {{ post.author_name }} ({{ post.author_post_count }} posts)</p>
    <p>{{ post.content }}</p>
    <p><small>{{ post.created_at }}</small></p>
  </article>
  <h3>Comments</h3>
  {% for c in comments %}
  <p><strong>{{ c.author_name }}</strong>: {{ c.content }}</p>
  {% endfor %}
  <form method="post" action="/post/{{ post.id }}/comment">
    <input type="text" name="user_id" placeholder="User ID" required>
    <input type="text" name="content" placeholder="Comment" required>
    <button type="submit">Add comment</button>
  </form>
  {% else %}
  <p>Post not found.</p>
  {% endif %}
</body>
</html>
"""

USERS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Blog – Users</title></head>
<body>
""" + NAV + """
  <h2>Users (authors / commenters)</h2>
  <ul>
  {% for u in users %}
  <li>{{ u.name }} &lt;{{ u.email }}&gt; [id: {{ u.id }}]</li>
  {% endfor %}
  </ul>
  <form method="post" action="/users">
    <input type="text" name="name" placeholder="Name" required>
    <input type="email" name="email" placeholder="Email" required>
    <button type="submit">Add user</button>
  </form>
</body>
</html>
"""


@app.route("/")
def main_feed():
    sort_by = request.args.get("sort", "date")
    if sort_by == "content":
        sort_label = "content (A-Z)"
    else:
        sort_label = "date (newest first)"
    posts = db.feed_posts(sort_by=sort_by, limit=50)
    for p in posts:
        p["created_at"] = str(p.get("created_at", ""))
    return render_template_string(FEED_HTML, posts=posts, sort_label=sort_label)


@app.route("/post/<post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    post = db.get_post(post_id)
    if not post:
        return "Post not found", 404
    author = db.get_user(post["user_id"])
    post["author_name"] = author["name"] if author else "Unknown"
    post["author_post_count"] = db.count_posts_by_user(post["user_id"])
    post["created_at"] = str(post.get("created_at", ""))
    comments = db.get_comments_for_post(post_id)
    for c in comments:
        u = db.get_user(c["user_id"])
        c["author_name"] = u["name"] if u else "Unknown"
        c["user_name"] = c["author_name"]
        c["created_at"] = str(c.get("created_at", ""))
    return render_template_string(POST_HTML, post=post, comments=comments)


@app.route("/post/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    user_id = request.form.get("user_id", "").strip()
    content = request.form.get("content", "").strip()
    if not user_id or not content:
        return "user_id and content required", 400
    db.create_comment(post_id, user_id, content)
    return __import__("flask").redirect(f"/post/{post_id}")


@app.route("/posts/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if user_id and title:
            db.create_post(user_id, title, content)
            return __import__("flask").redirect("/")
    users_list = db.list_users()
    new_post_html = """
<!DOCTYPE html>
<html>
<head><title>Blog – New post</title></head>
<body>
""" + NAV + """
  <h2>New post</h2>
  <form method="post" action="/posts/new">
    <p><label>Author (user id): <input type="text" name="user_id" required></label></p>
    <p><label>Title: <input type="text" name="title" required></label></p>
    <p><label>Content: <textarea name="content" rows="4"></textarea></label></p>
    <button type="submit">Create post</button>
  </form>
  <p>User IDs: {% for u in users %}{{ u.id }} ({{ u.name }}) {% endfor %}</p>
</body>
</html>
"""
    return render_template_string(new_post_html, users=users_list)


@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if name and email:
            db.create_user(name, email)
        return __import__("flask").redirect("/users")
    users_list = db.list_users()
    return render_template_string(USERS_HTML, users=users_list)


# --- API for programmatic use ---

@app.route("/api/users", methods=["POST"])
def api_create_user():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    if not name or not email:
        return jsonify({"error": "name and email required"}), 400
    user = db.create_user(name, email)
    return jsonify(user), 201


@app.route("/api/posts", methods=["POST"])
def api_create_post():
    data = request.get_json() or {}
    user_id = data.get("user_id", "").strip()
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    if not user_id or not title:
        return jsonify({"error": "user_id and title required"}), 400
    post = db.create_post(user_id, title, content or "")
    return jsonify(post), 201


@app.route("/api/feed")
def api_feed():
    """Main feed: list of posts. Each post has user_name, user_id, created_at, id, content, author_post_count (Iteration 2)."""
    sort_by = request.args.get("sort", "date")
    include_comments = request.args.get("comments", "").lower() in ("1", "true", "yes")
    posts = db.feed_posts(sort_by=sort_by, limit=50)
    out = []
    for p in posts:
        o = {
            "id": p.get("id"),
            "user_id": p.get("user_id"),
            "user_name": p.get("user_name", p.get("author_name", "Unknown")),
            "created_at": str(p.get("created_at", "")),
            "content": p.get("content", ""),
            "title": p.get("title", ""),
            "author_post_count": p.get("author_post_count", 0),
        }
        if include_comments:
            full = db.get_post_with_comments(p["id"])
            o["comments"] = full["comments"] if full else []
        out.append(o)
    return jsonify({"posts": out})


@app.route("/api/post/<post_id>")
def api_post_detail(post_id):
    """Single post in Iteration 2 shape: user_name, user_id, created_at, id, content, comments (user_name, user_id, content)."""
    post = db.get_post_with_comments(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    post["created_at"] = str(post.get("created_at", ""))
    return jsonify(post)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
