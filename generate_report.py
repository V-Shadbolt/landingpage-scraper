#!/usr/bin/env python3
"""
HTML Report Generator for Domain Scan Results
Creates a beautiful, interactive dashboard from scan JSON data
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def generate_html_report(scan_data: dict, output_path: str = "docs/index.html", github_repo: str = ""):
    """Generate an HTML dashboard from scan results
    
    Args:
        scan_data: The scan results dictionary
        output_path: Where to write the HTML file
        github_repo: GitHub repo URL (e.g., 'https://github.com/user/repo')
    """
    
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
        
        /* GitHub link */
        .github-link {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s ease;
            z-index: 100;
        }}
        
        .github-link:hover {{
            background: var(--bg-card-hover);
            color: var(--text-primary);
            border-color: rgba(255,255,255,0.15);
        }}
        
        .github-link svg {{
            width: 18px;
            height: 18px;
            fill: currentColor;
        }}
        
        /* Filter controls */
        .filter-bar {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
            flex-wrap: wrap;
        }}
        
        .filter-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .filter-slider {{
            width: 200px;
            accent-color: var(--accent-purple);
        }}
        
        .filter-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--accent-purple);
            min-width: 45px;
        }}
        
        @media (max-width: 640px) {{
            .github-link {{
                top: auto;
                bottom: 1rem;
                right: 1rem;
            }}
            .github-link span {{
                display: none;
            }}
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
    
    <!-- GitHub Link -->
    <a href="{github_repo if github_repo else '#'}" target="_blank" class="github-link" id="github-link" {'style="display:none"' if not github_repo else ''}>
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
        </svg>
        <span>View on GitHub</span>
    </a>
    
    <div class="container">
        <header>
            <div class="logo">Unstoppable Domains</div>
            <h1>Partner Dashboard</h1>
            <p class="subtitle">Domain sales tracking across all partner landing pages</p>
            <div class="scan-time" id="scan-time" data-timestamp="{scan_time}">Last updated: {formatted_date}</div>
        </header>
        
        <div class="filter-bar">
            <span class="filter-label">Healthy threshold:</span>
            <input type="range" class="filter-slider" id="threshold-slider" min="10" max="90" value="50" step="5">
            <span class="filter-value" id="threshold-value">&lt;50%</span>
            <span class="filter-label" style="color: var(--text-muted); font-size: 0.75rem;">(Partners below this % are considered healthy)</span>
        </div>
        
'''
    
    # Collect all partners with domains for JavaScript
    partners_with_domains = []
    for r in results:
        if r.get('has_premium_domains') and not r.get('error'):
            partners_with_domains.append({
                'partner': r.get('partner', 'Unknown'),
                'url': r.get('url', '#'),
                'sold': r.get('sold_domains', 0),
                'total': r.get('total_domains', 0),
                'percentage': r.get('percentage_sold', 0)
            })
    
    # Convert to JSON for JavaScript
    import json as json_module
    partners_json = json_module.dumps(partners_with_domains)
    
    # Add dynamic sections container
    html += f'''
        <!-- Partner data for dynamic filtering -->
        <script id="partners-data" type="application/json">{partners_json}</script>
        
        <!-- Dynamic sections - populated by JavaScript -->
        <div id="dynamic-sections"></div>
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
    
    <script>
        // Convert timestamp to local time with timezone
        (function() {
            const scanTimeEl = document.getElementById('scan-time');
            const timestamp = scanTimeEl.dataset.timestamp;
            
            if (timestamp) {
                try {
                    const date = new Date(timestamp);
                    const options = {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        timeZoneName: 'short'
                    };
                    const localTime = date.toLocaleString(undefined, options);
                    scanTimeEl.textContent = 'Last updated: ' + localTime;
                } catch (e) {
                    console.error('Failed to parse timestamp:', e);
                }
            }
        })();
        
        // Dynamic partner sections
        (function() {
            const slider = document.getElementById('threshold-slider');
            const valueDisplay = document.getElementById('threshold-value');
            const container = document.getElementById('dynamic-sections');
            const partnersData = JSON.parse(document.getElementById('partners-data').textContent);
            
            function createCard(p, priority) {
                const priorityLabels = { high: 'Critical', medium: 'Update', low: 'Healthy' };
                return `
                    <a href="${p.url}" target="_blank" class="partner-card" data-percentage="${p.percentage}">
                        <div class="partner-header">
                            <span class="partner-name">${p.partner}</span>
                            <span class="priority-badge priority-${priority}">${priorityLabels[priority]}</span>
                        </div>
                        <div class="partner-stats">
                            <div class="partner-stat">
                                <span class="partner-stat-label">Sold</span>
                                <span class="partner-stat-value">${p.sold}/${p.total}</span>
                            </div>
                            <div class="partner-stat">
                                <span class="partner-stat-label">Rate</span>
                                <span class="partner-stat-value">${p.percentage.toFixed(1)}%</span>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill progress-${priority}" style="width: ${Math.min(p.percentage, 100)}%"></div>
                        </div>
                    </a>
                `;
            }
            
            function createSection(icon, title, count, cardsHtml) {
                if (count === 0) return '';
                return `
                    <section class="section">
                        <div class="section-header">
                            <span class="section-icon">${icon}</span>
                            <h2 class="section-title">${title}</h2>
                            <span class="section-count">${count}</span>
                        </div>
                        <div class="partners-grid">
                            ${cardsHtml}
                        </div>
                    </section>
                `;
            }
            
            function renderSections() {
                const threshold = parseInt(slider.value);
                valueDisplay.textContent = '<' + threshold + '%';
                
                // Categorize partners based on current threshold
                const highPriority = partnersData.filter(p => p.percentage >= 90);
                const needsUpdate = partnersData.filter(p => p.percentage >= threshold && p.percentage < 90);
                const healthy = partnersData.filter(p => p.percentage < threshold);
                
                // Sort each category
                highPriority.sort((a, b) => b.percentage - a.percentage);
                needsUpdate.sort((a, b) => b.percentage - a.percentage);
                healthy.sort((a, b) => a.partner.toLowerCase().localeCompare(b.partner.toLowerCase()));
                
                // Build HTML
                let html = '';
                
                html += createSection('🚨', 'High Priority', highPriority.length, 
                    highPriority.map(p => createCard(p, 'high')).join(''));
                
                html += createSection('⚠️', 'Needs Update', needsUpdate.length,
                    needsUpdate.map(p => createCard(p, 'medium')).join(''));
                
                html += createSection('✅', 'Healthy Partners', healthy.length,
                    healthy.map(p => createCard(p, 'low')).join(''));
                
                container.innerHTML = html;
            }
            
            // Initial render
            renderSections();
            
            // Re-render on slider change
            slider.addEventListener('input', renderSections);
        })();
    </script>
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
    
    return f'''                <a href="{url}" target="_blank" class="partner-card" data-percentage="{percentage}">
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
    import os
    
    parser = argparse.ArgumentParser(description='Generate HTML report from scan results')
    parser.add_argument('--input', '-i', default='scan_results.json',
                        help='Input JSON file from scanner')
    parser.add_argument('--output', '-o', default='docs/index.html',
                        help='Output HTML file path')
    parser.add_argument('--github-repo', '-g', default='',
                        help='GitHub repository URL for the "View on GitHub" link')
    args = parser.parse_args()
    
    # Try to auto-detect GitHub repo URL from environment
    github_repo = args.github_repo
    if not github_repo and os.environ.get('GITHUB_REPOSITORY'):
        github_repo = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {args.input}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in {args.input}")
        sys.exit(1)
    
    generate_html_report(scan_data, args.output, github_repo=github_repo)


if __name__ == "__main__":
    main()
