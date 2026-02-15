import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser

INPUT_FILE = Path("data/processed/merged_rss.json")
OUTPUT_FILE = Path("data/processed/normalized_rss.json")

# Ne garder que les articles publiés dans les dernières N heures
MAX_AGE_HOURS = 30


def parse_published(published_str):
    """Tente de parser la date de publication. Retourne None si impossible."""
    if not published_str:
        return None
    try:
        dt = dateutil_parser.parse(published_str)
        # Rendre timezone-aware si ce n'est pas le cas
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def is_recent(published_str, max_age_hours=MAX_AGE_HOURS):
    """Retourne True si l'article est récent ou si la date est indéterminée."""
    dt = parse_published(published_str)
    if dt is None:
        return True  # Conserver si on ne peut pas déterminer la date
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    return dt >= cutoff


def normalize_article(article):
    return {
        "source": article.get("source"),
        "title": article.get("title", "").strip(),
        "summary": article.get("summary", "").strip(),
        "link": article.get("link"),
        "published": article.get("published") or None
    }


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_articles = data.get("articles", [])

    # Filtre temporel : on ne garde que les articles récents
    recent_articles = [a for a in all_articles if is_recent(a.get("published"))]
    filtered_count = len(all_articles) - len(recent_articles)

    normalized_articles = [normalize_article(a) for a in recent_articles]

    output = {
        "normalized_at": datetime.utcnow().isoformat(),
        "total_articles": len(normalized_articles),
        "articles": normalized_articles
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[OK] Normalized {len(normalized_articles)} articles "
          f"({filtered_count} anciens filtrés sur {len(all_articles)} total, fenêtre {MAX_AGE_HOURS}h)")


if __name__ == "__main__":
    main()
