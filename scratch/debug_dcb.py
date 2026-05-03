import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://defesacivil.blumenau.sc.gov.br/d/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers, verify=False)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("a[href^='/d/noticia/']")
print(f"Items found with 'a[href^=\"/d/noticia/\"]': {len(items)}")

if not items:
    # Try just all links to see what's there
    links = soup.find_all("a")
    print(f"Total links found: {len(links)}")
    for link in links[:10]:
        print(f"  Link: {link.get('href')}")

if items:
    for i, item in enumerate(items[:3]):
        print(f"Item {i+1}:")
        title_el = item.select_one("h3.titulo")
        print(f"  Title: {title_el.get_text(strip=True) if title_el else 'N/A'}")
        data_el = item.select_one("p.data")
        print(f"  Date: {data_el.get_text(strip=True) if data_el else 'N/A'}")
