from http.server import BaseHTTPRequestHandler
import requests
import random
from bs4 import BeautifulSoup
from supabase import create_client
import os
import re

# --- HARDCODED CREDENTIALS (PRIVATE REPO ONLY) ---
SUPABASE_URL = "https://ksmkkrzwpnqnvgckwxja.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzbWtrcnp3cG5xbnZnY2t3eGphIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzODkxNDcsImV4cCI6MjA2MDk2NTE0N30.JtyEZ3CG-x8BuVhgVr7UyD_-gwI4y-_vvo8x-96hXSw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sniffer_email(text):
    # Detects common professional emails
    pattern = r'[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Nogan Target Logic: 5 High-Value Categories
        categories = {
            "Construction": ["roofing", "hvac repair", "plumbing contractor", "flooring", "electrician"],
            "Food_Industry": ["pizza parlor", "bakery", "coffee shop", "steakhouse", "food truck"],
            "Health_Wellness": ["personal trainer", "yoga studio", "dental clinic", "chiropractor", "med spa"],
            "Automotive": ["auto detailing", "towing service", "mechanic shop", "window tinting"],
            "Services": ["barbershop", "cleaning service", "pet grooming", "landscaping"]
        }
        
        niche_group = random.choice(list(categories.keys()))
        niche_keyword = random.choice(categories[niche_group])
        
        # High-Value US Locations
        zips = ["10001", "90210", "30301", "60601", "75201", "33101", "28202", "85001", "94105", "20001"]
        target_zip = random.choice(zips)
        
        # Diversify Search: Page 1 or Page 2, Instagram or Facebook
        platform = random.choice(["facebook.com", "instagram.com"])
        page_offset = random.choice([0, 10])

        # 2. Build the Hunting Query
        query = f'"{niche_keyword}" "{target_zip}" site:{platform} "@gmail.com"'
        url = f"https://html.duckduckgo.com/html/?q={query}&s={page_offset}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}

        try:
            r = requests.get(url, headers=headers, timeout=8) 
            soup = BeautifulSoup(r.text, 'html.parser')
            results = soup.find_all('div', class_='result')

            found_count = 0
            for res in results:
                a_tag = res.find('a', class_='result__a')
                if not a_tag: continue
                
                title = a_tag.get_text().strip()
                link = a_tag['href']
                snippet_tag = res.find('a', class_='result__snippet')
                snippet = snippet_tag.get_text() if snippet_tag else ""
                
                email = sniffer_email(snippet)
                # Filtering logic: Look for businesses missing a dedicated .com website
                has_site = any(x in snippet.lower() for x in ["www.", "http", ".com/", ".net", ".org"])

                if email and not has_site:
                    data = {
                        "name": title, 
                        "platform": platform, 
                        "url": link, 
                        "email": email, 
                        "niche": niche_keyword, 
                        "zip": target_zip
                    }
                    # Push to Supabase
                    supabase.table("gold_leads").insert(data).execute()
                    found_count += 1

            # Response for Cron-job.org
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            status_update = f"Target: {niche_keyword} in {target_zip} | Leads Found: {found_count}"
            self.wfile.write(status_update.encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"System Error: {str(e)}".encode())
