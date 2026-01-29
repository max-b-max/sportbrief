import json
from pathlib import Path
from datetime import datetime

RAW_RSS_DIR = Path("data/raw/rss")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "merged_rss.json"

def main():
    all_articles = []

    for file in RAW_RSS_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            feed_data = json.load(f)
            articles = feed_data.get("articles", [])
            all_articles.extend(articles)

    merged_data = {
        "merged_at": datetime.utcnow().isoformat(),
        "total_articles": len(all_articles),
        "articles": all_articles
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Merged {len(all_articles)} articles into {OUTPUT_FILE}")

if __name__ == "__main__":
    main()