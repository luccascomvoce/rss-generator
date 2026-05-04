import requests
from bs4 import BeautifulSoup

url = "https://www.celesc.com.br/listagem-noticias?format=feed&type=rss"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers, verify=False)
print(f"Status: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

if resp.status_code == 200:
    soup = BeautifulSoup(resp.content, "xml")
    items = soup.find_all("item")
    print(f"Items found: {len(items)}")
    if items:
        print(f"First item title: {items[0].find('title').get_text(strip=True)}")
        print(f"First item description: {items[0].find('description').get_text(strip=True)[:100]}...")
