from http.server import BaseHTTPRequestHandler
import requests
import random
from bs4 import BeautifulSoup
from supabase import create_client
import os
import re

# --- HARDCODED CREDENTIALS ---
SUPABASE_URL = "https://ksmkkrzwpnqnvgckwxja.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtzbWtrcnp3cG5xbnZnY2t3eGphIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUzODkxNDcsImV4cCI6MjA2MDk2NTE0N30.JtyEZ3CG-x8BuVhgVr7UyD_-gwI4y-_vvo8x-96hXSw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sniffer_email(text):
    # Standard email pattern for harvesting
    pattern = r'[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else "None Found"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Expanded Nogan Categories (Maximum Harvest)
        categories = {
            "Construction": ["roofing", "hvac", "plumbing", "electrician", "renovation"],
            "Food": ["pizza", "bakery", "cafe", "restaurant", "catering"],
            "Wellness": ["gym", "yoga", "dentist", "spa", "chiropractor"],
            "Auto": ["detailing", "towing", "mechanic", "car wash"],
            "Professional": ["barbershop", "landscaping", "cleaning", "lawyer"]
        }
        
        niche_group = random.choice(list(categories.keys()))
        niche_keyword = random.choice(categories[niche_group])
        
        zips = ["10001", "90210", "30301", "60601", "75201", "33101", "85251", "28202", "94105", "20001"]
        target_zip = random.choice(zips)
        
        platform = random.choice(["facebook.com", "instagram.com"])
        page_offset = random.choice([0, 10, 20]) # Added 3rd page for deeper crawling

        # 2. Build Query
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
                
                # Extract Email if exists, otherwise mark as None Found
                email = sniffer_email(snippet)

                # ARCHITECT'S MOVE: No filters. Save everything for the Stage 2 Researcher.
                data = {
                    "name": title, 
                    "platform": platform, 
                    "url": link, 
                    "email": email, 
                    "niche": niche_keyword, 
                    "zip": target_zip,
                    "raw_snippet": snippet # Saving the snippet so Stage 2 can re-read it
                }
                
                # Use UPSERT to prevent duplicate URLs from cluttering your table
                supabase.table("gold_leads").upsert(data, on_conflict="url").execute()
                found_count += 1

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            status_msg = f"Harvest Complete: {found_count} profiles sent to vault."
            self.wfile.write(status_msg.encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Harvest Error: {str(e)}".encode())
