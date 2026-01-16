#!/usr/bin/env python3
"""
HTML Report Generator for Domain Scan Results
Creates a beautiful, interactive dashboard from scan JSON data
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_html_report(scan_data: dict, output_path: str = "docs/index.html"):
    """Generate an HTML dashboard from scan results"""
    
    summary = scan_data.get('summary', {})
    results = scan_data.get('results', [])
    scan_time = scan_data.get('scan_timestamp', datetime.now().isoformat())
    
    # Parse timestamp for display
    try:
        dt = datetime.fromisoformat(scan_time.replace('Z', '+00:00'))
        formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        formatted_date = scan_time
    
    # Categorize partners
    high_priority = [r for r in results if r.get('needs_update', {}).get('priority') == 'high']
    medium_priority = [r for r in results if r.get('needs_update', {}).get('priority') == 'medium']
    low_priority = [r for r in results if r.get('has_premium_domains') and r.get('needs_update', {}).get('priority') == 'low']
    no_domains = [r for r in results if not r.get('has_premium_domains') and not r.get('error')]
    errors = [r for r in results if r.get('error')]
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Domain Sales Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --bg-card-hover: #22222e;
            --text-primary: #f0f0f5;
            --text-secondary: #8888a0;
            --text-muted: #5a5a70;
            --accent-blue: #4a9eff;
            --accent-purple: #a855f7;
            --accent-pink: #ec4899;
            --accent-green: #22c55e;
            --accent-yellow: #eab308;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --border-subtle: rgba(255,255,255,0.06);
            --gradient-hero: linear-gradient(135deg, #4a9eff 0%, #a855f7 50%, #ec4899 100%);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }}
        
        /* Animated background */
        .bg-pattern {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(74, 158, 255, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(168, 85, 247, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(236, 72, 153, 0.04) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
            z-index: 1;
        }}
        
        /* Header */
        header {{
            text-align: center;
            padding: 3rem 0 4rem;
        }}
        
        .logo {{
            font-size: 0.875rem;
            font-weight: 500;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            background: var(--gradient-hero);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.75rem;
            letter-spacing: -0.02em;
        }}
        
        .subtitle {{
            font-size: 1.125rem;
            color: var(--text-secondary);
            font-weight: 300;
        }}
        
        .scan-time {{
            margin-top: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--text-muted);
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border-radius: 100px;
            display: inline-block;
            border: 1px solid var(--border-subtle);
        }}
        
        @media (max-width: 640px) {{
            h1 {{ font-size: 2.5rem; }}
        }}
        
        /* Sections */
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.25rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-subtle);
        }}
        
        .section-icon {{
            font-size: 1.25rem;
        }}
        
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}
        
        .section-count {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            border-radius: 100px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
        }}
        
        /* Partner Cards */
        .partners-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }}
        
        .partner-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--border-subtle);
            transition: all 0.2s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .partner-card:hover {{
            background: var(--bg-card-hover);
            border-color: rgba(255,255,255,0.1);
            transform: translateY(-1px);
        }}
        
        .partner-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}
        
        .partner-name {{
            font-size: 1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .priority-badge {{
            font-size: 0.65rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .priority-high {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        
        .priority-medium {{
            background: rgba(249, 115, 22, 0.15);
            color: var(--accent-orange);
            border: 1px solid rgba(249, 115, 22, 0.3);
        }}
        
        .priority-low {{
            background: rgba(34, 197, 94, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(34, 197, 94, 0.3);
        }}
        
        .partner-stats {{
            display: flex;
            gap: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
        }}
        
        .partner-stat {{
            display: flex;
            flex-direction: column;
            gap: 0.125rem;
        }}
        
        .partner-stat-label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-family: 'Outfit', sans-serif;
        }}
        
        .partner-stat-value {{
            color: var(--text-primary);
            font-weight: 500;
        }}
        
        /* Progress bar */
        .progress-bar {{
            height: 4px;
            background: var(--bg-secondary);
            border-radius: 2px;
            margin-top: 1rem;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 2px;
            transition: width 0.3s ease;
        }}
        
        .progress-high {{ background: var(--accent-red); }}
        .progress-medium {{ background: var(--accent-orange); }}
        .progress-low {{ background: var(--accent-green); }}
        
        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        /* No domains list */
        .no-domains-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .no-domain-chip {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            padding: 0.4rem 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-subtle);
            border-radius: 6px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        
        .no-domain-chip:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        
        /* Footer */
        footer {{
            text-align: center;
            padding: 3rem 0;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--border-subtle);
            margin-top: 2rem;
        }}
        
        footer a {{
            color: var(--accent-blue);
            text-decoration: none;
        }}
        
        footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="bg-pattern"></div>
    
    <div class="container">
        <header>
            <div class="logo">Unstoppable Domains</div>
            <h1>Partner Dashboard</h1>
            <p class="subtitle">Domain sales tracking across all partner landing pages</p>
            <div class="scan-time">Last updated: {formatted_date}</div>
        </header>
        
'''
    
    # High Priority Section
    if high_priority:
        html += f'''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">🚨</span>
                <h2 class="section-title">High Priority</h2>
                <span class="section-count">{len(high_priority)}</span>
            </div>
            <div class="partners-grid">
'''
        for p in sorted(high_priority, key=lambda x: x.get('percentage_sold', 0), reverse=True):
            html += generate_partner_card(p, 'high')
        html += '''
            </div>
        </section>
'''
    
    # Medium Priority Section
    if medium_priority:
        html += f'''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">⚠️</span>
                <h2 class="section-title">Needs Update</h2>
                <span class="section-count">{len(medium_priority)}</span>
            </div>
            <div class="partners-grid">
'''
        for p in sorted(medium_priority, key=lambda x: x.get('percentage_sold', 0), reverse=True):
            html += generate_partner_card(p, 'medium')
        html += '''
            </div>
        </section>
'''
    
    # Healthy Partners Section
    if low_priority:
        html += f'''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">✅</span>
                <h2 class="section-title">Healthy Partners</h2>
                <span class="section-count">{len(low_priority)}</span>
            </div>
            <div class="partners-grid">
'''
        for p in sorted(low_priority, key=lambda x: x.get('partner', '').lower()):
            html += generate_partner_card(p, 'low')
        html += '''
            </div>
        </section>
'''
    
    # No Domains Section
    if no_domains:
        html += f'''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">⚪</span>
                <h2 class="section-title">No Premium Domains</h2>
                <span class="section-count">{len(no_domains)}</span>
            </div>
            <div class="no-domains-list">
'''
        for p in sorted(no_domains, key=lambda x: x.get('partner', '').lower()):
            html += f'''                <a href="{p.get('url', '#')}" target="_blank" class="no-domain-chip">{p.get('partner', 'Unknown').upper()}</a>
'''
        html += '''
            </div>
        </section>
'''
    
    # Errors Section
    if errors:
        html += f'''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">❌</span>
                <h2 class="section-title">Scan Errors</h2>
                <span class="section-count">{len(errors)}</span>
            </div>
            <div class="no-domains-list">
'''
        for p in sorted(errors, key=lambda x: x.get('partner', '').lower()):
            html += f'''                <a href="{p.get('url', '#')}" target="_blank" class="no-domain-chip">{p.get('partner', 'Unknown').upper()}</a>
'''
        html += '''
            </div>
        </section>
'''
    
    html += '''
        <footer>
            <p>Automated scan powered by <a href="https://github.com">GitHub Actions</a></p>
            <p style="margin-top: 0.5rem;">Runs every Sunday</p>
        </footer>
    </div>
</body>
</html>
'''
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML report generated: {output_path}")
    return output_path


def generate_partner_card(partner: dict, priority: str) -> str:
    """Generate HTML for a single partner card"""
    name = partner.get('partner', 'Unknown')
    url = partner.get('url', '#')
    sold = partner.get('sold_domains', 0)
    total = partner.get('total_domains', 0)
    percentage = partner.get('percentage_sold', 0)
    
    priority_labels = {
        'high': 'Critical',
        'medium': 'Update',
        'low': 'Healthy'
    }
    
    return f'''                <a href="{url}" target="_blank" class="partner-card">
                    <div class="partner-header">
                        <span class="partner-name">{name}</span>
                        <span class="priority-badge priority-{priority}">{priority_labels[priority]}</span>
                    </div>
                    <div class="partner-stats">
                        <div class="partner-stat">
                            <span class="partner-stat-label">Sold</span>
                            <span class="partner-stat-value">{sold}/{total}</span>
                        </div>
                        <div class="partner-stat">
                            <span class="partner-stat-label">Rate</span>
                            <span class="partner-stat-value">{percentage:.1f}%</span>
                        </div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill progress-{priority}" style="width: {min(percentage, 100)}%"></div>
                    </div>
                </a>
'''


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate HTML report from scan results')
    parser.add_argument('--input', '-i', default='scan_results.json',
                        help='Input JSON file from scanner')
    parser.add_argument('--output', '-o', default='docs/index.html',
                        help='Output HTML file path')
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {args.input}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {args.input}")
        sys.exit(1)
    
    generate_html_report(scan_data, args.output)


if __name__ == "__main__":
    main()
