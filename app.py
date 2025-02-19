from flask import Flask, render_template, request, jsonify
from fetch_youtube_data import fetch_and_store_channel_data
import psycopg2
from config import DATABASE_URL

app = Flask(__name__)

# Get database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Home Route (Dashboard)
@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT channel_id, title, subscribers, views, videos FROM youtube_stats ORDER BY subscribers DESC;")
    channels = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template("index.html", channels=channels)

# API Route to Fetch New Data
@app.route("/fetch", methods=["POST"])
def fetch_data():
    data = request.json
    channel_ids = data.get("channel_ids", [])

    if not channel_ids:
        return jsonify({"error": "No channel IDs provided"}), 400

    fetch_and_store_channel_data(channel_ids)
    return jsonify({"message": "Data updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
