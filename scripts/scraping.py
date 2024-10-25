import requests
from bs4 import BeautifulSoup
import re
import os
import json
from tqdm import tqdm
from urllib.parse import urljoin

# Base URL to scrape
base_url = "https://www.vanderbilt.edu/datascience/"

# Function to scrape a single page
def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract all text from paragraphs and headers
    paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4'])
    text_content = "\n".join([para.get_text() for para in paragraphs])
    
    # Clean up the text (remove extra whitespace)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    
    return text_content

# Function to scrape all links from a page
def scrape_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all links that point to internal pages
    links = [a.get('href') for a in soup.find_all('a', href=True)]
    full_links = [urljoin(base_url, link) for link in links if link.startswith('/') or link.startswith(base_url)]
    
    # Filter links to ensure they are within the data science section and not PHP or likely empty pages
    data_science_links = [link for link in full_links if link.startswith(base_url) and not link.endswith('.php') and not any(x in link for x in ['login', 'admin', 'wp-', 'feed', 'rss'])]
    
    return list(set(data_science_links))  # Return unique links only

# Function to get all links from the site
def get_all_links(base_url):
    all_links = set([base_url])
    to_visit = [base_url]
    
    while to_visit and len(all_links) < 100:
        current_url = to_visit.pop(0)
        new_links = set(scrape_links(current_url)) - all_links
        all_links.update(new_links)
        to_visit.extend(new_links)
        
        if len(all_links) >= 100:
            all_links = list(all_links)[:100]
            break
    
    return list(all_links)

# Function to scrape all pages
def scrape_all_pages(links):
    for link in tqdm(links, desc="Scraping pages", unit="page"):
        print(f"Scraping: {link}")
        page_text = scrape_page(link)
        
        # Save the scraped content
        filename = link.replace(base_url, '').replace('/', '_')
        if not filename:
            filename = 'index'
        filename = re.sub(r'[^\w\-_\. ]', '_', filename)  # Replace invalid filename characters
        with open(os.path.join(data_dir, f"{filename}.txt"), 'w', encoding='utf-8') as f:
            f.write(page_text)

# Main execution
if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the data directory one level up from the scripts folder
    data_dir = os.path.join(os.path.dirname(script_dir), 'data', 'scraped_data')
    os.makedirs(data_dir, exist_ok=True)

    # Get all links (up to 100)
    print("Gathering links...")
    all_links = get_all_links(base_url)
    print(f"Found {len(all_links)} links")

    # Start scraping the pages
    scrape_all_pages(all_links)
