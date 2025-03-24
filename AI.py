import streamlit as st
import requests
import time  # Added for retry mechanism
from datetime import datetime, timedelta

# Use Streamlit secrets for security
API_KEY = st.secrets["YOUTUBE_API_KEY"]
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# Keywords
keywords = [
    "Affair Relationship Stories", "Reddit Update", "Reddit Relationship Advice", "Reddit Relationship",
    "Reddit Cheating", "AITA Update", "Open Marriage", "Open Relationship", "X BF Caught",
    "Stories Cheat", "X GF Reddit", "AskReddit Surviving Infidelity", "GurlCan Reddit",
    "Cheating Story Actually Happened", "Cheating Story Real", "True Cheating Story",
    "Reddit Cheating Story", "R/Surviving Infidelity", "Surviving Infidelity",
    "Reddit Marriage", "Wife Cheated I Can't Forgive", "Reddit AP", "Exposed Wife",
    "Cheat Exposed"
]

# Debugging Log
def debug_log(message):
    st.text(f"DEBUG: {message}")

# API request function with error handling
def fetch_api(url, params):
    for _ in range(3):  # Retry 3 times
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            st.error("API quota exceeded or access forbidden.")
            return None
        else:
            debug_log(f"API error {response.status_code}: {response.text}")
            time.sleep(2)  # Wait and retry
    return None

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        # Date range for search
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        # Iterate over keywords
        for keyword in keywords:
            debug_log(f"Searching for keyword: {keyword}")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            data = fetch_api(YOUTUBE_SEARCH_URL, search_params)
            if not data or "items" not in data:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"].get("videoId") for video in videos if "id" in video]
            channel_ids = [video["snippet"].get("channelId") for video in videos if "snippet" in video]

            video_ids = [vid for vid in video_ids if vid]  # Remove None values
            channel_ids = [cid for cid in channel_ids if cid]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing data.")
                continue

            # Fetch video stats
            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_data = fetch_api(YOUTUBE_VIDEO_URL, stats_params)
            if not stats_data or "items" not in stats_data:
                st.warning(f"Failed to fetch video statistics for keyword: {keyword}")
                continue

            # Fetch channel stats
            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_data = fetch_api(YOUTUBE_CHANNEL_URL, channel_params)
            if not channel_data or "items" not in channel_data:
                st.warning(f"Failed to fetch channel statistics for keyword: {keyword}")
                continue

            # Collect and store results
            for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:200]
                video_id = video["id"].get("videoId", "N/A")
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                views = int(stat["statistics"].get("viewCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                if subs < 3000:  # Only include small channels
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs
                    })

        # Display results
        if all_results:
            st.success(f"Found {len(all_results)} results!")
            for result in all_results:
                st.markdown(
                    f"**Title:** {result['Title']}  \n"
                    f"**Description:** {result['Description']}  \n"
                    f"**URL:** [Watch Video]({result['URL']})  \n"
                    f"**Views:** {result['Views']}  \n"
                    f"**Subscribers:** {result['Subscribers']}"
                )
                st.write("---")
        else:
            st.warning("No results found for small channels.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
