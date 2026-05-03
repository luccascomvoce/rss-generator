import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://defesacivil.blumenau.sc.gov.br/weather/media/carga_noticias/carga_noticias.json"
resp = requests.get(url, verify=False)
data = resp.json()

print(f"Total items in JSON: {len(data)}")
if data:
    item = data[0]
    print("Sample item:")
    print(json.dumps(item, indent=2, ensure_ascii=False))
