import os
import requests
import time
import random
from bs4 import BeautifulSoup
from supabase import create_client

# --- CLOUD CONFIG (Get these from Supabase.com) ---
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_anon_key"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sniffer_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@(gmail|yahoo|outlook|hotmail|icloud)\.com'
    import re
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None

def cloud_scrape(niche, location, zip_code):
    platforms = ["facebook.com", "instagram.com", "x.com"]
    for platform in platforms:
        query = f'"{niche}" "{zip_code}" site:{platform} "@gmail.com"'
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}

        try:
            r = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, 'html.parser')
            results = soup.find_all('div', class_='result')

            for res in results:
                title = res.find('a', class_='result__a').get_text().strip()
                link = res.find('a', class_='result__a')['href']
                snippet = res.find('a', class_='result__snippet').get_text()
                
                email = sniffer_email(snippet)
                has_site = any(x in snippet.lower() for x in ["www.", "http", ".com/"])

                if email and not has_site:
                    # PUSH TO CLOUD DATABASE
                    data = {
                        "name": title, "platform": platform, "url": link, 
                        "email": email, "niche": niche, "zip": zip_code
                    }
                    supabase.table("gold_leads").insert(data).execute()
                    print(f" [CLOUD SAVED] {title[:20]}")
            
            time.sleep(random.uniform(15, 25))
        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    # You can set these via environment variables on the server
    cloud_scrape("restaurant", "Charlotte", "28202")
