import requests
import xml.etree.ElementTree as ET

url = "https://oblumenauense.com.br/feed/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
}
resp = requests.get(url, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Content length: {len(resp.text)}")

if resp.status_code == 200:
    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    items = channel.findall("item")
    print(f"Items found: {len(items)}")
    if items:
        print(f"First item title: {items[0].find('title').text}")
