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
import urllib3
import re
import html

# Desabilita avisos de SSL inseguro caso uma fonte precise de verify: false
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

log = logging.getLogger(__name__)


def _clean_html(raw_html):
    """Remove tags HTML, decodifica entidades e limpa rodapés/links de 'leia mais'."""
    if not raw_html:
        return ""
    
    # Converte para string e decodifica entidades HTML
    if hasattr(raw_html, "decode_contents"):
        content = raw_html.decode_contents()
    else:
        content = str(raw_html)
    
    content = html.unescape(content)

    # Usa BS4 para manipular o HTML
    # Silencia o aviso 'MarkupResemblesLocator' verificando se há tags HTML
    if "<" not in content or ">" not in content:
        return content.strip()

    soup = BeautifulSoup(content, "lxml")
    
    # 1. Remove links de "Leia mais", "Read more" e similares por classe ou texto
    for a in soup.find_all("a"):
        # Se a classe contém palavras de 'leia mais'
        classes = " ".join(a.get("class", []))
        if re.search(r"more|read|leia|excerpt", classes, re.I):
            a.decompose()
            continue
        # Se o texto do link é só [...] ou similar
        if re.match(r"^[\[\(\.\s]*\.\.\.[\]\)\s]*$", a.get_text()):
            a.decompose()

    # 2. Extrai apenas o texto puro
    text = soup.get_text(separator=" ", strip=True)

    # 3. Remove rodapés WordPress e padrões de reticências que sobraram no texto
    patterns = [
        r"O post .* apareceu primeiro em .*",
        r"The post .* appeared first on .*",
        r"\[\.\.\.\]", 
        r"\(\.\.\.\)",
        r"\.\.\.\s*$" # Reticências no final
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # 4. Normalização final
    text = " ".join(text.split())
    return text.strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}
REQUEST_TIMEOUT = 30
POLITE_DELAY = 1.5  # segundos entre requisições


def _get(url, custom_headers=None, verify=True):
    headers = HEADERS.copy()
    if custom_headers:
        headers.update(custom_headers)
    
    # Se não houver X-Requested-With e for uma chamada AJAX comum, adicionamos
    if "X-Requested-With" not in headers and "controller" in url:
        headers["X-Requested-With"] = "XMLHttpRequest"

    resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=verify)
    resp.encoding = resp.apparent_encoding
    resp.raise_for_status()
    time.sleep(POLITE_DELAY)
    return resp


# Sessão global para persistir cookies entre chamadas (necessário para alguns sites)
session = requests.Session()

def _get_with_session(url, custom_headers=None, verify=True):
    headers = HEADERS.copy()
    if custom_headers:
        headers.update(custom_headers)
    
    resp = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=verify)
    resp.encoding = resp.apparent_encoding
    resp.raise_for_status()
    time.sleep(POLITE_DELAY)
    return resp


def scrape_page(cfg):
    """Extrai itens de uma página HTML usando seletores CSS."""
    verify = cfg.get("verify_ssl", True)

    # Alguns sites exigem visitar a página principal antes para obter cookies
    if cfg.get("pre_visit"):
        _get_with_session(cfg["url"], verify=verify)
        actual_url = cfg.get("actual_url", cfg["url"])
    else:
        actual_url = cfg["url"]

    resp = _get_with_session(actual_url, custom_headers=cfg.get("headers"), verify=verify)
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
        
        # O link pode ser o próprio elemento ou um filho
        link_el = None
        if link_sel:
            # Se o seletor for o próprio elemento (ex: item é um <a> e link_sel é "a")
            if el.name == link_sel or el.has_attr('class') and any(c in link_sel for c in el['class']):
                link_el = el
            else:
                link_el = el.select_one(link_sel)
            
            # Fallback se ainda não encontrou mas o item é um link
            if not link_el and el.name == "a":
                link_el = el
        
        date_el = el.select_one(date_sel) if date_sel else None
        summary_el = el.select_one(summary_sel) if summary_sel else None
        
        image_sel = sel.get("image")
        image_el = el.select_one(image_sel) if image_sel else None

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

        # Imagem
        image_url = ""
        if image_el:
            # Lista de atributos comuns para Lazy Loading (em ordem de prioridade)
            lazy_attrs = ["data-src", "data-lazy", "data-original", "data-echo", "data-url", "src"]
            
            for attr in lazy_attrs:
                val = image_el.get(attr)
                if val:
                    # Verifica se no é um placeholder comum
                    placeholders = ["pre-img", "placeholder", "loading", "spacer", "transparent", "default"]
                    if not any(p in val.lower() for p in placeholders):
                        image_url = val
                        break
            
            # Fallback para o primeiro valor encontrado se nenhum passou no filtro (melhor que nada)
            if not image_url:
                image_url = image_el.get("src") or ""

            # Trata background-image via style caso não tenha tag img com src
            if not image_url and image_el.has_attr("style"):
                bg_match = re.search(r'url\((["\']?)(.*?)\1\)', image_el["style"])
                if bg_match:
                    image_url = bg_match.group(2)
            
            if image_url and not image_url.startswith("http"):
                image_url = urljoin(link_prefix or cfg["url"], image_url)

        # Limpeza de título: remove prefixos repetidos
        if date_str and title.startswith(date_str):
            title = title[len(date_str):].strip()
            for sep in ["-", "|", ":", "—"]:
                if title.startswith(sep):
                    title = title[len(sep):].strip()
                    break

        summary = _clean_html(summary_el) if summary_el else ""

        # Se faltar imagem ou resumo, tenta buscar no site (Fallback Automático)
        if (not image_url or not summary) and link:
            fb = _fetch_fallback_data(link, verify=cfg.get("verify_ssl", True))
            if not image_url: image_url = fb["image"]
            if not summary: summary = fb["summary"]

        items.append({
            "title": title,
            "link": link,
            "date": date_str,
            "summary": summary,
            "image": image_url,
        })

    # Aplica filtro por palavras-chave se configurado
    filter_keywords = cfg.get("filter_keywords")
    if filter_keywords:
        kw_lower = [k.lower() for k in filter_keywords]
        items = [
            item for item in items
            if any(kw in (item["title"] + " " + item["summary"]).lower() for kw in kw_lower)
        ]

    return items


