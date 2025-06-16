#!/usr/bin/env python3
"""
Simple GUI browser for domain scan results
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime
import webbrowser

class DomainResultsBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Domain Sales Results Browser")
        self.root.geometry("1200x800")
        
        self.data = None
        self.filtered_results = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Top frame for file loading and filters
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # File loading
        ttk.Button(top_frame, text="Load JSON Results", command=self.load_file).pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter options
        ttk.Label(top_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(top_frame, textvariable=self.filter_var, values=[
            "all", "with_domains", "needs_update", "high_priority", "sold_out", "no_sales"
        ], state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', self.apply_filter)
        
        # Search
        ttk.Label(top_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.apply_filter)
        
        # Summary frame
        summary_frame = ttk.LabelFrame(self.root, text="Summary", padding="10")
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.summary_text = tk.Text(summary_frame, height=4, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.X)
        
        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Partners list (left side)
        left_frame = ttk.LabelFrame(main_frame, text="Partners", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Treeview for partners
        columns = ("Partner", "Sold/Total", "Percentage", "Value", "Status")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_partner_select)
        
        # Details panel (right side)
        right_frame = ttk.LabelFrame(main_frame, text="Details", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Partner details
        self.details_text = tk.Text(right_frame, wrap=tk.WORD, width=40)
        details_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.open_url_btn = ttk.Button(button_frame, text="Open URL", command=self.open_url, state=tk.DISABLED)
        self.open_url_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    def load_file(self):
        """Load JSON results file"""
        filename = filedialog.askopenfilename(
            title="Select domain scan results JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                
                self.populate_summary()
                self.populate_results()
                messagebox.showinfo("Success", f"Loaded {len(self.data['results'])} results")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def populate_summary(self):
        """Populate the summary section"""
        if not self.data:
            return
        
        summary = self.data['summary']
        summary_text = f"""Total Partners: {summary['successful_scans']} | With Domains: {summary['pages_with_premium_domains']} | Without Domains: {summary['pages_without_premium_domains']}
Total Domains: {summary['total_domains_across_all_partners']} | Sold: {summary['total_sold_across_all_partners']} | Sell-through: {summary['overall_sell_through_rate']}%
Total Sold Value: ${summary['total_sold_value']:,} | Need Updates: {summary['partners_needing_update']} | High Priority: {summary['high_priority_updates']}
Scan Date: {self.data['scan_timestamp']}"""
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
    
    def populate_results(self):
        """Populate the results tree"""
        if not self.data:
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.filtered_results = []
        
        for result in self.data['results']:
            if self.should_include_result(result):
                self.filtered_results.append(result)
                self.add_result_to_tree(result)
    
    def should_include_result(self, result):
        """Check if result should be included based on filters"""
        if 'error' in result:
            return False
        
        # Apply filter
        filter_value = self.filter_var.get()
        if filter_value == "with_domains" and not result.get('has_premium_domains', False):
            return False
        elif filter_value == "needs_update" and not result.get('needs_update', {}).get('needs_update', False):
            return False
        elif filter_value == "high_priority" and result.get('needs_update', {}).get('priority') != 'high':
            return False
        elif filter_value == "sold_out" and result.get('percentage_sold', 0) != 100:
            return False
        elif filter_value == "no_sales" and result.get('sold_domains', 0) > 0:
            return False
        
        # Apply search
        search_text = self.search_var.get().lower()
        if search_text and search_text not in result['partner'].lower():
            return False
        
        return True
    
    def add_result_to_tree(self, result):
        """Add a result to the tree view"""
        if not result.get('has_premium_domains', False):
            values = (result['partner'], "No domains", "-", "-", "No domains")
        else:
            sold_total = f"{result['sold_domains']}/{result['total_domains']}"
            percentage = f"{result['percentage_sold']:.1f}%"
            value = f"${result['total_sold_value']}"
            
            if result.get('needs_update', {}).get('needs_update', False):
                priority = result['needs_update']['priority']
                status = f"Update needed ({priority})"
            else:
                status = "OK"
            
            values = (result['partner'], sold_total, percentage, value, status)
        
        item = self.tree.insert("", tk.END, values=values)
        
        # Color coding
        if result.get('needs_update', {}).get('priority') == 'high':
            self.tree.set(item, "Status", "🚨 " + values[4])
        elif result.get('needs_update', {}).get('needs_update', False):
            self.tree.set(item, "Status", "⚠️ " + values[4])
    
    def apply_filter(self, event=None):
        """Apply current filters"""
        self.populate_results()
    
    def on_partner_select(self, event):
        """Handle partner selection"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        partner_name = self.tree.item(item, "values")[0]
        
        # Find the result data
        result = None
        for r in self.filtered_results:
            if r['partner'] == partner_name:
                result = r
                break
        
        if result:
            self.show_partner_details(result)
            self.current_result = result
            self.open_url_btn.config(state=tk.NORMAL)
    
    def show_partner_details(self, result):
        """Show detailed information for selected partner"""
        self.details_text.delete(1.0, tk.END)
        
        details = f"Partner: {result['partner'].upper()}\n"
        details += f"URL: {result['url']}\n"
        details += f"Scan Time: {result['timestamp']}\n\n"
        
        if not result.get('has_premium_domains', False):
            details += "❌ No premium domains found on this page\n"
        else:
            details += f"📊 SUMMARY:\n"
            details += f"Total Domains: {result['total_domains']}\n"
            details += f"Sold: {result['sold_domains']} ({result['percentage_sold']:.1f}%)\n"
            details += f"Available: {result['available_domains']}\n"
            details += f"Total Sold Value: ${result['total_sold_value']}\n\n"
            
            if result.get('needs_update', {}).get('needs_update', False):
                update_info = result['needs_update']
                details += f"🔴 UPDATE NEEDED ({update_info['priority'].upper()})\n"
                details += f"Reason: {update_info['reason']}\n\n"
            
            if result['sold_domains_list']:
                details += "💰 SOLD DOMAINS:\n"
                for domain in result['sold_domains_list']:
                    details += f"  • {domain['domain']} - {domain['price']}\n"
                details += "\n"
            
            if result['available_domains_list']:
                details += "🛒 AVAILABLE DOMAINS:\n"
                for domain in result['available_domains_list']:
                    details += f"  • {domain['domain']} - {domain['price']}\n"
        
        self.details_text.insert(1.0, details)
    
    def open_url(self):
        """Open the selected partner's URL in browser"""
        if hasattr(self, 'current_result'):
            webbrowser.open(self.current_result['url'])

def main():
    root = tk.Tk()
    app = DomainResultsBrowser(root)
    root.mainloop()

if __name__ == "__main__":
    main()