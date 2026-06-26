import os
import re
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
import pandas as pd
from config import SELECTORS, TIMEOUT_MS, BROWSER_HEADLESS, CSV_DIR, MAX_RESULTS, logging

# Windows Terminal Encoding Fix (Charmap Crash Se Bachne Ke Liye)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class GoogleMapsScraper:
    # Bulletproof Constructor: *args aur **kwargs lagaya taaki UI se koi bhi name-mismatch na ho
    def __init__(self, country: str, state: str, city: str, keyword: str = "", max_results: int = None, *args, **kwargs):
        self.country = country.strip()
        self.state = state.strip()
        self.city = city.strip() if city else ""
        
        # Agar UI se 'keyword' ki jagah 'business_keyword' aaye toh bhi handle ho jayega
        if not keyword and "business_keyword" in kwargs:
            self.keyword = kwargs["business_keyword"].strip()
        else:
            self.keyword = keyword.strip()
            
        # Dynamic Max Results Handler
        self.max_results = max_results if max_results is not None else kwargs.get("max_results", MAX_RESULTS)
        
        self.search_query = f"{self.keyword} in {self.city} {self.state} {self.country}".replace("  ", " ")

    def clean_text(self, text: str) -> str:
        if not text:
            return text
        # Special Unicode aur bad elements ko screen se saaf karne ke liye
        return "".join(c for c in text if not (0xE000 <= ord(c) <= 0xF8FF)).strip()

    def deep_scrape_website(self, page, url: str) -> dict:
        """Website par jaakar Email aur Phone dono dhoondhne ke liye"""
        result = {"email": None, "website_phone": None}
        if not url or pd.isna(url):
            return result
        try:
            logging.info(f"Deep scraping website: {url}")
            page.goto(url, timeout=TIMEOUT_MS)
            page.wait_for_load_state("domcontentloaded")
            html_content = page.content()
            
            # 1. Scrape Emails
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', html_content))
            filtered_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
            if filtered_emails:
                result["email"] = ", ".join(filtered_emails)
                
            # 2. Scrape Phone Numbers from Website (Generic Regex for Mobile/Landline)
            phones = set(re.findall(r'(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}', html_content))
            filtered_phones = [p.strip() for p in phones if 8 <= len(re.sub(r'\D', '', p)) <= 15]
            if filtered_phones:
                result["website_phone"] = ", ".join(filtered_phones[:2]) # Top 2 numbers uthayega
                
            return result
        except Exception as e:
            logging.warning(f"Failed to deep scrape website {url}: {str(e)}")
            return result

    def execute_sync(self) -> str:
        logging.info(f"Starting execution loop for query: '{self.search_query}' (Target: {self.max_results})")
        records = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=BROWSER_HEADLESS)
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            
            # ---- TIMEOUT PROTECTOR ----
            # Bad or Ad-items par 30 second hang hone se bachayega, max 10s wait karega
            context.set_default_timeout(10000) 
            
            page = context.new_page()
            
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(self.search_query)
            direct_search_url = f"https://www.google.com/maps/search/{encoded_query}"
            
            logging.info(f"Navigating directly to: {direct_search_url}")
            page.goto(direct_search_url, timeout=TIMEOUT_MS)
            
            feed_selector = "div[role='feed']"
            try:
                page.wait_for_selector(feed_selector, timeout=20000)
            except Exception:
                logging.error("No map result feed container found.")
                browser.close()
                return None

            # Dynamic Fast Scroll Logic
            last_height = page.evaluate("sel => document.querySelector(sel) ? document.querySelector(sel).scrollHeight : 0", feed_selector)
            while True:
                current_count = page.locator(SELECTORS["result_cards"]).count()
                if current_count >= self.max_results:
                    logging.info(f"Target count of {self.max_results} reached in feed. Stopping scroll.")
                    break
                
                page.evaluate("sel => { const el = document.querySelector(sel); if(el) el.scrollTo(0, el.scrollHeight); }", feed_selector)
                page.wait_for_timeout(1500)
                
                new_height = page.evaluate("sel => document.querySelector(sel) ? document.querySelector(sel).scrollHeight : 0", feed_selector)
                if new_height == last_height or page.locator(SELECTORS["endpoint_marker"]).count() > 0:
                    break
                last_height = new_height

            listings = page.locator(SELECTORS["result_cards"]).all()
            total_items = min(len(listings), self.max_results)
            logging.info(f"Processing top {total_items} items...")

            for index, listing in enumerate(listings[:self.max_results]):
                try:
                    logging.info(f"--- Extracting Shop {index + 1}/{total_items} ---")
                    if listing.count() > 0:
                        listing.scroll_into_view_if_needed()
                        listing.click(timeout=5000, force=True)
                        page.wait_for_timeout(2000)

                    # Name Extraction
                    name = "Unknown Name"
                    name_selectors = ["h1.DUwDvf", "h1.fontHeadlineLarge", SELECTORS.get("name", "")]
                    for sel in name_selectors:
                        if sel and page.locator(sel).count() > 0:
                            name_text = page.locator(sel).first.text_content()
                            if name_text:
                                name = name_text.strip()
                                break

                    # Address Extraction
                    address = None
                    address_selectors = ["button[data-item-id='address']", "div.Io6YTe", SELECTORS.get("address", "")]
                    for sel in address_selectors:
                        if sel and page.locator(sel).count() > 0:
                            addr_text = page.locator(sel).first.text_content()
                            if addr_text:
                                address = addr_text.strip()
                                break

                    # Phone (Google Maps waala)
                    maps_phone = None
                    phone_selectors = ["button[data-item-id^='phone:tel:']", SELECTORS.get("phone", "")]
                    for sel in phone_selectors:
                        if sel and page.locator(sel).count() > 0:
                            phone_text = page.locator(sel).first.text_content()
                            if phone_text:
                                maps_phone = phone_text.strip()
                                break

                    # Website Extraction
                    website = None
                    web_selectors = ["a[data-item-id='authority']", SELECTORS.get("website", "")]
                    for sel in web_selectors:
                        if sel and page.locator(sel).count() > 0:
                            web_href = page.locator(sel).first.get_attribute("href")
                            if web_href:
                                website = web_href
                                break

                    # Unicode Clean Strings for Safe Terminal Logging
                    name = self.clean_text(name)
                    address = self.clean_text(address) if address else None
                    maps_phone = self.clean_text(maps_phone) if maps_phone else None

                    # Safe logs inside console terminal
                    logging.info(f"Successfully Parsed -> Name: {name} | Phone: {maps_phone if maps_phone else 'N/A'}")

                    records.append({
                        "business_name": name,
                        "country": self.country,
                        "state": self.state,
                        "city": self.city if self.city else "Unspecified",
                        "address": address,
                        "website": website,
                        "phone_number": maps_phone, 
                        "email": None
                    })
                except Exception as entry_err:
                    logging.warning(f"Skipping item {index + 1} due to error: {str(entry_err)}")
                    continue

            # --- HYBRID EXTRACTION (WEBSITE VISITING LOGIC) ---
            external_page = context.new_page()
            for record in records:
                if record["website"] and record["business_name"] != "Unknown Name":
                    site_data = self.deep_scrape_website(external_page, record["website"])
                    record["email"] = site_data["email"]
                    
                    if not record["phone_number"] and site_data["website_phone"]:
                        safe_biz_name = self.clean_text(record['business_name'])
                        logging.info(f"Found phone number from website for {safe_biz_name}: {site_data['website_phone']}")
                        record["phone_number"] = site_data["website_phone"]
                
                record["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            browser.close()

        if not records:
            return None

        df = pd.DataFrame(records)
        df.drop_duplicates(subset=["business_name", "address"], inplace=True)
        
        filename = f"leads_{self.keyword.lower().replace(' ', '_')}_{self.state.lower().replace(' ', '_')}.csv"
        target_path = os.path.join(CSV_DIR, filename)
        df.to_csv(target_path, index=False)
        logging.info(f"Data saved to: {target_path}")
        return target_path