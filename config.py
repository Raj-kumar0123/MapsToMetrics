import os
import logging

# Directory Setup (Ye automatic folders bana dega)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")
REPORT_DIR = os.path.join(OUTPUT_DIR, "reports")

for dir_path in [CSV_DIR, REPORT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "platform.log")),
        logging.StreamHandler()
    ]
)

# Playwright Scraper Settings
BROWSER_HEADLESS = False
TIMEOUT_MS = 30000
MAX_RESULTS = 10  # <--- BASS 10 STORES KI LIMIT SET KAR DI HAI TESTING KE LIYE

# DOM Selectors
SELECTORS = {
    "search_input": "input#searchboxinput",
    "search_button": "button#searchbox-searchbutton",
    "result_cards": "div[role='feed'] > div",
    # Bulletproof Playwright Text Selector (Quotes ka lafda hamesha ke liye khatam)
    "endpoint_marker": "text=You've reached the end of the list.",
    "name": "h1.DUwDvf",
    "address": "button[data-item-id^='address'] .Io6YTe",
    "website": "a[data-item-id='authority']",
    "phone": "button[data-item-id^='phone:tel:'] .Io6YTe"
}