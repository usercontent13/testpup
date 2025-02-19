import os
import requests
import time
import psycopg2
from tqdm import tqdm
from config import DATABASE_URL, API_KEY

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Resolve YouTube Handle to Channel ID
def resolve_handle_to_id(handle):
    """Convert YouTube handle (@username) to channel ID."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {"part": "snippet", "q": handle, "type": "channel", "key": API_KEY}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("items"):
            return data["items"][0]["id"]["channelId"]
    except requests.RequestException as e:
        print(f"Error resolving {handle}: {e}")
    return None

# Fetch Channel Stats
def get_channel_stats(channel_ids):
    """Fetch channel statistics in batches."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    all_stats = []

    for i in range(0, len(channel_ids), 5):  # Process in batches of 5
        batch = channel_ids[i:i+5]
        print(f"Processing batch: {batch}")
        
        resolved_ids = [resolve_handle_to_id(ch) if ch.startswith("@") else ch for ch in batch]
        resolved_ids = [ch for ch in resolved_ids if ch]  # Remove None values

        params = {"part": "snippet,statistics", "id": ",".join(resolved_ids), "key": API_KEY}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("items", []):
                snippet = item["snippet"]
                statistics = item["statistics"]
                all_stats.append({
                    "channel_id": item["id"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "subscribers": statistics.get("subscriberCount", "0"),
                    "views": statistics.get("viewCount", "0"),
                    "videos": statistics.get("videoCount", "0"),
                })
            
        except requests.RequestException as e:
            print(f"Error fetching batch {batch}: {e}")
        
        time.sleep(2)  # Prevent API rate limits

    return all_stats

# Save Data to Database
def save_to_db(channel_stats):
    """Store fetched channel statistics in PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS youtube_stats (
        id SERIAL PRIMARY KEY,
        channel_id TEXT UNIQUE,
        title TEXT,
        description TEXT,
        subscribers BIGINT,
        views BIGINT,
        videos BIGINT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")


    for channel in channel_stats:
        cur.execute("""
    INSERT INTO youtube_stats (channel_id, title, description, subscribers, views, videos)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (channel_id) DO UPDATE 
    SET subscribers = EXCLUDED.subscribers, views = EXCLUDED.views, videos = EXCLUDED.videos;
""", (channel["channel_id"], channel["title"], channel["description"], channel["subscribers"], channel["views"], channel["videos"]))


    conn.commit()
    cur.close()
    conn.close()

# Main Function to Fetch and Save Data
def fetch_and_store_channel_data(channel_ids):
    stats = get_channel_stats(channel_ids)
    save_to_db(stats)
    return stats
