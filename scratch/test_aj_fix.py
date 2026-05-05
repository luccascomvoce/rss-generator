import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://ajnoticias.com.br/ultimas-noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

items = soup.select("a.lista-home-4")
print(f"Items: {len(items)}")

for i, el in enumerate(items[:3]):
    print(f"Item {i+1}:")
    image_el = el.select_one("img")
    if image_el:
        print(f"  Raw attrs: {image_el.attrs}")
        
        # Test the new logic
        image_url = ""
        lazy_attrs = ["data-src", "data-lazy", "data-original", "data-echo", "data-url", "src"]
        placeholders = ["pre-img", "placeholder", "loading", "spacer", "transparent", "default"]
        
        for attr in lazy_attrs:
            val = image_el.get(attr)
            if val:
                if not any(p in val.lower() for p in placeholders):
                    image_url = val
                    break
        
        if not image_url:
            image_url = image_el.get("src") or ""
            
        print(f"  Extracted Image URL: {image_url}")
