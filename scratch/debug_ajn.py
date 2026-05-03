import requests
from bs4 import BeautifulSoup

url = "https://ajnoticias.com.br/ultimas-noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("a.lista-home-4")
print(f"Items found with 'a.lista-home-4': {len(items)}")

if items:
    for i, item in enumerate(items[:3]):
        print(f"Item {i+1}:")
        print(f"  Title: {item.select_one('h3').get_text(strip=True) if item.select_one('h3') else 'N/A'}")
        spans = item.select("div > span")
        print(f"  Spans count: {len(spans)}")
        for j, span in enumerate(spans):
            print(f"    Span {j}: {span.get_text(strip=True)}")
else:
    # Try another selector
    print("Trying alternative selectors...")
    articles = soup.select("article")
    print(f"Articles found: {len(articles)}")
