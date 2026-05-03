import requests
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://defesacivil.blumenau.sc.gov.br/d/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers, verify=False)

# Search for common patterns
links = re.findall(r'href="(/d/noticia/[^"]+)"', resp.text)
print(f"Links found via regex: {len(links)}")
for link in links[:5]:
    print(f"  Link: {link}")

if not links:
    print("No news links found in static HTML.")
    # Search for anything that looks like a title
    titles = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', resp.text, re.DOTALL)
    print(f"Titles found: {len(titles)}")
    for title in titles:
        print(f"  Title: {title.strip()}")
