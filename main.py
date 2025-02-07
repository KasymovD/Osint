import logging
import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATABASE = "news.db"

def init_db():
    """Initializes the SQLite database and creates the articles table if it doesn't exist."""
    with sqlite3.connect(DATABASE) as conn:
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
    logging.info("Database initialized.")

def insert_article(source, title, url, published_at):
    """Inserts a news article into the database.

    Duplicate entries (based on URL) are silently ignored.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (source, title, url, published_at)
                VALUES (?, ?, ?, ?)
            """, (source, title, url, published_at))
            conn.commit()
    except sqlite3.IntegrityError:
        logging.debug(f"Article already exists: {title}")
    except Exception as e:
        logging.error(f"Error inserting article: {e}")

def get_soup(url, timeout=10):
    """Fetches a URL and returns a BeautifulSoup object for parsing.

    Args:
        url (str): The URL to fetch.
        timeout (int): Timeout for the HTTP request in seconds.

    Returns:
        BeautifulSoup or None: Parsed HTML content, or None if an error occurred.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return None

def scrape_bbc():
    """Scrapes BBC News for articles and inserts them into the database."""
    source = "BBC"
    url = "https://www.bbc.com/news"
    soup = get_soup(url)
    if soup is None:
        return

    articles = soup.find_all("a", class_="gs-c-promo-heading")
    for article in articles:
        title = article.get_text(strip=True)
        href = article.get("href")
        if href and not href.startswith("http"):
            href = "https://www.bbc.com" + href
        published_at = "" 
        insert_article(source, title, href, published_at)
    logging.info("Finished scraping BBC.")

def scrape_reuters():
    """Scrapes Reuters for world news articles and inserts them into the database."""
    source = "Reuters"
    url = "https://www.reuters.com/news/archive/worldNews"
    soup = get_soup(url)
    if soup is None:
        return

    articles = soup.find_all("article")
    for article in articles:
        header = article.find("h3", class_="story-title") or article.find("h2")
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
    logging.info("Finished scraping Reuters.")

def scrape_cnn():
    """Scrapes CNN for world news articles and inserts them into the database."""
    source = "CNN"
    url = "https://edition.cnn.com/world"
    soup = get_soup(url)
    if soup is None:
        return

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
    logging.info("Finished scraping CNN.")

def start_scraping():
    """Starts scraping news articles concurrently from multiple sources."""
    init_db()
    threads = []
    functions = [scrape_bbc, scrape_reuters, scrape_cnn]
    for func in functions:
        thread = threading.Thread(target=func)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    logging.info("All scraping threads have finished.")

def display_articles():
    """Retrieves and prints all articles stored in the database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, source, title, url, published_at FROM articles")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

def main():
    """Main entry point of the application."""
    start_scraping()
    time.sleep(2)
    display_articles()

if __name__ == "__main__":
    main()
