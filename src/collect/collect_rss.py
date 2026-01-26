import feedparser
import json
from datetime import datetime
from pathlib import Path

# Quelques flux RSS sportifs pour commencer
RSS_FEEDS = {
    "rmc_foot": "https://rmcsport.bfmtv.com/rss/football/",
    "rmc_rugby": "https://rmcsport.bfmtv.com/rss/rugby/",
    "rmc_basket": "https://rmcsport.bfmtv.com/rss/basket/",
    "rmc_tennis": "https://rmcsport.bfmtv.com/rss/tennis/",
    "rmc_f1": "https://rmcsport.bfmtv.com/rss/auto-moto/f1/",
}

OUTPUT_DIR = Path("data/raw/rss")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def collect_feed(source_name, url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "source": source_name,
            "title": entry.get("title"),
            "summary": entry.get("summary", ""),
            "link": entry.get("link"),
            "published": entry.get("published", None)
        })

    return {
        "source": source_name,
        "fetched_at": datetime.utcnow().isoformat(),
        "articles": articles
    }

def main():
    for source, url in RSS_FEEDS.items():
        data = collect_feed(source, url)
        output_file = OUTPUT_DIR / f"{source}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] {source}: {len(data['articles'])} articles")

if __name__ == "__main__":
    main()
