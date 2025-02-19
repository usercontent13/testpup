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
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT title, subscribers, prev_subscribers, views, prev_views, videos, prev_videos 
        FROM youtube_stats 
        ORDER BY subscribers DESC;
    """)
    
    data = []
    for row in cur.fetchall():
        title, subscribers, prev_subscribers, views, prev_views, videos, prev_videos = row

        # Compute change
        sub_change = subscribers - prev_subscribers if prev_subscribers else 0
        views_change = views - prev_views if prev_views else 0
        videos_change = videos - prev_videos if prev_videos else 0

        # Prepare the response
        data.append({
            "Title": title,
            "Subscribers": f"{subscribers} {'⬆'+str(sub_change) if sub_change > 0 else '⬇'+str(abs(sub_change)) if sub_change < 0 else ''}",
            "Views": f"{views} {'⬆'+str(views_change) if views_change > 0 else '⬇'+str(abs(views_change)) if views_change < 0 else ''}",
            "Videos": f"{videos} {'⬆'+str(videos_change) if videos_change > 0 else '⬇'+str(abs(videos_change)) if videos_change < 0 else ''}",
        })
    
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
