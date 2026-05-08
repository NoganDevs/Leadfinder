from http.server import BaseHTTPRequestHandler
import requests
import random
from bs4 import BeautifulSoup
from supabase import create_client
import os
import re

# Credentials from Vercel Env Variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sniffer_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Pick a random Zip from your master list
        zips = ["10001", "90210", "30301", "60601", "75201", "33101"]
        target_zip = random.choice(zips)
        platform = random.choice(["facebook.com", "instagram.com"])
        niche = "restaurant"

        # 2. Execute the Search
        query = f'"{niche}" "{target_zip}" site:{platform} "@gmail.com"'
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}

        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            results = soup.find_all('div', class_='result')

            found_count = 0
            for res in results:
                title = res.find('a', class_='result__a').get_text().strip()
                link = res.find('a', class_='result__a')['href']
                snippet = res.find('a', class_='result__snippet').get_text()
                
                email = sniffer_email(snippet)
                has_site = any(x in snippet.lower() for x in ["www.", "http", ".com/"])

                if email and not has_site:
                    data = {
                        "name": title, "platform": platform, "url": link, 
                        "email": email, "niche": niche, "zip": target_zip
                    }
                    # Supabase 'url' unique constraint prevents duplicates
                    supabase.table("gold_leads").insert(data).execute()
                    found_count += 1

            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Success. Found {found_count} leads in Zip {target_zip}".encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
