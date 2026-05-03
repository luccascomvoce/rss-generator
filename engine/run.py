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

from scraper import scrape_page, fetch_rss
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
            )
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


def main():
    sources = load_sources()
    if not sources:
        log.warning("Nenhuma fonte encontrada em sources/")
        return

    log.info(f"Carregadas {len(sources)} fontes")
    for cfg in sources:
        process_source(cfg)

    log.info("Concluído.")


if __name__ == "__main__":
    main()
