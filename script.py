import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import os
import re

class BlogScraper:
    def __init__(self, start_url, output_file):
        self.start_url = start_url
        self.output_file = output_file
        self.domain = urlparse(start_url).netloc
        self.visited_urls = set()
        self.rp = RobotFileParser()
        self.rp.set_url(urljoin(start_url, '/robots.txt'))
        self.rp.read()
        self.rate_limit = 5  # Delay between requests in seconds

    def is_allowed(self, url):
        return self.rp.can_fetch("*", url)

    def get_soup(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_content(self, soup):
        # This is a basic extraction method. Adjust selectors based on the blog's structure.
        content = {
            'title': soup.find('h1').get_text(strip=True) if soup.find('h1') else '',
            'body': soup.find('article').get_text(strip=True) if soup.find('article') else '',
            'date': soup.find('time').get('datetime') if soup.find('time') else '',
            'tags': [tag.get_text(strip=True) for tag in soup.find_all(class_='tag')],
            'categories': [cat.get_text(strip=True) for cat in soup.find_all(class_='category')],
            'comments': [comment.get_text(strip=True) for comment in soup.find_all(class_='comment')]
        }
        return content

    def save_content(self, content):
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(f"Title: {content['title']}\n")
            f.write(f"Date: {content['date']}\n")
            f.write(f"Tags: {', '.join(content['tags'])}\n")
            f.write(f"Categories: {', '.join(content['categories'])}\n")
            f.write(f"Content:\n{content['body']}\n")
            f.write("Comments:\n")
            for comment in content['comments']:
                f.write(f"- {comment}\n")
            f.write("\n---\n\n")

    def extract_links(self, soup):
        return [urljoin(self.start_url, a['href']) for a in soup.find_all('a', href=True)
                if urlparse(urljoin(self.start_url, a['href'])).netloc == self.domain]

    def scrape(self, url):
        if url in self.visited_urls or not self.is_allowed(url):
            return

        self.visited_urls.add(url)
        print(f"Scraping: {url}")

        soup = self.get_soup(url)
        if not soup:
            return

        content = self.extract_content(soup)
        self.save_content(content)

        for link in self.extract_links(soup):
            time.sleep(self.rate_limit)
            self.scrape(link)

def main():
    start_url = input("Enter the blog's starting URL: ")
    output_file = input("Enter the output file name: ")

    if os.path.exists(output_file):
        os.remove(output_file)

    scraper = BlogScraper(start_url, output_file)
    scraper.scrape(start_url)

    print(f"Scraping completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()
