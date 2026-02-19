import feedparser
import json
from datetime import datetime
from pathlib import Path

RSS_FEEDS = {
    "dailysport": "https://www.dailysports.fr/rss/index.html",

    # L'Équipe
    "lequipe_foot": "https://dwh.lequipe.fr/api/edito/rss?path=/Football/",
    "lequipe_basket": "https://dwh.lequipe.fr/api/edito/rss?path=/Basket/",
    "lequipe_rugby": "https://dwh.lequipe.fr/api/edito/rss?path=/Rugby/",
    "lequipe_tennis": "https://dwh.lequipe.fr/api/edito/rss?path=/Tennis/",
    "lequipe_cyclisme": "https://dwh.lequipe.fr/api/edito/rss?path=/Cyclisme/",
    "lequipe_handball": "https://dwh.lequipe.fr/api/edito/rss?path=/Handball/",
    "lequipe_f1": "https://dwh.lequipe.fr/api/edito/rss?path=/Formule-1/",
    "lequipe_volley": "https://dwh.lequipe.fr/api/edito/rss?path=/Volley-ball/",
    "lequipe_athletisme": "https://dwh.lequipe.fr/api/edito/rss?path=/Athletisme/",
    "lequipe_ski": "https://dwh.lequipe.fr/api/edito/rss?path=/Ski/",
    "lequipe_moto": "https://dwh.lequipe.fr/api/edito/rss?path=/Moto/",

    # RMC Sport
    "rmc_foot": "https://rmcsport.bfmtv.com/rss/football/",
    "rmc_foot_coupe_monde": "https://rmcsport.bfmtv.com/rss/football/coupe-du-monde/",
    "rmc_euro": "https://rmcsport.bfmtv.com/rss/football/euro/",
    "rmc_LDC": "https://rmcsport.bfmtv.com/rss/football/ligue-des-champions/",
    "rmc_ligue1": "https://rmcsport.bfmtv.com/rss/football/ligue-1/",
    "rmc_premier_league": "https://rmcsport.bfmtv.com/rss/football/premier-league/",
    "rmc_mercato": "https://rmcsport.bfmtv.com/rss/football/transferts/",
    "dailysport_football": "https://www.dailysports.fr/rss/football.html",

    "rmc_rugby": "https://rmcsport.bfmtv.com/rss/rugby/",
    "rmc_rugby_coupe_monde":"https://rmcsport.bfmtv.com/rss/rugby/coupe-du-monde/",
    "rmc_rugby_coupe_europe":"https://rmcsport.bfmtv.com/rss/rugby/coupe-d-europe/",
    "rmc_rugby_6_nations": "https://rmcsport.bfmtv.com/rss/rugby/tournoi-des-6-nations/",
    "dailysport_rugby": "https://www.dailysports.fr/rss/rugby.html",

    "rmc_basket": "https://rmcsport.bfmtv.com/rss/basket/",
    "rmc_nba": "https://rmcsport.bfmtv.com/rss/basket/nba/",
    "dailysport_basket": "https://www.dailysports.fr/rss/basket.html",

    "rmc_tennis": "https://rmcsport.bfmtv.com/rss/tennis/",
    "dailysport_tennis": "https://www.dailysports.fr/rss/tennis.html",

    "rmc_cyclisme": "https://rmcsport.bfmtv.com/rss/cyclisme/",
    "rmc_TDF": "https://rmcsport.bfmtv.com/rss/cyclisme/tour-de-france/",
    "dailysport_cyclisme": "https://www.dailysports.fr/rss/cyclisme.html",

    "rmc_f1": "https://rmcsport.bfmtv.com/rss/auto-moto/f1/",
    "dailysport_automoto": "https://www.dailysports.fr/rss/auto-moto.html",

    "rmc_handball": "https://rmcsport.bfmtv.com/rss/handball/",
    
    "rmc_volley": "https://rmcsport.bfmtv.com/rss/volley",

    "rmc_combat": "https://rmcsport.bfmtv.com/rss/sports-de-combat/",
    
    "rmc_JO": "https://rmcsport.bfmtv.com/rss/jeux-olympiques/",
    "lequipe_JO": "https://dwh.lequipe.fr/api/edito/rss?path=/Jo/",
    "lemonde_JO": "https://www.lemonde.fr/jeux-olympiques/rss_full.xml",

    "rmc_societe": "https://rmcsport.bfmtv.com/rss/societe/",

    "dailysport_autres_sports": "https://www.dailysports.fr/rss/autres-sports.html"
}


OUTPUT_DIR = Path("data/raw/rss")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def collect_feed(source_name, url):
    try:
        feed = feedparser.parse(url)

        # Vérifier si le flux est malformé
        if feed.bozo:
            print(f"[WARNING] {source_name}: flux malformé (bozo bit activé)")
            # On continue quand même si des entrées sont présentes

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

    except Exception as e:
        print(f"[ERROR] {source_name}: {e}")
        # Retourne une structure vide pour ne pas casser le pipeline
        return {
            "source": source_name,
            "fetched_at": datetime.utcnow().isoformat(),
            "articles": []
        }

def main():
    for source, url in RSS_FEEDS.items():
        data = collect_feed(source, url)

        output_file = OUTPUT_DIR / f"{source}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] {source}: {len(data['articles'])} articles collected")

if __name__ == "__main__":
    main()
