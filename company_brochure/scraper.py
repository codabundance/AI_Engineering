from __future__ import annotations

from collections import OrderedDict

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


# def fetch_website_links(base_url: str, max_links: int = 25) -> list[str]:
#     response = requests.get(base_url, timeout=15)
#     response.raise_for_status()
#
#     soup = BeautifulSoup(response.text, "html.parser")
#     links: "OrderedDict[str, None]" = OrderedDict()
#
#     for anchor in soup.find_all("a", href=True):
#         absolute_url = urljoin(base_url, anchor["href"]).split("#")[0]
#         if absolute_url.startswith(("http://", "https://")):
#             links[absolute_url] = None
#         if len(links) >= max_links:
#             break
#
#     return list(links.keys())


# def fetch_website_contents(urls: list[str]) -> dict[str, str]:
#     contents: dict[str, str] = {}
#
#     for url in urls:
#         try:
#             response = requests.get(url, timeout=60)
#             response.raise_for_status()
#             contents[url] = _clean_text(response.text)
#         except requests.RequestException as exc:
#             contents[url] = f"ERROR: {exc}"
#
#     return contents
#
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
# }


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]
