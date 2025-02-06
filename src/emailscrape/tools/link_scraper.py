from crewai.tools import BaseTool
from typing import Type, Set
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import time

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _scrape_page(self, url: str, base_domain: str, depth: int = 0) -> dict:
        if depth > 2 or url in self.visited_urls:
            return {}
            
        try:
            self.visited_urls.add(url)
            
            with sync_playwright() as p:
                # Launch browser with more realistic settings
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    has_touch=True,
                    locale='en-US',
                    timezone_id='America/Los_Angeles'
                )
                
                page = context.new_page()
                
                # Navigate to the page
                page.goto(url, wait_until='networkidle')
                
                # Handle Cloudflare challenge
                try:
                    # Wait for and solve Cloudflare challenge
                    if page.locator("text=Verify you are human").is_visible(timeout=5000):
                        # Wait for challenge to complete
                        page.wait_for_selector("text=Verify you are human", state="hidden", timeout=30000)
                        time.sleep(5)  # Additional wait for page load
                    
                    # Handle cookie consent if present
                    for button_text in ["Accept", "Accept All", "I Accept", "Allow Cookies"]:
                        try:
                            page.click(f"text={button_text}", timeout=5000)
                            break
                        except PlaywrightTimeout:
                            continue
                    
                    # Ensure page is fully loaded
                    page.wait_for_load_state('networkidle')
                    
                    # Extract content after challenge is solved
                    content = page.content()
                    
                except PlaywrightTimeout:
                    logger.warning(f"Timeout waiting for Cloudflare challenge on {url}")
                    return {'error': 'Cloudflare challenge timeout'}
                
                finally:
                    browser.close()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                result = {
                    'url': url,
                    'mailto_links': self._extract_mailto(soup),
                    'content': self._extract_content(soup),
                    'sub_pages': {}
                }
                
                # Process subpages only if main page was successfully loaded
                if not result.get('error'):
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_domain, href)
                        
                        if (full_url.startswith(base_domain) and 
                            any(keyword in href.lower() for keyword in ['contact', 'support', 'about', 'help']) and
                            full_url not in self.visited_urls):
                            result['sub_pages'][full_url] = self._scrape_page(full_url, base_domain, depth + 1)
                
                return result
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
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