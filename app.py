from flask import Flask, render_template, request, jsonify
from fetch_youtube_data import fetch_and_store_channel_data
import psycopg2
from config import DATABASE_URL, CHANNEL_IDS  # Import CHANNEL_IDS

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

@app.route("/data")
def get_data():
    """Fetch data from the database and send it to the frontend."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT title, subscribers, views, videos FROM youtube_stats ORDER BY subscribers DESC;")
    data = [{"Title": row[0], "Subscribers": row[1], "Views": row[2], "Videos": row[3]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()

    return jsonify(data)

# API Route to Fetch New Data
@app.route("/update", methods=["POST"])
def fetch_data():
    """Fetch and store data using predefined channel IDs from config.py."""
    if not CHANNEL_IDS:
        return jsonify({"error": "No channel IDs defined in config.py"}), 400

    fetch_and_store_channel_data(CHANNEL_IDS)
    return jsonify({"message": "Data updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
