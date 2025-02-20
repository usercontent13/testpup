import threading
import time
import psycopg2
from flask import Flask, render_template, request, jsonify
from fetch_youtube_data import fetch_and_store_channel_data
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

# Logging function
def log_message(message):
    """Prints a log message with timestamps"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Background Task for Fetching YouTube Data
def fetch_data_task():
    """Fetch and store data using predefined channel IDs from config.py."""
    log_message("Starting background data fetch...")

    if not CHANNEL_IDS:
        log_message("❌ No channel IDs defined in config.py. Exiting...")
        return
    
    for i, channel_id in enumerate(CHANNEL_IDS, start=1):
        log_message(f"🔄 Processing {i}/{len(CHANNEL_IDS)}: {channel_id}")
        
        try:
            fetch_and_store_channel_data([channel_id])  # Process one by one
            log_message(f"✅ Successfully updated: {channel_id}")
        except Exception as e:
            log_message(f"⚠️ Error processing {channel_id}: {str(e)}")

    log_message("🎉 Data update completed!")

# API Route to Fetch New Data Asynchronously
@app.route("/update", methods=["POST"])
def fetch_data():
    """Start the data fetching process asynchronously."""
    thread = threading.Thread(target=fetch_data_task)
    thread.start()
    
    return jsonify({"message": "Data update started in the background!"}), 202  # 202 Accepted

if __name__ == "__main__":
    app.run(debug=True)
