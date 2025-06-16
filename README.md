# Domain Sales Tracker

A comprehensive toolkit for monitoring domain sales across multiple partner landing pages with real-time GUI updates and automated reporting.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## 🚀 Live Domain Scanner (Primary Tool)

The **Live Domain Scanner** is the flagship tool that combines automated web scraping with a real-time GUI interface. Watch your domain sales data update live as the scanner processes each partner page.

### ✨ Key Features

- **Real-time GUI Updates**: Watch scan progress with live statistics
- **Automated Domain Detection**: Distinguishes between sold, available, and "coming soon" domains
- **Smart Prioritization**: Automatically flags partners needing inventory updates
- **Export Functionality**: Generate JSON reports and no-domain URL lists
- **Interactive Results**: Double-click partners to open their pages
- **Progress Tracking**: Visual progress bar and detailed status updates

### 📊 Live Dashboard

- **Scan Summary**: Real-time statistics and partner status
- **Action Items**: Immediate visibility into high-priority updates needed
- **Complete Snapshot**: All partners with domains displayed with current status
- **Export Ready**: One-click export of comprehensive scan results

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Chrome browser (for web scraping)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd domain-sales-tracker
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🎯 Usage

### Live Domain Scanner (Recommended)

```bash
python live_domain_scanner.py
```

1. Click **"Start Scan"** to begin processing all partner pages
2. Monitor real-time progress in the GUI
3. Review live statistics in the summary panel
4. Export results when scan completes
5. Double-click any partner to open their URL

### Sample Live Output

```
SCAN PROGRESS: 25/67

SUMMARY:
• Total Partners: 25
• With Domains: 6
• Without Domains: 19

DOMAIN STATS:
• Total Domains: 43
• Total Sold: 12
• Sell-through Rate: 27.9%

ACTIONS NEEDED:
• Updates Needed: 2
• High Priority: 1

PARTNERS NEEDING UPDATES:
🚨 MOON: 5/6 (83.3%)
⚠️ ONCHAIN: 8/13 (61.5%)

ALL OTHER PARTNERS:
✅ U: 0/6 (0.0%)
✅ QUANTUM: 0/6 (0.0%)
✅ BRAVE: 2/12 (16.7%)
```

## 📁 Additional Tools

### Domain Tracker (Command Line)

For users who prefer command-line interfaces:

```bash
python domain_tracker.py
```

- Console-based scanning with clean output
- Generates JSON results and no-domain URL lists
- Lightweight alternative to the GUI version

### JSON Browser (Results Viewer)

Browse previously generated scan results:

```bash
python json_browser.py
```

- Load and filter existing JSON scan results
- Search and categorize partners
- Detailed partner information viewer
- Export filtered results

## 📋 Output Files

### JSON Results
- **Complete scan data** with domain details, prices, and status
- **Partner classifications** (needs update, priority levels)
- **Summary statistics** across all partners
- **Timestamp tracking** for historical analysis

### No-Domain URLs
- **Clean list** of partner URLs without premium domains
- **Ready to copy/paste** for removing from scan lists
- **Reduces future scan time** by eliminating empty pages

## 🎨 Features

### Smart Domain Classification
- **Sold**: Domains that have been purchased
- **Available**: Domains ready for purchase ("Buy Now")
- **Coming Soon**: Domains not yet launched
- **Error Handling**: Graceful handling of page issues

### Priority System
- **🚨 High Priority**: 90%+ domains sold (immediate attention)
- **⚠️ Medium Priority**: 75%+ domains sold (update needed)
- **✅ OK**: Below 75% sold (no action needed)

### Export Options
- **Full JSON Export**: Complete scan results with all domain data
- **No-Domain URLs**: List of pages without premium domains
- **Timestamped Files**: Automatic file naming with scan timestamps

## 🔧 Configuration

Edit the `partner_urls` list in `live_domain_scanner.py` to customize which partner pages to scan:

```python
self.partner_urls = [
    'https://get.unstoppabledomains.com/partner1/',
    'https://get.unstoppabledomains.com/partner2/',
    # Add your partner URLs here
]
```

## 🐛 Troubleshooting

### ChromeDriver Issues
The tool uses WebDriver Manager to automatically handle ChromeDriver installation. If you encounter browser issues:

1. Ensure Chrome is installed and up to date
2. Check your internet connection
3. Try running with `--no-sandbox` flag if on Linux

### Scan Performance
- **Default timeout**: 5 seconds per page
- **Delay between requests**: 0.5 seconds
- **Headless mode**: Enabled by default for better performance

### Common Issues
- **"No domain cards found"**: Normal for pages without premium domains
- **Export errors**: Ensure you have write permissions in the target directory
- **GUI freezing**: Large scans may take time; monitor the progress bar

## 📊 Understanding Results

### Status Indicators
- **✅ Complete**: Successfully scanned
- **❌ Error**: Failed to scan (check error message)
- **🚨 High Priority**: Immediate inventory update needed
- **⚠️ Update Needed**: Consider refreshing inventory soon

### Metrics
- **Sell-through Rate**: Percentage of total domains sold
- **Total Value**: Sum of all sold domain prices
- **Priority Actions**: Partners requiring immediate attention

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the console output for error messages
3. Open an issue with detailed information about your problem

---

**Happy domain tracking! 🎯**