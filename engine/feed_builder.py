"""
Gera o arquivo XML RSS a partir da lista de itens.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator
from dateutil import parser as dateparser

log = logging.getLogger(__name__)


def build_feed(cfg, items, output_path: Path):
    """Constrói e salva o feed RSS em output_path."""
    fg = FeedGenerator()
    fg.id(cfg.get("url") or cfg.get("rss_url", ""))
    fg.title(cfg.get("title", cfg["id"]))
    fg.description(cfg.get("description", cfg.get("title", cfg["id"])))
    fg.link(href=cfg.get("url") or cfg.get("rss_url", ""), rel="alternate")
    fg.language("pt-BR")
    fg.lastBuildDate(datetime.now(tz=timezone.utc))

    for item in items:
        fe = fg.add_entry()
        fe.id(item["link"])
        fe.title(item["title"] or "(sem título)")
        fe.link(href=item["link"])

        if item.get("summary"):
            fe.description(item["summary"])

        pub_date = _parse_date(item.get("date"))
        fe.pubDate(pub_date)

    fg.rss_file(str(output_path), pretty=True)


def _parse_date(date_str):
    """Tenta converter string de data para datetime com timezone. Fallback: agora."""
    if not date_str:
        return datetime.now(tz=timezone.utc)
    
    # Tradução simples para datas em Português (comum em sites do governo)
    months_pt = {
        "janeiro": "January", "fevereiro": "February", "março": "March",
        "abril": "April", "maio": "May", "junho": "June",
        "julho": "July", "agosto": "August", "setembro": "September",
        "outubro": "October", "novembro": "November", "dezembro": "December"
    }
    
    clean_date = date_str.lower()
    for pt, en in months_pt.items():
        if pt in clean_date:
            clean_date = clean_date.replace(pt, en)
    
    # Remove "de" (ex: "2 de maio de 2024")
    clean_date = clean_date.replace(" de ", " ")

    try:
        dt = dateparser.parse(clean_date)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt or datetime.now(tz=timezone.utc)
    except Exception:
        return datetime.now(tz=timezone.utc)
