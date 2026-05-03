import requests
from bs4 import BeautifulSoup

url = "https://camarablu.sc.gov.br/noticias/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("#lista-noticia article.noticia")
print(f"Items found: {len(items)}")

if items:
    print("First item HTML:")
    print(items[0].prettify())
