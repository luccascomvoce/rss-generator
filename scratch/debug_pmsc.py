import requests
from bs4 import BeautifulSoup
import urllib3

# Desabilita avisos de SSL para o debug
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.pm.sc.gov.br/10bpm/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

print(f"Acessando {url}...")
resp = requests.get(url, headers=headers, verify=False, timeout=15)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

# Testa o container da notícia
items = soup.select(".noticia")
print(f"Itens com '.noticia': {len(items)}")

if len(items) > 0:
    for i, item in enumerate(items[:3]):
        title_el = item.select_one(".titulo-noticia a")
        title = title_el.get_text(strip=True) if title_el else "SEM TITULO"
        link = title_el.get("href") if title_el else "SEM LINK"
        print(f"\nItem {i+1}:")
        print(f"  Título: {title}")
        print(f"  Link: {link}")
else:
    print("\nNenhum item encontrado com '.noticia'.")
    # Mostra um pouco do HTML para análise
    print("\nSnippet do HTML:")
    print(resp.text[:2000])
