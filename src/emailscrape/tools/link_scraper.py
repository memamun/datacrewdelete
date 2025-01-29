from crewai.tools import BaseTool
from typing import Type, Set
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class LinkScraperInput(BaseModel):
    """Input schema for LinkScraperTool."""
    url: str = Field(..., description="The URL to scrape links and content from")

class LinkScraperTool(BaseTool):
    name: str = "Link and Content Scraper"
    description: str = (
        "Recursively extracts links, mailto addresses, and content from webpages, focusing on contact information"
    )
    args_schema: Type[BaseModel] = LinkScraperInput
    visited_urls: Set[str] = Field(default_factory=set)

    def _get_base_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _extract_mailto(self, soup):
        mailto_links = []
        # Find all links with mailto:
        for link in soup.find_all('a', href=True):
            if 'mailto:' in link['href'].lower():
                email = link['href'].replace('mailto:', '').strip()
                mailto_links.append(email)
        return mailto_links

    def _extract_content(self, soup):
        content = []
        
        # Check footer content
        footer = soup.find('footer')
        if footer:
            content.append("Footer Content: " + footer.get_text(strip=True))
            
        # Check contact sections
        contact_sections = soup.find_all(['div', 'section', 'article'], 
            class_=lambda x: x and any(word in x.lower() for word in ['contact', 'support', 'help']))
        for section in contact_sections:
            content.append("Contact Section: " + section.get_text(strip=True))
            
        # Extract general content
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            content.append("Main Content: " + main_content.get_text(strip=True))
            
        return "\n".join(content)

    def _scrape_page(self, url: str, base_domain: str, depth: int = 0) -> dict:
        if depth > 2 or url in self.visited_urls:  # Limit recursion depth
            return {}
        
        try:
            self.visited_urls.add(url)
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                'url': url,
                'mailto_links': self._extract_mailto(soup),
                'content': self._extract_content(soup),
                'sub_pages': {}
            }
            
            # Find contact-related links
            contact_keywords = ['contact', 'support', 'about', 'help']
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_domain, href)
                
                # Only follow links within same domain and containing contact keywords
                if (full_url.startswith(base_domain) and 
                    any(keyword in href.lower() for keyword in contact_keywords) and
                    full_url not in self.visited_urls):
                    result['sub_pages'][full_url] = self._scrape_page(full_url, base_domain, depth + 1)
            
            return result
            
        except Exception as e:
            return {'error': str(e)}

    def _format_results(self, results: dict, indent: int = 0) -> str:
        output = []
        indent_str = "  " * indent
        
        output.append(f"{indent_str}=== Page: {results.get('url')} ===")
        
        if 'mailto_links' in results and results['mailto_links']:
            output.append(f"{indent_str}Mailto Links:")
            for email in results['mailto_links']:
                output.append(f"{indent_str}- {email}")
        
        if 'content' in results and results['content']:
            output.append(f"{indent_str}Content:")
            output.append(f"{indent_str}{results['content']}")
        
        if 'sub_pages' in results:
            for sub_url, sub_results in results['sub_pages'].items():
                output.append(self._format_results(sub_results, indent + 1))
        
        return "\n".join(output)

    def _run(self, url: str) -> str:
        self.visited_urls.clear()
        base_domain = self._get_base_domain(url)
        results = self._scrape_page(url, base_domain)
        return self._format_results(results) 