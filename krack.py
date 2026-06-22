import os
import json
import time
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re

def load_cookies_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cookies = {}

    if isinstance(data, list):
        for item in data:
            if "name" in item and "value" in item:
                cookies[item["name"]] = item["value"]
    elif isinstance(data, dict):
        cookies = data

    return cookies


args_parser = argparse.ArgumentParser(description="Download course media from krack.ai")
args_parser.add_argument("course_url", nargs="?", help="Course URL", default="https://krack.ai/courses/learn-ukulele/")
args_parser.add_argument("--cookies", help="Path to cookies JSON file", default="cookies.txt")
args_parser.add_argument("--out", help="Download directory", default="downloads")
args = args_parser.parse_args()

cookies = load_cookies_from_json(args.cookies)

headers = {
    "User-Agent": "Mozilla/5.0"
}

COURSE_URL = args.course_url
DOWNLOAD_DIR = args.out

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# setup requests session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(500,502,503,504))
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))

def sanitize_filename(name):
    name = re.sub(r"[:\\/*?\"<>|]", "-", name)
    name = name.strip().replace("\n", " ")
    return name or "file"

def download_file(url, folder):
    filename = url.split("/")[-1].split("?")[0]
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"Skipping: {filename}")
        return

    print(f"Downloading: {filename}")

    try:
        r = session.get(url, headers=headers, cookies=cookies, stream=True, timeout=20)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(1024 * 16):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def get_lessons(course_url):
    print("Fetching lessons...")

    r = requests.get(course_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")

    lessons = []
    current_group = "Unknown"

    # iterate in order
    for el in soup.find_all(["h3", "h4", "a"]):

        # group titles (sections)
        if el.name in ["h3", "h4"]:
            text = el.text.strip()
            if text:
                current_group = text

        # lesson links
        if el.name == "a" and el.get("href"):
            href = el["href"]
            if "/lesson/" in href:
                lessons.append({
                    "url": href,
                    "group": current_group
                })

    return lessons

def process_lesson(lesson):
    url = lesson["url"]
    group_name = lesson["group"]

    print(f"\nVisiting: {url}")
    print(f"Saving to: {group_name}")

    r = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")

    group_folder = os.path.join(DOWNLOAD_DIR, group_name)
    os.makedirs(group_folder, exist_ok=True)

    # videos
    for tag in soup.find_all(["video", "source"]):
        src = tag.get("src")
        if src and ".mp4" in src:
            download_file(urljoin(url, src), group_folder)

    # pdfs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href:
            download_file(urljoin(url, href), group_folder)

lessons = get_lessons(COURSE_URL)

print(f"Found {len(lessons)} lessons")

for lesson in lessons:
    process_lesson(lesson)

print("Done")