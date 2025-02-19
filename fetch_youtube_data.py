import psycopg2
import requests
from config import API_KEY, DATABASE_URL, CHANNEL_IDS

def connect_db():
    """Create a database connection."""
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def setup_table():
    """Create the YouTube stats table if not exists."""
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS youtube_stats (
                    id SERIAL PRIMARY KEY,
                    channel_id TEXT UNIQUE,
                    title TEXT,
                    subscribers BIGINT,
                    views BIGINT,
                    videos BIGINT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

def get_channel_stats(channel_id):
    """Fetch YouTube channel statistics."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "snippet,statistics", "id": channel_id, "key": API_KEY}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            return {
                "channel_id": channel_id,
                "title": item["snippet"]["title"],
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "views": int(item["statistics"].get("viewCount", 0)),
                "videos": int(item["statistics"].get("videoCount", 0)),
            }
    return None

def update_channel_stats():
    """Fetch latest stats and update the database."""
    setup_table()
    with connect_db() as conn:
        with conn.cursor() as cur:
            for channel_id in CHANNEL_IDS:
                data = get_channel_stats(channel_id)
                if data:
                    cur.execute("""
                        INSERT INTO youtube_stats (channel_id, title, subscribers, views, videos)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (channel_id) 
                        DO UPDATE SET
                            title = EXCLUDED.title,
                            subscribers = EXCLUDED.subscribers,
                            views = EXCLUDED.views,
                            videos = EXCLUDED.videos,
                            last_updated = CURRENT_TIMESTAMP
                    """, (data["channel_id"], data["title"], data["subscribers"], data["views"], data["videos"]))
            conn.commit()

if __name__ == "__main__":
    update_channel_stats()
