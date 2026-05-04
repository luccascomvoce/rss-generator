import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.celesc.com.br/listagem-noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("article.item")
print(f"Items found with 'article.item': {len(items)}")

if items:
    for i, item in enumerate(items[:5]):
        print(f"Item {i+1}:")
        title_el = item.select_one("h2")
        print(f"  Title: {title_el.get_text(strip=True) if title_el else 'N/A'}")
        date_el = item.select_one("time")
        print(f"  Date: {date_el.get_text(strip=True) if date_el else 'N/A'}")
        summary_el = item.select_one("p")
        print(f"  Summary: {summary_el.get_text(strip=True)[:100] if summary_el else 'N/A'}...")
