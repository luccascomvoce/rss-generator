import requests
from bs4 import BeautifulSoup

url = "https://pc.sc.gov.br/?page_id=1258"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

print(f"Acessando {url}...")
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

# Procura por qualquer link que pareça uma notícia para entender a estrutura
links = soup.find_all("a", href=True)
news_links = [l for l in links if "/?p=" in l['href'] or "/noticias/" in l['href']]
print(f"Links de notícias encontrados: {len(news_links)}")

# Testa o seletor Elementor
items = soup.select(".elementor-post")
print(f"Itens com '.elementor-post': {len(items)}")

if len(items) == 0:
    # Se falhou, tenta um seletor mais genérico de artigos
    articles = soup.find_all("article")
    print(f"Itens com 'article': {len(articles)}")
    
    # Mostra um pouco do HTML para análise
    print("\nSnippet do HTML:")
    print(resp.text[:1000])
