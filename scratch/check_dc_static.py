import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://defesacivil.blumenau.sc.gov.br/d/noticias"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers, verify=False)
print(f"Content length: {len(resp.text)}")
print("First 1000 chars:")
print(resp.text[:1000])

if "noticia" in resp.text.lower():
    print("'noticia' found in text.")
else:
    print("'noticia' NOT found in text.")
