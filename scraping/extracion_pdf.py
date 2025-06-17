import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://municipalidaddemomostenango.com/mayo-2025/"
output_folder = "pdfs_mayo_2025"
os.makedirs(output_folder, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

pdf_links = []
for a_tag in soup.find_all("a", href=True):
    href = a_tag['href']
    if href.lower().endswith(".pdf"):
        full_url = urljoin(url, href)
        pdf_links.append(full_url)

print(f"Encontrados {len(pdf_links)} archivos PDF.")

for pdf_url in pdf_links:
    filename = os.path.join(output_folder, pdf_url.split("/")[-1])
    print(f"Descargando {pdf_url} ...")
    r = requests.get(pdf_url, headers=headers)
    r.raise_for_status()
    with open(filename, "wb") as f:
        f.write(r.content)

print("Descarga completada.")