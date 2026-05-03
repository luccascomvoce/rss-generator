import requests
from bs4 import BeautifulSoup

url = "https://www.defesacivil.sc.gov.br/categoria/noticia/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "lxml")

item = soup.select_one("article.category-noticia")
if item:
    time_el = item.select_one("time")
    if time_el:
        print(f"Time tag: {time_el}")
        print(f"Datetime attr: {time_el.get('datetime')}")
