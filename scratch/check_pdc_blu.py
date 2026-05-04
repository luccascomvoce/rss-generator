import requests
from bs4 import BeautifulSoup

url = "https://blumenau.portaldacidade.com/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("a.list-content--item")
print(f"Items found with 'a.list-content--item': {len(items)}")

if items:
    for i, item in enumerate(items[:3]):
        print(f"Item {i+1}:")
        title_el = item.select_one("h2.list-content--title")
        print(f"  Title: {title_el.get_text(strip=True) if title_el else 'N/A'}")
        date_el = item.select_one("p.news-item--post-date")
        print(f"  Date: {date_el.get_text(strip=True) if date_el else 'N/A'}")
        summary_el = item.select_one("p.news-item--subtitle")
        print(f"  Summary: {summary_el.get_text(strip=True)[:100] if summary_el else 'N/A'}...")
