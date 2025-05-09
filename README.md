# 📢 RSS to Discord Webhook Bot

A Python bot that reads multiple RSS feeds and sends new entries to Discord channels via webhooks.

---

## 📦 Installation

```bash
git clone <your_repo_url>
cd <your_repo_name>
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `webhook_config.json` file in the `config` folder (example):

```json
[
    {
        "source_name": "@BBC_News",
        "source_rss": "https://feeds.bbci.co.uk/news/rss.xml",
        "destination_webhook": "your_webhook1"
    },
    {
        "source_name": "@CNN",
        "source_rss": "http://rss.cnn.com/rss/edition.rss",
        "destination_webhook": "your_webhook2"
    }
]
```

---

## ▶️ Running the Bot

From the main directory:

```bash
python project/rss_to_discord.py --config config/webhook_config.json
```

With a custom interval (e.g., every 60 seconds):

```bash
python project/rss_to_discord.py --config config/webhook_config.json --interval 60
```
