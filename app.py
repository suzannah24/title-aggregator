from flask import Flask, render_template
import feedparser
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import os



app = Flask(__name__)

# The Verge RSS feed URL
VERGE_RSS_URL = "https://www.theverge.com/rss/index.xml"

def get_verge_articles_from_rss():
    """Get recent articles from The Verge RSS feed"""
    articles = []
    start_date = datetime(2022, 1, 1)
    
    try:
        # Get articles from RSS feed
        feed = feedparser.parse(VERGE_RSS_URL)
        
        # Process each entry in the feed
        for entry in feed.entries:
            # Get the publication date
            pub_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if not pub_struct:
                continue
            
            pub_date = datetime(*pub_struct[:6])
            
            # Check if article is from 2022 or later
            if pub_date >= start_date:
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "date": pub_date
                })
        
        print(f"Found {len(articles)} articles from The Verge RSS feed")
    
    except Exception as e:
        print(f"Error fetching articles from RSS: {e}")
    
    return articles

def get_verge_articles_from_archive():
    """Scrape historical articles from The Verge archive pages"""
    articles = []
    start_date = datetime(2022, 1, 1)
    
    # Years and months to scrape
    years = list(range(2022, datetime.now().year + 1))
    months = list(range(1, 13))
    
    try:
        # For each year and month combination
        for year in years:
            for month in months:
                # Skip future months
                if year == datetime.now().year and month > datetime.now().month:
                    continue
                
                # Format URL for the archive page
                archive_url = f"https://www.theverge.com/archives/{year}/{month}"
                print(f"Scraping archive: {archive_url}")
                
                try:
                    # Add a random delay to be respectful to the server
                    time.sleep(random.uniform(1, 2))
                    
                    # Request the archive page
                    response = requests.get(archive_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find article elements
                        article_elements = soup.select('h2 a') or soup.select('.c-entry-box--compact__title a')
                        
                        for article in article_elements:
                            title = article.text.strip()
                            link = article['href']
                            
                            # Make sure the link is absolute
                            if not link.startswith('http'):
                                link = f"https://www.theverge.com{link}"
                            
                            # Extract date from URL or try to get it from the article page
                            date_match = re.search(r'/(\d{4})/(\d{1,2})/(\d{1,2})/', link)
                            
                            if date_match:
                                year, month, day = map(int, date_match.groups())
                                article_date = datetime(year, month, day)
                                
                                # Check if the article is from 2022 or later
                                if article_date >= start_date:
                                    articles.append({
                                        "title": title,
                                        "link": link,
                                        "date": article_date
                                    })
                    else:
                        print(f"Failed to retrieve {archive_url}: Status code {response.status_code}")
                
                except Exception as e:
                    print(f"Error processing archive {year}/{month}: {e}")
        
        print(f"Found {len(articles)} articles from archive pages")
    
    except Exception as e:
        print(f"Error in archive scraping: {e}")
    
    return articles

def get_all_verge_articles():
    """Combine articles from RSS and archive scraping"""
    # Get articles from both sources
    rss_articles = get_verge_articles_from_rss()
    archive_articles = get_verge_articles_from_archive()
    
    # Combine and remove duplicates (based on URL)
    all_articles = rss_articles.copy()
    
    # Track URLs we already have
    existing_urls = {article['link'] for article in all_articles}
    
    # Add non-duplicate articles from archive
    for article in archive_articles:
        if article['link'] not in existing_urls:
            all_articles.append(article)
            existing_urls.add(article['link'])
    
    # Sort by date (latest first)
    all_articles.sort(key=lambda x: x["date"], reverse=True)
    
    print(f"Total unique articles: {len(all_articles)}")
    if all_articles:
        oldest = min(all_articles, key=lambda x: x["date"])
        newest = max(all_articles, key=lambda x: x["date"])
        print(f"Date range: {oldest['date'].strftime('%Y-%m-%d')} to {newest['date'].strftime('%Y-%m-%d')}")
    
    return all_articles

@app.route("/")
def index():
    articles = get_all_verge_articles()
    return render_template("index.html", articles=articles)



if __name__ == "__main__":
    app.run(debug=True)


