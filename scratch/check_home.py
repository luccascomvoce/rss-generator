import requests
from bs4 import BeautifulSoup

url = "https://camarablu.sc.gov.br/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

# Procura seções que pareçam notícias com datas
news_sections = soup.find_all(class_=lambda x: x and 'noticia' in x.lower())
print(f"Found {len(news_sections)} elements with 'noticia' in class")

for section in news_sections[:5]:
    print(f"Class: {section.get('class')}")
    print(section.get_text(strip=True)[:100])
    print("-" * 20)
