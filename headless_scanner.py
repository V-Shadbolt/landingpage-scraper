#!/usr/bin/env python3
"""
Headless Domain Scanner for CI/CD Automation
Runs without GUI for GitHub Actions and other automated environments
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List
import re
from dataclasses import dataclass, asdict

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Import partner URLs configuration
from partner_urls import get_all_urls

# Optional Google Sheets integration
def get_urls_with_fallback(include_not_launched: bool = False, use_sheets: bool = False):
    """Get URLs from Google Sheets if configured, otherwise use local file"""
    if use_sheets:
        try:
            from sheets_config import get_urls_from_sheet
            return get_urls_from_sheet(include_not_launched=include_not_launched)
        except Exception as e:
            print(f"⚠️  Google Sheets failed ({e}), falling back to local file")
    return get_all_urls(include_not_launched=include_not_launched)


@dataclass
class ScanResult:
    partner: str
    url: str
    status: str  # 'completed', 'error'
    has_domains: bool
    total_domains: int
    sold_domains: int
    percentage_sold: float
    total_sold_value: int
    error_message: str = ""
    domains_data: List = None


class HeadlessScanner:
    def __init__(self, include_not_launched: bool = False, use_sheets: bool = False):
        self.partner_urls = get_urls_with_fallback(
            include_not_launched=include_not_launched,
            use_sheets=use_sheets
        )
        self.scan_results = {}
        self.driver = None
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # For GitHub Actions, use system Chrome
        if os.environ.get('GITHUB_ACTIONS'):
            chrome_options.binary_location = '/usr/bin/google-chrome'
            self.driver = webdriver.Chrome(options=chrome_options)
        else:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove webdriver property to avoid detection
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        
    def scan_partner(self, url: str, partner_name: str) -> ScanResult:
        """Scan a single partner page"""
        try:
            self.driver.get(url)
            
            # Wait for domain cards
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "domain-card"))
                )
                time.sleep(1)
                has_cards = True
            except TimeoutException:
                has_cards = False
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            domain_cards = soup.find_all('div', class_='domain-card')
            
            if not has_cards or len(domain_cards) == 0:
                return ScanResult(
                    partner=partner_name,
                    url=url,
                    status='completed',
                    has_domains=False,
                    total_domains=0,
                    sold_domains=0,
                    percentage_sold=0,
                    total_sold_value=0,
                    domains_data=[]
                )
            
            # Extract domain information
            domains_data = []
            sold_count = 0
            total_sold_value = 0
            
            for card in domain_cards:
                domain_info = self.extract_domain_info(card)
                domains_data.append(domain_info)
                
                if domain_info['status'] == 'sold':
                    sold_count += 1
                    if domain_info['price_numeric'] > 0:
                        total_sold_value += domain_info['price_numeric']
            
            percentage_sold = (sold_count / len(domain_cards) * 100) if domain_cards else 0
            
            return ScanResult(
                partner=partner_name,
                url=url,
                status='completed',
                has_domains=True,
                total_domains=len(domain_cards),
                sold_domains=sold_count,
                percentage_sold=round(percentage_sold, 2),
                total_sold_value=total_sold_value,
                domains_data=domains_data
            )
            
        except Exception as e:
            return ScanResult(
                partner=partner_name,
                url=url,
                status='error',
                has_domains=False,
                total_domains=0,
                sold_domains=0,
                percentage_sold=0,
                total_sold_value=0,
                error_message=str(e)
            )
    
    def extract_domain_info(self, card) -> Dict:
        """Extract domain information from a card"""
        try:
            domain_slug = card.find('div', class_='domain-slug')
            domain_ending = card.find('strong', class_='domain-ending')
            
            domain_name = ""
            if domain_slug and domain_ending:
                domain_name = domain_slug.text.strip() + domain_ending.text.strip()
            
            button = card.find('button', class_='add-to-cart')
            button_text = button.text.strip().lower() if button else ""
            button_classes = button.get('class', []) if button else []
            has_disabled = button.has_attr('disabled') if button else False
            
            if button_text == "sold":
                status = "sold"
            elif button_text == "coming soon":
                status = "coming_soon"
            elif button_text == "buy now":
                status = "available"
            elif button_text.startswith("available"):
                status = "coming_soon"
            else:
                is_sold_class = button and ('sold' in button_classes and has_disabled)
                status = "sold" if is_sold_class else "available"
            
            price_element = card.find('div', class_='price')
            price = ""
            price_numeric = 0
            if price_element:
                price_text = price_element.text.strip()
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
    
    def run_scan(self) -> Dict:
        """Run the full scan and return results"""
        print(f"🚀 Starting scan of {len(self.partner_urls)} partners...")
        print("=" * 60)
        
        try:
            self.setup_driver()
            
            for i, url in enumerate(self.partner_urls):
                partner_name = url.rstrip('/').split('/')[-1]
                if not partner_name:
                    partner_name = url.rstrip('/').split('/')[-2]
                
                print(f"[{i+1}/{len(self.partner_urls)}] Scanning {partner_name}...", end=" ")
                
                result = self.scan_partner(url, partner_name)
                self.scan_results[partner_name] = result
                
                if result.status == 'error':
                    print(f"❌ Error: {result.error_message[:50]}")
                elif not result.has_domains:
                    print("⚪ No domains")
                elif result.percentage_sold >= 90:
                    print(f"🚨 {result.sold_domains}/{result.total_domains} sold ({result.percentage_sold:.1f}%)")
                elif result.percentage_sold >= 50:
                    print(f"⚠️  {result.sold_domains}/{result.total_domains} sold ({result.percentage_sold:.1f}%)")
                else:
                    print(f"✅ {result.sold_domains}/{result.total_domains} sold ({result.percentage_sold:.1f}%)")
                
                time.sleep(0.5)
            
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive report"""
        completed_results = [r for r in self.scan_results.values() if r.status == 'completed']
        with_domains = [r for r in completed_results if r.has_domains]
        without_domains = [r for r in completed_results if not r.has_domains]
        
        total_domains = sum(r.total_domains for r in with_domains)
        total_sold = sum(r.sold_domains for r in with_domains)
        total_value = sum(r.total_sold_value for r in with_domains)
        
        needs_update = len([r for r in with_domains if r.percentage_sold >= 50])
        high_priority = len([r for r in with_domains if r.percentage_sold >= 90])
        
        sell_through = (total_sold / total_domains * 100) if total_domains > 0 else 0
        
        # Convert results to dict format
        results = []
        sorted_results = sorted(self.scan_results.values(), key=lambda r: r.partner.lower())
        
        for result in sorted_results:
            if result.status == 'error':
                results.append({
                    'partner': result.partner,
                    'url': result.url,
                    'error': result.error_message,
                    'timestamp': datetime.now().isoformat(),
                    'has_premium_domains': False
                })
            else:
                sold_domains_list = [d for d in (result.domains_data or []) if d['status'] == 'sold']
                available_domains_list = [d for d in (result.domains_data or []) if d['status'] == 'available']
                
                if not result.has_domains:
                    needs_update_info = {
                        'needs_update': False,
                        'priority': "none",
                        'reason': "No premium domains on this page"
                    }
                elif result.percentage_sold >= 90:
                    needs_update_info = {
                        'needs_update': True,
                        'priority': "high",
                        'reason': f"Almost sold out ({result.sold_domains}/{result.total_domains} sold)"
                    }
                elif result.percentage_sold >= 50:
                    needs_update_info = {
                        'needs_update': True,
                        'priority': "medium",
                        'reason': f"Mostly sold ({result.sold_domains}/{result.total_domains} sold)"
                    }
                else:
                    needs_update_info = {
                        'needs_update': False,
                        'priority': "low",
                        'reason': ""
                    }
                
                results.append({
                    'partner': result.partner,
                    'url': result.url,
                    'timestamp': datetime.now().isoformat(),
                    'has_premium_domains': result.has_domains,
                    'total_domains': result.total_domains,
                    'sold_domains': result.sold_domains,
                    'available_domains': result.total_domains - result.sold_domains,
                    'percentage_sold': result.percentage_sold,
                    'total_sold_value': result.total_sold_value,
                    'domains': result.domains_data,
                    'sold_domains_list': sold_domains_list,
                    'available_domains_list': available_domains_list,
                    'needs_update': needs_update_info
                })
        
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_partners_scanned': len(self.scan_results),
                'successful_scans': len(completed_results),
                'failed_scans': len([r for r in self.scan_results.values() if r.status == 'error']),
                'pages_with_premium_domains': len(with_domains),
                'pages_without_premium_domains': len(without_domains),
                'partners_needing_update': needs_update,
                'high_priority_updates': high_priority,
                'total_domains_across_all_partners': total_domains,
                'total_sold_across_all_partners': total_sold,
                'total_sold_value': total_value,
                'overall_sell_through_rate': round(sell_through, 2)
            },
            'results': results
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Partners Scanned: {len(self.scan_results)}")
        print(f"Partners with Domains:  {len(with_domains)}")
        print(f"Partners without:       {len(without_domains)}")
        print(f"Total Domains:          {total_domains}")
        print(f"Total Sold:             {total_sold}")
        print(f"Sell-through Rate:      {sell_through:.1f}%")
        print(f"Total Value:            ${total_value:,}")
        print(f"\n🚨 High Priority Updates: {high_priority}")
        print(f"⚠️  Medium Priority:       {needs_update - high_priority}")
        
        return report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Headless Domain Scanner')
    parser.add_argument('--include-not-launched', action='store_true',
                        help='Include not-yet-launched partners in scan')
    parser.add_argument('--use-sheets', action='store_true',
                        help='Fetch URLs from Google Sheets instead of local file')
    parser.add_argument('--output', '-o', default='scan_results.json',
                        help='Output JSON file path')
    args = parser.parse_args()
    
    scanner = HeadlessScanner(
        include_not_launched=args.include_not_launched,
        use_sheets=args.use_sheets
    )
    report = scanner.run_scan()
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to {args.output}")
    
    # Exit with error if there were high priority items
    if report['summary']['high_priority_updates'] > 0:
        sys.exit(0)  # Could use exit(1) to fail the build, but keeping as success
    
    return report


if __name__ == "__main__":
    main()
