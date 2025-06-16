#!/usr/bin/env python3
"""
Live Domain Scanner with Real-time GUI Updates
Combines domain scanning with live GUI updates as the scan progresses
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import time
import threading
from datetime import datetime
from typing import Dict, List
import re
import webbrowser
from dataclasses import dataclass
from queue import Queue

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

@dataclass
class ScanResult:
    partner: str
    url: str
    status: str  # 'scanning', 'completed', 'error'
    has_domains: bool
    total_domains: int
    sold_domains: int
    percentage_sold: float
    total_sold_value: int
    error_message: str = ""
    domains_data: List = None

class LiveDomainScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Domain Scanner")
        self.root.geometry("1400x900")
        
        self.partner_urls = []
        self.scan_results = {}
        self.scanning = False
        self.driver = None
        self.scan_thread = None
        self.result_queue = Queue()
        
        # For saving results
        self.full_scan_data = None
        
        self.setup_ui()
        self.setup_default_urls()
        
        # Start the result processor
        self.process_results()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Control frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Scan controls
        self.scan_btn = ttk.Button(control_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, length=300, mode='determinate')
        self.progress.pack(side=tk.LEFT, padx=(10, 10))
        
        self.progress_label = ttk.Label(control_frame, text="Ready to scan")
        self.progress_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # Export buttons
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=(10, 10))
        
        self.export_btn = ttk.Button(control_frame, text="Export Results", command=self.export_results, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_no_domains_btn = ttk.Button(control_frame, text="Export No-Domain URLs", command=self.export_no_domains, state=tk.DISABLED)
        self.export_no_domains_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Summary and statistics
        left_frame = ttk.LabelFrame(main_frame, text="Scan Summary", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.summary_text = tk.Text(left_frame, width=35, height=15, wrap=tk.WORD)
        summary_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right side - Live results
        right_frame = ttk.LabelFrame(main_frame, text="Live Results", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Results treeview
        columns = ("Partner", "Status", "Domains", "Sold/Total", "Percentage", "Action")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=25)
        
        # Configure columns
        self.tree.heading("Partner", text="Partner")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Domains", text="Has Domains")
        self.tree.heading("Sold/Total", text="Sold/Total")
        self.tree.heading("Percentage", text="Percentage")
        self.tree.heading("Action", text="Action Needed")
        
        self.tree.column("Partner", width=120)
        self.tree.column("Status", width=100)
        self.tree.column("Domains", width=100)
        self.tree.column("Sold/Total", width=100)
        self.tree.column("Percentage", width=100)
        self.tree.column("Action", width=120)
        
        tree_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to open URL
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_default_urls(self):
        """Setup the default partner URLs"""
        self.partner_urls = [
            'https://get.unstoppabledomains.com/moon/',
            'https://get.unstoppabledomains.com/u/',
            'https://get.unstoppabledomains.com/quantum/',
            'https://get.unstoppabledomains.com/onchain/',
            'https://get.unstoppabledomains.com/ltc/',
            'https://get.unstoppabledomains.com/her/',
            'https://get.unstoppabledomains.com/xec/',
            'https://get.unstoppabledomains.com/kpm/',
            'https://get.unstoppabledomains.com/nibi/',
            'https://get.unstoppabledomains.com/ask/',
            'https://get.unstoppabledomains.com/south/',
            'https://get.unstoppabledomains.com/calicoin/',
            'https://get.unstoppabledomains.com/hegecoin/',
            'https://get.unstoppabledomains.com/bobi/',
            'https://get.unstoppabledomains.com/twin/',
            'https://get.unstoppabledomains.com/mery/',
            'https://get.unstoppabledomains.com/bch/',
            'https://get.unstoppabledomains.com/mycircle/',
            'https://get.unstoppabledomains.com/derad/',
            'https://get.unstoppabledomains.com/sonic/',
            'https://get.unstoppabledomains.com/pendle/',
            'https://get.unstoppabledomains.com/dejay/',
            'https://get.unstoppabledomains.com/xyo/',
            'https://get.unstoppabledomains.com/swamp/',
            'https://get.unstoppabledomains.com/pengu/',
            'https://get.unstoppabledomains.com/hub/',
            'https://get.unstoppabledomains.com/brave/',
            'https://get.unstoppabledomains.com/ath/',
            'https://get.unstoppabledomains.com/bunni/',
            'https://get.unstoppabledomains.com/collect/',
            'https://get.unstoppabledomains.com/housecoin/',
            'https://get.unstoppabledomains.com/tigershark/',
            'https://get.unstoppabledomains.com/pundi/',
            'https://get.unstoppabledomains.com/imtoken/',
            'https://get.unstoppabledomains.com/ohm/',
            'https://get.unstoppabledomains.com/arculus/',
        ]
        
        # Remove duplicates
        self.partner_urls = list(dict.fromkeys(self.partner_urls))
        
        # Initialize tree with URLs
        for url in self.partner_urls:
            partner_name = url.rstrip('/').split('/')[-1]
            if not partner_name:
                partner_name = url.rstrip('/').split('/')[-2]
            
            self.tree.insert("", tk.END, values=(partner_name, "Waiting", "-", "-", "-", "-"))
    
    def start_scan(self):
        """Start the scanning process"""
        if self.scanning:
            return
        
        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        self.export_no_domains_btn.config(state=tk.DISABLED)
        
        self.progress['maximum'] = len(self.partner_urls)
        self.progress['value'] = 0
        
        # Clear previous results
        self.scan_results.clear()
        
        # Start scanning in a separate thread
        self.scan_thread = threading.Thread(target=self.scan_worker)
        self.scan_thread.daemon = True
        self.scan_thread.start()
    
    def stop_scan(self):
        """Stop the scanning process"""
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="Scan stopped")
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def scan_worker(self):
        """Worker thread for scanning"""
        try:
            # Setup Selenium
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Scan each URL
            for i, url in enumerate(self.partner_urls):
                if not self.scanning:
                    break
                
                partner_name = url.rstrip('/').split('/')[-1]
                if not partner_name:
                    partner_name = url.rstrip('/').split('/')[-2]
                
                # Update status
                self.result_queue.put(('status', partner_name, 'Scanning'))
                
                # Scan the partner
                result = self.scan_partner(url, partner_name)
                
                # Send result to main thread
                self.result_queue.put(('result', result))
                
                # Update progress
                self.result_queue.put(('progress', i + 1))
                
                # Small delay between requests
                time.sleep(0.5)
            
            # Scan completed
            self.result_queue.put(('complete', None))
            
        except Exception as e:
            self.result_queue.put(('error', str(e)))
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
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
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
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
            # Get domain name
            domain_slug = card.find('div', class_='domain-slug')
            domain_ending = card.find('strong', class_='domain-ending')
            
            domain_name = ""
            if domain_slug and domain_ending:
                domain_name = domain_slug.text.strip() + domain_ending.text.strip()
            
            # Check button status
            button = card.find('button', class_='add-to-cart')
            button_text = button.text.strip().lower() if button else ""
            
            # Determine status based on button text
            if button_text == "sold":
                status = "sold"
            elif button_text == "coming soon":
                status = "coming_soon"
            elif button_text == "buy now":
                status = "available"
            else:
                # Fallback: check if button has sold class and is disabled
                is_sold_class = button and ('sold' in button.get('class', []) and button.get('disabled'))
                status = "sold" if is_sold_class else "available"
            
            # Get price
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
    
    def process_results(self):
        """Process results from the scanning thread"""
        try:
            while True:
                try:
                    message_type, data, *extra = self.result_queue.get_nowait()
                    
                    if message_type == 'status':
                        partner_name, status = data, extra[0]
                        self.update_partner_status(partner_name, status)
                        self.status_bar.config(text=f"Scanning {partner_name}...")
                    
                    elif message_type == 'result':
                        result = data
                        self.scan_results[result.partner] = result
                        self.update_partner_result(result)
                        self.update_summary()
                    
                    elif message_type == 'progress':
                        progress = data
                        self.progress['value'] = progress
                        self.progress_label.config(text=f"{progress}/{len(self.partner_urls)}")
                    
                    elif message_type == 'complete':
                        self.scan_completed()
                    
                    elif message_type == 'error':
                        messagebox.showerror("Scan Error", f"An error occurred: {data}")
                        self.stop_scan()
                
                except:
                    break
        
        finally:
            # Schedule next check
            self.root.after(100, self.process_results)
    
    def update_partner_status(self, partner_name: str, status: str):
        """Update partner status in the tree"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            if values[0] == partner_name:
                values[1] = status
                self.tree.item(item, values=values)
                break
    
    def update_partner_result(self, result: ScanResult):
        """Update partner result in the tree"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, 'values'))
            if values[0] == result.partner:
                if result.status == 'error':
                    values[1] = "❌ Error"
                    values[2] = "-"
                    values[3] = "-"
                    values[4] = "-"
                    values[5] = "-"
                elif not result.has_domains:
                    values[1] = "✅ Complete"
                    values[2] = "No"
                    values[3] = "-"
                    values[4] = "-"
                    values[5] = "-"
                else:
                    values[1] = "✅ Complete"
                    values[2] = "Yes"
                    values[3] = f"{result.sold_domains}/{result.total_domains}"
                    values[4] = f"{result.percentage_sold:.1f}%"
                    
                    # Determine action needed
                    if result.percentage_sold >= 90:
                        values[5] = "🚨 High Priority"
                    elif result.percentage_sold >= 75:
                        values[5] = "⚠️ Update Needed"
                    else:
                        values[5] = "✅ OK"
                
                self.tree.item(item, values=values)
                break
    
    def update_summary(self):
        """Update the summary panel"""
        completed_results = [r for r in self.scan_results.values() if r.status == 'completed']
        with_domains = [r for r in completed_results if r.has_domains]
        without_domains = [r for r in completed_results if not r.has_domains]
        
        total_domains = sum(r.total_domains for r in with_domains)
        total_sold = sum(r.sold_domains for r in with_domains)
        total_value = sum(r.total_sold_value for r in with_domains)
        
        needs_update = [r for r in with_domains if r.percentage_sold >= 75]
        high_priority = [r for r in with_domains if r.percentage_sold >= 90]
        
        sell_through = (total_sold / total_domains * 100) if total_domains > 0 else 0
        
        summary = f"""SCAN PROGRESS: {len(completed_results)}/{len(self.partner_urls)}

