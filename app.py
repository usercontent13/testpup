import threading
import time
from flask import Flask, render_template, request, jsonify
from fetch_youtube_data import fetch_and_store_channel_data
import psycopg2
from config import DATABASE_URL, CHANNEL_IDS

app = Flask(__name__)

# Global lock to ensure only one update runs at a time
queue_lock = threading.Lock()

# Update status tracking
update_status = {"updating": False, "progress": 0, "message": "Idle"}

# Get database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Home Route (Dashboard)
@app.route("/")
def index():
    return render_template("index.html")

# Fetch Data Route
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
    total_subscribers = 0
    total_views = 0
    total_videos = 0

    for row in cur.fetchall():
        title, subscribers, prev_subscribers, views, prev_views, videos, prev_videos = row

        # Compute changes
        sub_change = subscribers - prev_subscribers if prev_subscribers else 0
        views_change = views - prev_views if prev_views else 0
        videos_change = videos - prev_videos if prev_videos else 0

        total_subscribers += subscribers
        total_views += views
        total_videos += videos

        # Format trends
        def format_change(value, change):
            if change > 0:
                return f"{value} ⬆{change}"
            elif change < 0:
                return f"{value} ⬇{abs(change)}"
            else:
                return f"{value}"

        data.append({
            "Title": title,
            "Subscribers": format_change(subscribers, sub_change),
            "Views": format_change(views, views_change),
            "Videos": format_change(videos, videos_change),
        })

    cur.close()
    conn.close()

    return jsonify({
        "channels": data,
        "totalSubscribers": total_subscribers,
        "totalViews": total_views,
        "totalVideos": total_videos
    })

# API Route to Fetch New Data Asynchronously
@app.route("/update", methods=["POST"])
def fetch_data():
    """Fetch and store data in the background using threading."""
    if not CHANNEL_IDS:
        return jsonify({"error": "No channel IDs defined in config.py"}), 400

    if update_status["updating"]:
        return jsonify({"message": "Update already in progress!"}), 429  # Too Many Requests

    def background_fetch():
        global update_status

        with queue_lock:  # Ensure only one thread runs at a time
            update_status["updating"] = True
            update_status["progress"] = 0
            update_status["message"] = "Fetching data..."

            total_batches = len(CHANNEL_IDS) // 5 + (1 if len(CHANNEL_IDS) % 5 else 0)

            for i in range(0, len(CHANNEL_IDS), 5):
                batch = CHANNEL_IDS[i:i + 5]
                print(f"🔄 Processing batch {i//5 + 1}/{total_batches}: {batch}")
                
                fetch_and_store_channel_data(batch)
                
                update_status["progress"] = int(((i + 5) / len(CHANNEL_IDS)) * 100)
                update_status["message"] = f"Processed batch {i//5 + 1}/{total_batches}"

                time.sleep(2)  # Simulate processing delay

            update_status["progress"] = 100
            update_status["message"] = "Update completed!"
            update_status["updating"] = False
            print("✅ Data update completed!")

    # Run the function in a separate thread
    thread = threading.Thread(target=background_fetch)
    thread.start()

    return jsonify({"message": "Data update started in the background!"}), 202  # 202 Accepted

# API to check update progress
@app.route("/update_status")
def check_update_status():
    return jsonify(update_status)

if __name__ == "__main__":
    app.run(debug=True)
