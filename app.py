from flask import Flask, render_template, jsonify
import psycopg2
from config import DATABASE_URL
from fetch_youtube_data import update_channel_stats

app = Flask(__name__)

def get_data():
    """Retrieve YouTube stats from the database."""
    with psycopg2.connect(DATABASE_URL, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT title, subscribers, views, videos FROM youtube_stats ORDER BY subscribers DESC")
            return [{"Title": row[0], "Subscribers": row[1], "Views": row[2], "Videos": row[3]} for row in cur.fetchall()]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def fetch_data():
    """Return latest YouTube stats."""
    return jsonify(get_data())

@app.route("/update")
def update_data():
    """Manually update YouTube stats."""
    update_channel_stats()
    return jsonify({"status": "updated"})

if __name__ == "__main__":
    app.run(debug=True)