def _fetch_fallback_data(url, verify=True):
    """Visita a URL da notícia para tentar encontrar a imagem e o resumo no HTML."""
    data = {"image": "", "summary": ""}
    try:
        resp = _get(url, verify=verify)
        soup = BeautifulSoup(resp.text, "lxml")
        
        # 1. Busca Imagem (Meta tags > Tags comuns)
        og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if og_image and og_image.get("content"):
            data["image"] = og_image["content"]
        else:
            featured = soup.select_one(".featured-image img, .post-thumbnail img, .entry-content img, article img")
            if featured:
                lazy_attrs = ["data-src", "data-lazy", "data-original", "src"]
                for attr in lazy_attrs:
                    val = featured.get(attr)
                    if val and not any(p in val.lower() for p in ["placeholder", "pre-img", "spacer"]):
                        data["image"] = urljoin(url, val)
                        break

        # 2. Busca Resumo (Meta tags > Primeiro parágrafo)
        desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            data["summary"] = _clean_html(desc["content"])
        else:
            first_p = soup.select_one("article p, .entry-content p, #noticia_texto p")
            if first_p:
                data["summary"] = _clean_html(first_p)

    except Exception as e:
        log.debug(f"  Falha ao buscar fallback data para {url}: {e}")
    return data


def fetch_rss(rss_url, filter_keywords=None, max_items=30, verify=True):
    """Busca um feed RSS existente, aplica filtro por palavras-chave e retorna itens."""
    resp = _get(rss_url, verify=verify)
    soup = BeautifulSoup(resp.content, "xml") 
    
    entries = []
    items = soup.find_all("item")
    if items:
        # RSS 2.0
        for item in items[:max_items * 3]:
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            link = item.find("link").get_text(strip=True) if item.find("link") else ""
            date = item.find("pubDate").get_text(strip=True) if item.find("pubDate") else ""
            summary = _clean_html(item.find("description")) if item.find("description") else ""
            
            image = ""
            enc = item.find("enclosure")
            if enc and enc.get("url"):
                image = enc["url"]
            if not image:
                media = item.find("content", namespace=re.compile(r".*media.*")) or item.find("thumbnail")
                if media and media.get("url"):
                    image = media["url"]
            
            # Se faltar imagem ou resumo, tenta buscar no site
            if (not image or not summary) and link:
                fb = _fetch_fallback_data(link, verify=verify)
                if not image: image = fb["image"]
                if not summary: summary = fb["summary"]

            entries.append({
                "title": title, "link": link, "date": date, 
                "summary": summary, "image": image
            })
    else:
        # Atom
        items = soup.find_all("entry")
        for item in items[:max_items * 3]:
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            link_el = item.find("link")
            link = link_el.get("href", "") if link_el else ""
            date = (item.find("updated") or item.find("published")).get_text(strip=True) if (item.find("updated") or item.find("published")) else ""
            summary = _clean_html(item.find("summary") or item.find("content"))

            image = ""
            link_img = item.find("link", rel="enclosure")
            if link_img and link_img.get("href"):
                image = link_img["href"]
            
            if (not image or not summary) and link:
                fb = _fetch_fallback_data(link, verify=verify)
                if not image: image = fb["image"]
                if not summary: summary = fb["summary"]

            entries.append({
                "title": title, "link": link, "date": date, 
                "summary": summary, "image": image
            })

    if filter_keywords:
        kw_lower = [k.lower() for k in filter_keywords]
        entries = [
            e for e in entries
            if any(kw in (e["title"] + " " + e["summary"]).lower() for kw in kw_lower)
        ]

    return entries[:max_items]


def fetch_json(cfg):
    """Extrai itens de um endpoint JSON usando mapeamento de campos."""
    url = cfg["url"]
    verify = cfg.get("verify_ssl", True)
    resp = _get(url, custom_headers=cfg.get("headers"), verify=verify)
    data = resp.json()
    
    # Se os itens estiverem em uma sub-chave (ex: data['noticias'])
    items_path = cfg.get("json_items_path")
    if items_path:
        for key in items_path.split('.'):
            data = data.get(key, [])
    
    # Se não for uma lista, não podemos processar
    if not isinstance(data, list):
        log.warning(f"  Endpoint JSON {url} não retornou uma lista.")
        return []

    mapping = cfg.get("selectors", {})
    items = []
    
    for entry in data[:cfg.get("max_items", 30)]:
        items.append({
            "title": entry.get(mapping.get("title", "title"), ""),
            "link": entry.get(mapping.get("link", "link"), ""),
            "date": entry.get(mapping.get("date", "date"), ""),
            "summary": _clean_html(entry.get(mapping.get("summary", "summary"), "")),
            "image": entry.get(mapping.get("image", "image"), ""),
        })

    # Aplica filtro por palavras-chave se configurado
    filter_keywords = cfg.get("filter_keywords")
    if filter_keywords:
        kw_lower = [k.lower() for k in filter_keywords]
        items = [
            item for item in items
            if any(kw in (item["title"] + " " + item["summary"]).lower() for kw in kw_lower)
        ]

    return items
