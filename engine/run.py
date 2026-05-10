"""
Ponto de entrada do gerador de feeds.
Carrega todas as fontes em sources/, processa cada uma e salva os XMLs em docs/.
"""
import os
import sys
import glob
import yaml
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scraper import scrape_page, fetch_rss, fetch_json
from feed_builder import build_feed
from deduplicator import is_new, mark_seen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
SOURCES_DIR = ROOT / "sources"
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)


def load_sources():
    configs = []
    for path in sorted(glob.glob(str(SOURCES_DIR / "*.yml"))):
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            cfg["_path"] = path
            configs.append(cfg)
    return configs


def process_source(cfg):
    source_id = cfg["id"]
    source_type = cfg.get("type", "scrape")
    log.info(f"Processando: {source_id} (tipo: {source_type})")

    try:
        if source_type == "rss":
            items = fetch_rss(
                cfg["rss_url"],
                filter_keywords=cfg.get("filter_keywords", []),
                max_items=cfg.get("max_items", 30),
                verify=cfg.get("verify_ssl", True)
            )
        elif source_type == "json":
            items = fetch_json(cfg)
        else:
            items = scrape_page(cfg)

        # Deduplica itens dentro da própria coleta (por URL)
        unique_items = []
        seen_urls = set()
        for item in items:
            if item["link"] not in seen_urls:
                unique_items.append(item)
                seen_urls.add(item["link"])
        
        items = unique_items
        new_items = [item for item in items if is_new(source_id, item["link"])]
        log.info(f"  {len(items)} itens únicos coletados, {len(new_items)} novos")

        if new_items:
            output_path = DOCS_DIR / cfg["feed_output"]
            build_feed(cfg, new_items, output_path)
            for item in new_items:
                mark_seen(source_id, item["link"])
            log.info(f"  Feed salvo: {output_path}")
        else:
            # Garante que o arquivo existe mesmo sem itens novos
            output_path = DOCS_DIR / cfg["feed_output"]
            if not output_path.exists():
                build_feed(cfg, [], output_path)
                log.info(f"  Feed vazio criado: {output_path}")

    except Exception as e:
        log.error(f"  Erro ao processar {source_id}: {e}")


import json

def generate_outputs(sources):
    """Gera o feeds.json e o index.html automaticamente com base nas fontes carregadas."""
    # 1. Gera feeds.json
    feeds_data = []
    for cfg in sources:
        feeds_data.append({
            "id": cfg["id"],
            "title": cfg["title"],
            "description": cfg.get("description", ""),
            "url": cfg["feed_output"]
        })
    
    json_path = DOCS_DIR / "feeds.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(feeds_data, f, indent=2, ensure_ascii=False)
    log.info(f"Registro JSON gerado: {json_path}")

    # 2. Gera index.html
    # Agrupa por categorias (heurística baseada no ID ou tipo)
    categories = {
        "🏛️ Órgãos Públicos": ["prefeitura", "camara", "samae", "defesa-civil-blumenau", "celesc", "furb"],
        "🚨 Segurança": ["pmsc", "pcsc", "cbmsc", "defesa-civil-noticias"],
        "📰 Portais de Notícias": [] # O resto cai aqui
    }
    
    html_items = {cat: [] for cat in categories}
    for cfg in sources:
        found_cat = False
        for cat, keywords in categories.items():
            if any(kw in cfg["id"] for kw in keywords):
                html_items[cat].append(cfg)
                found_cat = True
                break
        if not found_cat:
            html_items["📰 Portais de Notícias"].append(cfg)

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RSS Generator — Feeds</title>
  <style>
    body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; color: #222; line-height: 1.5; }}
    h1 {{ font-size: 1.6rem; border-bottom: 2px solid #016970; padding-bottom: 0.5rem; }}
    h2 {{ font-size: 1.2rem; margin-top: 2rem; color: #444; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin: .8rem 0; padding: 0.5rem; background: #f9f9f9; border-radius: 6px; border-left: 4px solid #016970; }}
    li:hover {{ background: #f0f7f8; }}
    a {{ color: #016970; text-decoration: none; font-weight: bold; }}
    .url {{ display: block; font-family: monospace; font-size: 0.85em; color: #666; margin-top: 4px; }}
    footer {{ margin-top: 4rem; font-size: .8rem; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 1rem; }}
  </style>
</head>
<body>
  <h1>📡 Feeds RSS — Blumenau</h1>
  <p>Atualizado automaticamente. <a href="feeds.json">Versão JSON para Bots</a></p>
"""
    for cat, items in html_items.items():
        if items:
            html_content += f"  <h2>{cat}</h2>\n  <ul>\n"
            for item in sorted(items, key=lambda x: x["title"]):
                html_content += f'    <li><a href="{item["feed_output"]}">{item["title"]}</a> <span class="url">{item["feed_output"]}</span></li>\n'
            html_content += "  </ul>\n"

    html_content += """  <footer>rss-generator</footer>
</body>
</html>"""

    html_path = DOCS_DIR / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    log.info(f"Página de índice gerada: {html_path}")


def main():
    sources = load_sources()
    if not sources:
        log.warning("Nenhuma fonte encontrada em sources/")
        return

    log.info(f"Carregadas {len(sources)} fontes")
    for cfg in sources:
        process_source(cfg)

    # NOVIDADE: Gera os arquivos de descoberta automaticamente
    generate_outputs(sources)
    log.info("Concluído.")


if __name__ == "__main__":
    main()
