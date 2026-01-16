#!/usr/bin/env python3
"""
Google Sheets Integration for Partner URLs
Fetches partner URLs from a Google Sheet for easy team management
"""

import os
import json
from typing import List, Tuple

# Try to import Google Sheets dependencies
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False


# Configuration - Update these values
SPREADSHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
SHEET_RANGE = 'A:B'  # Column A = URL, Column B = Status (launched/not_launched)


def get_urls_from_sheet(include_not_launched: bool = False) -> List[str]:
    """
    Fetch partner URLs from Google Sheet
    
    Expected sheet format:
    | URL                                              | Status       |
    |--------------------------------------------------|--------------|
    | https://get.unstoppabledomains.com/moon/         | launched     |
    | https://get.unstoppabledomains.com/upcoming/     | not_launched |
    
    Args:
        include_not_launched: If True, includes URLs with 'not_launched' status
        
    Returns:
        List of partner URLs
    """
    if not SHEETS_AVAILABLE:
        raise ImportError(
            "Google Sheets dependencies not installed. "
            "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
        )
    
    if not SPREADSHEET_ID:
        raise ValueError(
            "GOOGLE_SHEET_ID environment variable not set. "
            "Set it to your Google Sheet ID (from the URL)."
        )
    
    # Get credentials from environment or file
    creds = _get_credentials()
    
    # Build the Sheets API service
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # Fetch data
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=SHEET_RANGE
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print("⚠️  No data found in sheet")
        return []
    
    # Skip header row, parse URLs
    urls = []
    for row in values[1:]:  # Skip header
        if not row:
            continue
            
        url = row[0].strip() if len(row) > 0 else ''
        status = row[1].strip().lower() if len(row) > 1 else 'launched'
        
        if not url:
            continue
            
        # Ensure URL ends with /
        if not url.endswith('/'):
            url += '/'
        
        # Filter by status
        if status == 'not_launched' and not include_not_launched:
            continue
            
        urls.append(url)
    
    # Sort alphabetically by partner name
    def get_partner_name(url):
        name = url.rstrip('/').split('/')[-1]
        return name.lower()
    
    urls.sort(key=get_partner_name)
    
    print(f"✅ Loaded {len(urls)} URLs from Google Sheet")
    return urls


def _get_credentials():
    """Get Google API credentials from environment or file"""
    
    # Option 1: Credentials JSON in environment variable (for GitHub Actions)
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        try:
            # Clean up the JSON string - handle potential formatting issues
            creds_json = creds_json.strip()
            
            # Remove BOM if present
            if creds_json.startswith('\ufeff'):
                creds_json = creds_json[1:]
            
            # Handle if the JSON was accidentally wrapped in extra quotes
            if creds_json.startswith('"') and creds_json.endswith('"'):
                creds_json = creds_json[1:-1]
                # Unescape if it was double-escaped
                creds_json = creds_json.replace('\\"', '"').replace('\\n', '\n')
            
            # Try to parse the JSON
            creds_data = json.loads(creds_json)
            
            return Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        except json.JSONDecodeError as e:
            # Provide helpful debug info
            print(f"❌ Failed to parse GOOGLE_CREDENTIALS_JSON: {e}")
            print(f"   JSON length: {len(creds_json)} chars")
            print(f"   Starts with: {repr(creds_json[:20])}")
            print(f"   Ends with: {repr(creds_json[-20:])}")
            raise ValueError(
                f"Invalid JSON in GOOGLE_CREDENTIALS_JSON secret. "
                f"Make sure you copied the ENTIRE contents of the JSON key file "
                f"(starting with {{ and ending with }}). Error: {e}"
            )
    
    # Option 2: Credentials file path
    creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(creds_file):
        return Credentials.from_service_account_file(
            creds_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
    
    raise FileNotFoundError(
        "Google credentials not found. Either:\n"
        "1. Set GOOGLE_CREDENTIALS_JSON env var with the JSON content\n"
        "2. Set GOOGLE_CREDENTIALS_FILE env var with path to credentials.json\n"
        "3. Place credentials.json in the project root"
    )


def test_connection():
    """Test the Google Sheets connection"""
    try:
        urls = get_urls_from_sheet(include_not_launched=True)
        print(f"\n📋 Found {len(urls)} total URLs:")
        for url in urls[:5]:
            print(f"   • {url}")
        if len(urls) > 5:
            print(f"   ... and {len(urls) - 5} more")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🔗 Testing Google Sheets connection...")
    test_connection()
