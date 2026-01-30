import json
import re
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("data/processed/normalized_rss.json")
OUTPUT_FILE = Path("data/processed/deduplicated_rss.json")

def normalize_for_dedup(text):
    """Normalise le texte pour la déduplication en:
    - convertissant en minuscules
    - supprimant la ponctuation
    - normalisant les espaces
    """
    if not text:
        return ""
    text = text.lower()
    # Supprime la ponctuation
    text = re.sub(r'[^\w\s]', '', text)
    # Normalise les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])

    seen_titles = set()
    seen_links = set()
    unique_articles = []

    for article in articles:
        # Normalise le titre pour détecter les doublons sémantiques
        title_normalized = normalize_for_dedup(article.get("title", ""))
        link = article.get("link")

        # Un article est un doublon si:
        # - Son titre normalisé a déjà été vu OU
        # - Son lien a déjà été vu
        is_duplicate = (title_normalized in seen_titles) or (link in seen_links)

        if not is_duplicate:
            seen_titles.add(title_normalized)
            seen_links.add(link)
            unique_articles.append(article)

    output = {
        "deduplicated_at": datetime.utcnow().isoformat(),
        "total_articles": len(unique_articles),
        "articles": unique_articles
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Deduplicated {len(articles)} -> {len(unique_articles)} articles")

if __name__ == "__main__":
    main()