import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("data/processed/merged_rss.json")
OUTPUT_FILE = Path("data/processed/normalized_rss.json")

def normalize_article(article):
    return {
        "source": article.get("source"),
        "title": article.get("title", ""),
        "summary": article.get("summary", ""),
        "link": article.get("link"),
        "published": article.get("published")
    }

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    normalized_articles = [
        normalize_article(article)
        for article in data.get("articles", [])
    ]

    output = {
        "normalized_at": datetime.utcnow().isoformat(),
        "total_articles": len(normalized_articles),
        "articles": normalized_articles
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Normalized {len(normalized_articles)} articles")

if __name__ == "__main__":
    main()
