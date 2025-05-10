import time
import json
import argparse
import feedparser
import requests
import os

SENT_ENTRIES_DIR = "sent_entries"

def load_sent_entries(config_name):
    os.makedirs(SENT_ENTRIES_DIR, exist_ok=True)
    filepath = os.path.join(SENT_ENTRIES_DIR, f"{config_name}.txt")
    try:
        with open(filepath, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_sent_entry(config_name, entry_id):
    filepath = os.path.join(SENT_ENTRIES_DIR, f"{config_name}.txt")
    with open(filepath, "a") as f:
        f.write(f"{entry_id}\n")

def send_to_discord(webhook_url, message):
    payload = {"content": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 204:
        print(f"❌ Discord Error: {response.status_code} - {response.text}")

def check_feed(config, last_entries=5):
    source_name = config["source_name"]
    rss_url = config["source_rss"]
    webhook_url = config["destination_webhook"]
    config_name = source_name.replace("@", "").replace(" ", "_")

    print(f"🔍 Checking feed: {source_name}")
    feed = feedparser.parse(rss_url)
    sent_entries = load_sent_entries(config_name)

    new_entries = [entry for entry in reversed(feed.entries[:last_entries]) if entry.id not in sent_entries]

    for entry in new_entries:
        published = entry.get("published", "Unknown Date")
        message = (
            f"```fix\n📢 New post from {source_name}\n```\n"
            f"🗓️ **Date:** {published}\n"
            f"📄 **Title:** {entry.title}\n"
            f"🔗 {entry.link}"
        )
        send_to_discord(webhook_url, message)
        save_sent_entry(config_name, entry.id)

    if new_entries:
        print(f"✅ Sent {len(new_entries)} new entries from {source_name}.")
    else:
        print(f"📭 No new entries from {source_name}.")

def main(config_path, interval):
    with open(config_path, "r", encoding="utf-8") as f:
        configs = json.load(f)

    while True:
        try:
            for config in configs:
                check_feed(config)
        except Exception as e:
            print(f"❗ Error occurred: {e}")
        print(f"⏳ Waiting {interval} seconds before next check...")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSS to Discord Webhook Bot")
    parser.add_argument("--config", help="Path to the JSON config file")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Scan interval in seconds (default: 300 seconds = 5 minutes)"
    )
    args = parser.parse_args()

    main(args.config, args.interval)