SUMMARY:
• Total Partners: {len(completed_results)}
• With Domains: {len(with_domains)}
• Without Domains: {len(without_domains)}

DOMAIN STATS:
• Total Domains: {total_domains}
• Total Sold: {total_sold}
• Sell-through Rate: {sell_through:.1f}%
• Total Value: ${total_value:,}

ACTIONS NEEDED:
• Updates Needed: {len(needs_update)}
• High Priority: {len(high_priority)}

PARTNERS NEEDING UPDATES:"""
        
        for r in needs_update:
            priority = "🚨" if r.percentage_sold >= 90 else "⚠️"
            summary += f"\n{priority} {r.partner.upper()}: {r.sold_domains}/{r.total_domains} ({r.percentage_sold:.1f}%)"
        
        # Add all other partners with domains
        other_partners = [r for r in with_domains if r.percentage_sold < 75]
        if other_partners:
            summary += f"\n\nALL OTHER PARTNERS:"
            for r in other_partners:
                summary += f"\n✅ {r.partner.upper()}: {r.sold_domains}/{r.total_domains} ({r.percentage_sold:.1f}%)"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
    
    def scan_completed(self):
        """Handle scan completion"""
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL)
        self.export_no_domains_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="Scan completed!")
        
        # Generate full scan data for export
        self.generate_full_scan_data()
        
        messagebox.showinfo("Scan Complete", f"Scan completed! Processed {len(self.scan_results)} partners.")
    
    def generate_full_scan_data(self):
        """Generate full scan data compatible with original format"""
        completed_results = [r for r in self.scan_results.values() if r.status == 'completed']
        with_domains = [r for r in completed_results if r.has_domains]
        without_domains = [r for r in completed_results if not r.has_domains]
        
        total_domains = sum(r.total_domains for r in with_domains)
        total_sold = sum(r.sold_domains for r in with_domains)
        total_value = sum(r.total_sold_value for r in with_domains)
        
        needs_update = len([r for r in with_domains if r.percentage_sold >= 75])
        high_priority = len([r for r in with_domains if r.percentage_sold >= 90])
        
        sell_through = (total_sold / total_domains * 100) if total_domains > 0 else 0
        
        # Convert to original format
        results = []
        for result in self.scan_results.values():
            if result.status == 'error':
                results.append({
                    'partner': result.partner,
                    'url': result.url,
                    'error': result.error_message,
                    'timestamp': datetime.now().isoformat(),
                    'has_premium_domains': False
                })
            else:
                sold_domains_list = [d for d in result.domains_data if d['status'] == 'sold']
                available_domains_list = [d for d in result.domains_data if d['status'] == 'available']
                
                # Determine update status
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
                elif result.percentage_sold >= 75:
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
        
        self.full_scan_data = {
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
    
    def export_results(self):
        """Export scan results to JSON"""
        if not self.full_scan_data:
            messagebox.showwarning("No Data", "No scan data to export")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"domain_scan_results_{timestamp}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.full_scan_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def export_no_domains(self):
        """Export URLs without domains"""
        no_domain_urls = [r.url for r in self.scan_results.values() if r.status == 'completed' and not r.has_domains]
        
        if not no_domain_urls:
            messagebox.showinfo("No Data", "No pages without domains found")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"pages_without_domains_{timestamp}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("# Pages without premium domains - review and remove from scan list\n")
                    f.write("# Copy this list to remove these URLs from your partner_urls list\n\n")
                    for url in no_domain_urls:
                        f.write(f"{url}\n")
                messagebox.showinfo("Export Success", f"{len(no_domain_urls)} URLs exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def on_double_click(self, event):
        """Handle double-click on tree item"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        partner_name = self.tree.item(item, "values")[0]
        
        # Find the result and open URL
        for result in self.scan_results.values():
            if result.partner == partner_name:
                webbrowser.open(result.url)
                break

def main():
    root = tk.Tk()
    app = LiveDomainScanner(root)
    root.mainloop()

if __name__ == "__main__":
    main()