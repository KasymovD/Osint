import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import time

DATABASE = "news.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            url TEXT UNIQUE,
            published_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_article(source, title, url, published_at):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articles (source, title, url, published_at)
            VALUES (?, ?, ?, ?)
        """, (source, title, url, published_at))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def scrape_bbc():
    source = "BBC"
    url = "https://www.bbc.com/news"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("a", class_="gs-c-promo-heading")
        for article in articles:
            title = article.get_text(strip=True)
            href = article.get("href")
            if href and not href.startswith("http"):
                href = "https://www.bbc.com" + href
            published_at = ""
            insert_article(source, title, href, published_at)
    except Exception as e:
        print(f"Error scraping BBC: {e}")

def scrape_reuters():
    source = "Reuters"
    url = "https://www.reuters.com/news/archive/worldNews"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
        for article in articles:
            header = article.find("h3", class_="story-title")
            if not header:
                header = article.find("h2")
            if header:
                title = header.get_text(strip=True)
            else:
                continue
            link = article.find("a")
            if link:
                href = link.get("href")
                if href and not href.startswith("http"):
                    href = "https://www.reuters.com" + href
            else:
                continue
            timestamp_tag = article.find("span", class_="timestamp")
            published_at = timestamp_tag.get_text(strip=True) if timestamp_tag else ""
            insert_article(source, title, href, published_at)
    except Exception as e:
        print(f"Error scraping Reuters: {e}")

def scrape_cnn():
    source = "CNN"
    url = "https://edition.cnn.com/world"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("h3", class_="cd__headline")
        for article in articles:
            a_tag = article.find("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href")
            if href and not href.startswith("http"):
                href = "https://edition.cnn.com" + href
            published_at = ""
            insert_article(source, title, href, published_at)
    except Exception as e:
        print(f"Error scraping CNN: {e}")

def start_scraping():
    init_db()
    threads = []
    functions = [scrape_bbc, scrape_reuters, scrape_cnn]
    for func in functions:
        t = threading.Thread(target=func)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def display_articles():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, source, title, url, published_at FROM articles")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    start_scraping()
    time.sleep(2)
    display_articles()
