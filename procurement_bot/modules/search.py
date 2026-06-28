"""
Web search and scraping module for finding building material suppliers.

Supports multiple search providers (SerpApi, Google Custom Search) and
web scraping for contact information extraction.
"""

import asyncio
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from procurement_bot.config import settings


class SearchProvider:
    """Base class for search providers."""
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Execute search and return results."""
        raise NotImplementedError


class SerpApiSearch(SearchProvider):
    """Search using SerpApi."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Execute search using SerpApi."""
        params = {
            "api_key": self.api_key,
            "engine": "google",
            "q": query,
            "num": num_results,
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:num_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "source": "serpapi",
                    })
            
            return results
            
        except requests.RequestException as e:
            print(f"SerpApi search error: {e}")
            return []


class GoogleCustomSearch(SearchProvider):
    """Search using Google Custom Search API."""
    
    def __init__(self, api_key: str, search_engine_id: str):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Execute search using Google Custom Search API."""
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": num_results,
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "items" in data:
                for item in data["items"][:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "google_custom_search",
                    })
            
            return results
            
        except requests.RequestException as e:
            print(f"Google Custom Search error: {e}")
            return []


class WebScraper:
    """Web scraper for extracting contact information from websites."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return list(set(emails))  # Remove duplicates
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        phone_patterns = [
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+?44[-.\s]?\d{4}[-.\s]?\d{6}',  # UK format
            r'\+?61[-.\s]?\d{1}[-.\s]?\d{4}[-.\s]?\d{4}',  # Australian format
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return list(set(phones))
    
    def scrape_contact_info(self, url: str) -> Dict[str, Any]:
        """Scrape contact information from a website."""
        contact_info = {
            "url": url,
            "emails": [],
            "phones": [],
            "contact_form_url": None,
            "about_us_url": None,
            "company_name": None,
            "success": False,
        }
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract all text
            text = soup.get_text()
            
            # Extract emails
            contact_info["emails"] = self.extract_emails(text)
            
            # Extract phone numbers
            contact_info["phones"] = self.extract_phone_numbers(text)
            
            # Look for contact form
            contact_form = soup.find('form', {'action': re.compile(r'contact', re.I)})
            if contact_form:
                form_action = contact_form.get('action', '')
                if form_action:
                    contact_info["contact_form_url"] = urljoin(url, form_action)
            
            # Look for About Us page
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                if 'about' in href or 'company' in href:
                    contact_info["about_us_url"] = urljoin(url, link['href'])
                    break
            
            # Try to extract company name from title or h1
            title = soup.find('title')
            if title:
                contact_info["company_name"] = title.get_text().strip()
            
            h1 = soup.find('h1')
            if h1 and not contact_info["company_name"]:
                contact_info["company_name"] = h1.get_text().strip()
            
            contact_info["success"] = True
            
        except requests.RequestException as e:
            print(f"Scraping error for {url}: {e}")
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
        
        return contact_info
    
    def scrape_multiple_pages(self, urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
        """Scrape multiple URLs with rate limiting."""
        results = []
        
        for i, url in enumerate(urls):
            if i > 0:
                time.sleep(delay)  # Rate limiting
            
            print(f"Scraping {i+1}/{len(urls)}: {url}")
            contact_info = self.scrape_contact_info(url)
            results.append(contact_info)
        
        return results


class SupplierSearcher:
    """Main class for searching and finding building material suppliers."""
    
    def __init__(self):
        self.search_provider = self._get_search_provider()
        self.scraper = WebScraper()
        self.search_count = 0
        self.max_searches_per_hour = settings.max_searches_per_hour
    
    def _get_search_provider(self) -> SearchProvider:
        """Initialize the configured search provider."""
        if settings.search_provider == "serpapi" and settings.serpapi_key:
            return SerpApiSearch(settings.serpapi_key)
        elif settings.search_provider == "google_custom_search" and settings.google_search_api_key:
            return GoogleCustomSearch(
                settings.google_search_api_key,
                settings.google_search_engine_id
            )
        else:
            print(f"Warning: Search provider '{settings.search_provider}' not configured. Using dummy provider.")
            return DummySearchProvider()
    
    async def search_suppliers(
        self,
        query: str,
        location: Optional[str] = None,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for building material suppliers."""
        # Check rate limiting
        if self.search_count >= self.max_searches_per_hour:
            print("Rate limit reached for searches. Please wait.")
            return []
        
        # Build search query
        full_query = query
        if location:
            full_query = f"{query} {location}"
        
        print(f"Searching for: {full_query}")
        results = await self.search_provider.search(full_query, num_results)
        self.search_count += 1
        
        return results
    
    async def find_and_extract_suppliers(
        self,
        material_type: str,
        location: Optional[str] = None,
        num_results: int = 10,
        scrape_contact_info: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for suppliers and extract their contact information."""
        # Search for suppliers
        query = f"building material suppliers {material_type}"
        search_results = await self.search_suppliers(query, location, num_results)
        
        if not scrape_contact_info:
            return search_results
        
        # Extract contact information from websites
        urls = [result["link"] for result in search_results]
        contact_info_list = self.scraper.scrape_multiple_pages(urls, delay=2.0)
        
        # Combine search results with contact info
        combined_results = []
        for search_result, contact_info in zip(search_results, contact_info_list):
            combined_results.append({
                **search_result,
                "contact_info": contact_info,
            })
        
        return combined_results
    
    def generate_search_queries(self, material_types: List[str], locations: List[str]) -> List[str]:
        """Generate search queries for different materials and locations."""
        queries = []
        
        for material in material_types:
            # Generic query without location
            queries.append(f"building material suppliers {material}")
            
            # Location-specific queries
            for location in locations:
                queries.append(f"building material suppliers {material} {location}")
        
        return queries


class DummySearchProvider(SearchProvider):
    """Dummy search provider for testing when no API is configured."""
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Return dummy search results."""
        print(f"Dummy search for: {query}")
        return [
            {
                "title": f"Example Building Supplies - {query}",
                "link": "https://example.com/building-supplies",
                "snippet": "Your trusted source for quality building materials.",
                "source": "dummy",
            }
        ]


# Singleton instance
supplier_searcher = SupplierSearcher()