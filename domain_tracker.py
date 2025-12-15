#!/usr/bin/env python3
"""
Domain Sales Tracker for Unstoppable Domains Partner Pages
Scrapes partner landing pages to track domain sales status
"""

from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from typing import Dict, List
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Import partner URLs configuration
from partner_urls import get_all_urls

class DomainTracker:
    def __init__(self, delay_between_requests: float = 1.0, headless: bool = True):
        """
        Initialize the domain tracker
        
        Args:
            delay_between_requests: Delay in seconds between HTTP requests
            headless: Whether to run browser in headless mode
        """
        self.delay = delay_between_requests
        self.driver = None
        self._setup_selenium(headless)
    
    def _setup_selenium(self, headless: bool):
        """Setup Selenium WebDriver with WebDriver Manager"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless=new')  # Use new headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            # Add user agent to avoid detection
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            # Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Use WebDriver Manager to automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove webdriver property to avoid detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            print("Selenium WebDriver initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Selenium: {e}")
            raise Exception(f"Could not initialize WebDriver: {e}")
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
    
    def scrape_partner_page(self, partner_url: str) -> Dict:
        """
        Scrape a single partner page for domain information
        
        Args:
            partner_url: URL of the partner page to scrape
            
        Returns:
            Dictionary containing domain information for the partner
        """
        try:
            # Extract partner name from URL
            partner_name = partner_url.rstrip('/').split('/')[-1]
            if not partner_name:  # Handle case where URL ends with /
                partner_name = partner_url.rstrip('/').split('/')[-2]
            
            print(f"Scanning {partner_name}...")
            
            html_content = self._get_page_with_selenium(partner_url)
            
            if not html_content:
                return {
                    'partner': partner_name,
                    'url': partner_url,
                    'error': "Failed to retrieve page content",
                    'timestamp': datetime.now().isoformat(),
                    'has_premium_domains': False
                }
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all domain cards
            domain_cards = soup.find_all('div', class_='domain-card')
            print(f"   Found {len(domain_cards)} domain cards")
            
            # Check if this page has premium domains
            has_premium_domains = len(domain_cards) > 0
            
            domains = []
            sold_count = 0
            total_count = len(domain_cards)
            sold_domains_list = []
            available_domains_list = []
            total_sold_value = 0
            
            for card in domain_cards:
                domain_info = self._extract_domain_info(card)
                domains.append(domain_info)
                
                if domain_info['status'] == 'sold':
                    sold_count += 1
                    sold_domains_list.append(domain_info)
                    # Add to total sold value if price is available
                    if domain_info['price_numeric'] > 0:
                        total_sold_value += domain_info['price_numeric']
                elif domain_info['status'] == 'available':
                    available_domains_list.append(domain_info)
            
            # Calculate percentage sold
            percentage_sold = (sold_count / total_count * 100) if total_count > 0 else 0
            
            print(f"   Result: {sold_count}/{total_count} sold ({percentage_sold:.1f}%)")
            
            return {
                'partner': partner_name,
                'url': partner_url,
                'timestamp': datetime.now().isoformat(),
                'has_premium_domains': has_premium_domains,
                'total_domains': total_count,
                'sold_domains': sold_count,
                'available_domains': total_count - sold_count,
                'percentage_sold': round(percentage_sold, 2),
                'total_sold_value': total_sold_value,
                'domains': domains,
                'sold_domains_list': sold_domains_list,
                'available_domains_list': available_domains_list,
                'needs_update': self._needs_update(percentage_sold, sold_count, total_count, has_premium_domains)
            }
            
        except Exception as e:
            return {
                'partner': partner_url.split('/')[-1] or partner_url.split('/')[-2],
                'url': partner_url,
                'error': f"Parsing failed: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'has_premium_domains': False
            }
    
    def _get_page_with_selenium(self, url: str) -> str:
        """Get page content using Selenium for JavaScript rendering"""
        try:
            self.driver.get(url)
            
            # Wait for domain cards to load - much shorter timeout
            try:
                # Wait up to 5 seconds for at least one domain card to appear
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "domain-card"))
                )
                print("Domain cards loaded")
                # Only wait extra time if we found cards
                time.sleep(1)
            except TimeoutException:
                print("No domain cards found")
                # No additional wait if no cards found
            
            return self.driver.page_source
            
        except WebDriverException as e:
            print(f"Selenium error: {e}")
            return None
    
    def _extract_domain_info(self, card) -> Dict:
        """Extract domain information from a domain card"""
        try:
            # Get domain name
            domain_slug = card.find('div', class_='domain-slug')
            domain_ending = card.find('strong', class_='domain-ending')
            
            domain_name = ""
            if domain_slug and domain_ending:
                domain_name = domain_slug.text.strip() + domain_ending.text.strip()
            
            # Check button status
            button = card.find('button', class_='add-to-cart')
            button_text = button.text.strip().lower() if button else ""
            button_classes = button.get('class', []) if button else []
            has_disabled = button.has_attr('disabled') if button else False
            
            # Determine status based on button text first
            if button_text == "sold":
                status = "sold"
            elif button_text == "coming soon":
                status = "coming_soon"
            elif button_text == "buy now":
                status = "available"
            elif button_text.startswith("available"):  # Handles "Available [date/time]"
                status = "coming_soon"
            else:
                # Fallback: check if button has sold class and is disabled
                is_sold_class = button and ('sold' in button_classes and has_disabled)
                status = "sold" if is_sold_class else "available"
            
            # Get price
            price_element = card.find('div', class_='price')
            price = ""
            price_numeric = 0
            if price_element:
                price_text = price_element.text.strip()
                # Extract price using regex
                price_match = re.search(r'\$(\d+)', price_text)
                if price_match:
                    price = f"${price_match.group(1)}"
                    price_numeric = int(price_match.group(1))
            
            return {
                'domain': domain_name,
                'status': status,
                'price': price,
                'price_numeric': price_numeric,
                'button_text': button.text.strip() if button else ""
            }
            
        except Exception as e:
            return {
                'domain': 'Unknown',
                'status': 'error',
                'price': '',
                'price_numeric': 0,
                'error': str(e)
            }
    
    def _needs_update(self, percentage_sold: float, sold_count: int, total_count: int, has_premium_domains: bool) -> Dict:
        """Determine if a page needs updating based on sales metrics"""
        needs_update = False
        priority = "low"
        reason = ""
        
        # If page has no premium domains, it doesn't need updating
        if not has_premium_domains:
            return {
                'needs_update': False,
                'priority': "none",
                'reason': "No premium domains on this page"
            }
        
        if percentage_sold >= 90:
            needs_update = True
            priority = "high"
            reason = f"Almost sold out ({sold_count}/{total_count} sold)"
        elif percentage_sold >= 50:
            needs_update = True
            priority = "medium"
            reason = f"Mostly sold ({sold_count}/{total_count} sold)"
        elif sold_count == total_count:
            needs_update = True
            priority = "high"
            reason = "Completely sold out"
        
        return {
            'needs_update': needs_update,
            'priority': priority,
            'reason': reason
        }
    
    def scan_all_partners(self, partner_urls: List[str]) -> Dict:
        """
        Scan all partner pages and return comprehensive report
        
        Args:
            partner_urls: List of partner page URLs to scan
            
        Returns:
            Dictionary containing scan results for all partners
        """
        results = []
        
        print(f"Starting scan of {len(partner_urls)} partner pages...")
        
        for i, url in enumerate(partner_urls, 1):
            print(f"Scanning {i}/{len(partner_urls)}: {url}")
            
            result = self.scrape_partner_page(url)
            results.append(result)
            
            # Add delay between requests to be respectful
            if i < len(partner_urls):
                time.sleep(self.delay)
        
        # Generate summary
        summary = self._generate_summary(results)
        
        return {
            'scan_timestamp': datetime.now().isoformat(),
            'summary': summary,
            'results': results
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from scan results"""
        successful_scans = [r for r in results if 'error' not in r]
        failed_scans = [r for r in results if 'error' in r]
        
        # Separate pages with and without premium domains
        pages_with_domains = [r for r in successful_scans if r.get('has_premium_domains', False)]
        pages_without_domains = [r for r in successful_scans if not r.get('has_premium_domains', False)]
        
        needs_update = [r for r in pages_with_domains if r.get('needs_update', {}).get('needs_update', False)]
        high_priority = [r for r in needs_update if r.get('needs_update', {}).get('priority') == 'high']
        
        total_domains = sum(r.get('total_domains', 0) for r in pages_with_domains)
        total_sold = sum(r.get('sold_domains', 0) for r in pages_with_domains)
        total_sold_value = sum(r.get('total_sold_value', 0) for r in pages_with_domains)
        
        return {
            'total_partners_scanned': len(results),
            'successful_scans': len(successful_scans),
            'failed_scans': len(failed_scans),
            'pages_with_premium_domains': len(pages_with_domains),
            'pages_without_premium_domains': len(pages_without_domains),
            'partners_needing_update': len(needs_update),
            'high_priority_updates': len(high_priority),
            'total_domains_across_all_partners': total_domains,
            'total_sold_across_all_partners': total_sold,
            'total_sold_value': total_sold_value,
            'overall_sell_through_rate': round((total_sold / total_domains * 100) if total_domains > 0 else 0, 2)
        }
    
    def print_report(self, scan_results: Dict):
        """Print a clean, concise formatted report"""
        print("\n" + "="*60)
        print("DOMAIN SALES TRACKING REPORT")
        print("="*60)
        
        summary = scan_results['summary']
        print(f"Scan completed: {scan_results['scan_timestamp']}")
        print(f"Partners scanned: {summary['successful_scans']}/{summary['total_partners_scanned']}")
        print(f"Pages with premium domains: {summary['pages_with_premium_domains']}")
        print(f"Pages without premium domains: {summary['pages_without_premium_domains']}")
        print(f"Total domains: {summary['total_domains_across_all_partners']}")
        print(f"Total sold: {summary['total_sold_across_all_partners']}")
        print(f"Total sold value: ${summary['total_sold_value']:,}")
        print(f"Overall sell-through rate: {summary['overall_sell_through_rate']}%")
        print(f"Partners needing update: {summary['partners_needing_update']}")
        print(f"High priority updates: {summary['high_priority_updates']}")
        
        # Show partners that need updates (sorted alphabetically)
        if summary['partners_needing_update'] > 0:
            print("\n" + "-"*40)
            print("PARTNERS NEEDING UPDATES:")
            print("-"*40)
            
            needs_update_results = [r for r in scan_results['results'] if r.get('needs_update', {}).get('needs_update', False)]
            needs_update_results.sort(key=lambda r: r['partner'].lower())
            
            for result in needs_update_results:
                update_info = result['needs_update']
                print(f"{result['partner'].upper()}: {result['sold_domains']}/{result['total_domains']} sold ({result['percentage_sold']}%)")
        
        # Clean summary of all partners with domains (sorted alphabetically)
        print("\n" + "-"*40)
        print("ALL PARTNERS WITH DOMAINS:")
        print("-"*40)
        
        # Sort results alphabetically by partner name
        sorted_results = sorted(scan_results['results'], key=lambda r: r.get('partner', '').lower())
        
        for result in sorted_results:
            if 'error' in result:
                print(f"{result['partner'].upper()} - ERROR")
            elif not result.get('has_premium_domains', False):
                continue  # Skip pages without domains in console output
            else:
                print(f"{result['partner'].upper()}: {result['sold_domains']}/{result['total_domains']} sold ({result['percentage_sold']}%)")
    
    def save_results(self, scan_results: Dict, filename: str = None):
        """Save scan results to JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if filename is None:
            main_filename = f"domain_scan_results_{timestamp}.json"
        else:
            main_filename = filename
        
        # Save main results
        with open(main_filename, 'w', encoding='utf-8') as f:
            json.dump(scan_results, f, indent=2, ensure_ascii=False)
        
        # Save pages without domains to separate file
        pages_without_domains = []
        for result in scan_results['results']:
            if not result.get('has_premium_domains', False) and 'error' not in result:
                pages_without_domains.append(result['url'])
        
        if pages_without_domains:
            no_domains_filename = f"pages_without_domains_{timestamp}.txt"
            with open(no_domains_filename, 'w', encoding='utf-8') as f:
                f.write("# Pages without premium domains - review and remove from scan list\n")
                f.write("# Copy this list to remove these URLs from your partner_urls list\n\n")
                for url in pages_without_domains:
                    f.write(f"{url}\n")
            
            print(f"Main results saved to: {main_filename}")
            print(f"{len(pages_without_domains)} pages without domains saved to: {no_domains_filename}")
        else:
            print(f"Results saved to: {main_filename}")
        
        return main_filename, no_domains_filename if pages_without_domains else None


def main():
    """Main function to run the domain tracker"""
    
    # Load URLs from shared configuration
    # Set include_not_launched=True to scan not-yet-launched partners
    # Set include_not_launched=False to scan only launched partners
    partner_urls = get_all_urls(include_not_launched=False)
    
    print("Starting Domain Sales Tracker")
    print("=" * 50)
    print(f"Will scan {len(partner_urls)} partner pages")
    print("=" * 50)
    
    # Initialize tracker with Selenium
    tracker = DomainTracker(
        delay_between_requests=0.5,  # Reduced delay for faster scanning
        headless=True
    )
    
    # Scan all partners
    results = tracker.scan_all_partners(partner_urls)
    
    # Print report
    tracker.print_report(results)
    
    # Save results
    tracker.save_results(results)
    
    print("\nScan completed!")


if __name__ == "__main__":
    main()