import os
import time
import json
import base64
import argparse
import datetime
import logging
import requests
import feedparser

SENT_ENTRIES_DIR = "sent_entries"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


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
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code != 204:
            logger.error(f"Discord Error: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending to Discord: {e}")


def fetch_feed_content(rss_url, username=None, password=None):
    headers = {"User-Agent": "feedparser/6.0.11"}
    if username and password:
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"

    try:
        response = requests.get(rss_url, headers=headers, verify=False)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error fetching feed from {rss_url}: {e}")
        return None


def check_feed(config, last_entries=5):
    source_name = config["source_name"]
    rss_url = config["source_rss"]
    webhook_url = config["destination_webhook"]
    username = config.get("username")
    password = config.get("password")
    config_name = source_name.replace("@", "").replace(" ", "_")

    logger.info(f"Checking feed: {source_name}")
    logger.debug(f"RSS URL: {rss_url}")

    feed_content = fetch_feed_content(rss_url, username, password)
    if not feed_content:
        logger.error(f"Failed to fetch feed content for {source_name}")
        return

    feed = feedparser.parse(feed_content)
    logger.debug(f"Raw feed response: {feed}")

    sent_entries = load_sent_entries(config_name)
    new_entries = [
        entry for entry in reversed(feed.entries[:last_entries]) if entry.id not in sent_entries
    ]

    for entry in new_entries:
        published_raw = entry.get("published_parsed")
        if published_raw:
            published_dt = datetime.datetime(*published_raw[:6])
            published = published_dt.strftime("%Y-%m-%d %H:%M")
        else:
            published = "Unknown Date"

        author = entry.get("author", "").lstrip("@")
        status_url = entry.get("id", "")

        if status_url:
            status_id = status_url.split("/")[-1].split("#")[0]
            tweet_link = f"https://twitter.com/{author}/status/{status_id}"
        else:
            tweet_link = entry.get("link", "")

        message = f"📢 @{author} posted new [tweet]({tweet_link}) on {published}"

        send_to_discord(webhook_url, message)
        save_sent_entry(config_name, entry.id)

    if new_entries:
        logger.info(f"Sent {len(new_entries)} new entries from {source_name}.")
    else:
        logger.info(f"No new entries from {source_name}.")


def main(config_path, interval):
    while True:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                logger.debug(f"Loading config file: {config_path}")
                configs = json.load(f)
                logger.debug(f"Loaded config: {json.dumps(configs, indent=2)}")

            for config in configs:
                check_feed(config)

        except Exception as e:
            logger.error(f"Error occurred: {e}")

        logger.info(f"Waiting {interval} seconds before next check...")
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSS to Discord Webhook Bot")
    parser.add_argument("--config", help="Path to the JSON config file", required=True)
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Scan interval in seconds (default: 300 seconds = 5 minutes)",
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "ERROR"],
        help="Set the logging level (default: INFO)",
    )
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.loglevel.upper(), logging.INFO))
    main(args.config, args.interval)
