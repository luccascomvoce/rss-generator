"""
Módulo de coleta: scraping HTML e passthrough de RSS existente.
"""
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; rss-generator/1.0; "
        "+https://github.com/seu-usuario/rss-generator)"
    )
}
REQUEST_TIMEOUT = 15
POLITE_DELAY = 1.5  # segundos entre requisições


def _get(url, custom_headers=None):
    headers = HEADERS.copy()
    if custom_headers:
        headers.update(custom_headers)
    
    # Se não houver X-Requested-With e for uma chamada AJAX comum, adicionamos
    if "X-Requested-With" not in headers and "controller" in url:
        headers["X-Requested-With"] = "XMLHttpRequest"

    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    time.sleep(POLITE_DELAY)
    return resp


# Sessão global para persistir cookies entre chamadas (necessário para alguns sites)
session = requests.Session()

def _get_with_session(url, custom_headers=None):
    headers = HEADERS.copy()
    if custom_headers:
        headers.update(custom_headers)
    
    resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    time.sleep(POLITE_DELAY)
    return resp


def scrape_page(cfg):
    """Extrai itens de uma página HTML usando seletores CSS."""
    # Alguns sites exigem visitar a página principal antes para obter cookies
    if cfg.get("pre_visit"):
        _get_with_session(cfg["url"])
        actual_url = cfg.get("actual_url", cfg["url"])
    else:
        actual_url = cfg["url"]

    resp = _get_with_session(actual_url, custom_headers=cfg.get("headers"))
    soup = BeautifulSoup(resp.text, "lxml")
    sel = cfg.get("selectors", {})
    link_prefix = cfg.get("link_prefix", "")
    max_items = cfg.get("max_items", 30)

    raw_items = soup.select(sel.get("items", "article"))[:max_items]
    items = []

    for el in raw_items:
        title_sel = sel.get("title", "h2, h3")
        link_sel = sel.get("link", "a")
        date_sel = sel.get("date", "time")
        summary_sel = sel.get("summary", "p")

        title_el = el.select_one(title_sel) if title_sel else None
        link_el = el.select_one(link_sel) if link_sel else None
        date_el = el.select_one(date_sel) if date_sel else None
        summary_el = el.select_one(summary_sel) if summary_sel else None

        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        link = link_el.get("href", "")

        if link and not link.startswith("http"):
            link = urljoin(link_prefix or cfg["url"], link)

        if not link:
            continue

        date_str = None
        if date_el:
            date_str = date_el.get("datetime") or date_el.get_text(strip=True)

        # Limpeza de título: remove prefixos repetidos (comum se o seletor do título engloba a data)
        if date_str and title.startswith(date_str):
            title = title[len(date_str):].strip()
            # Remove separadores comuns como " - " ou " | "
            for sep in ["-", "|", ":", "—"]:
                if title.startswith(sep):
                    title = title[len(sep):].strip()
                    break

        summary = summary_el.get_text(strip=True) if summary_el else ""

        items.append({
            "title": title,
            "link": link,
            "date": date_str,
            "summary": summary,
        })

    return items


def fetch_rss(rss_url, filter_keywords=None, max_items=30):
    """Busca um feed RSS existente, aplica filtro por palavras-chave e retorna itens."""
    resp = _get(rss_url)
    root = ET.fromstring(resp.content)

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    channel = root.find("channel")
    entries = []

    if channel is not None:
        # RSS 2.0
        for item in channel.findall("item")[:max_items * 3]:
            title = _xml_text(item, "title")
            link = _xml_text(item, "link")
            date = _xml_text(item, "pubDate")
            summary = _xml_text(item, "description")
            entries.append({"title": title, "link": link, "date": date, "summary": summary})
    else:
        # Atom
        for entry in root.findall("atom:entry", ns)[:max_items * 3]:
            title = _xml_text(entry, "atom:title", ns)
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            date = _xml_text(entry, "atom:updated", ns)
            summary = _xml_text(entry, "atom:summary", ns)
            entries.append({"title": title, "link": link, "date": date, "summary": summary})

    if filter_keywords:
        kw_lower = [k.lower() for k in filter_keywords]
        entries = [
            e for e in entries
            if any(kw in (e["title"] + " " + e["summary"]).lower() for kw in kw_lower)
        ]

    return entries[:max_items]


def _xml_text(el, tag, ns=None):
    child = el.find(tag, ns) if ns else el.find(tag)
    if child is None:
        return ""
    return (child.text or "").strip()
