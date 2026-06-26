import sys
from scraper import GoogleMapsScraper
from analytics import LeadAnalyticsEngine
from config import logging

def run_pipeline():
    print("=== Smart Lead Finder & Data Analytics Platform ===")
    country = input("Enter Country (e.g., USA, India): ").strip()
    state = input("Enter State (e.g., Texas, Uttar Pradesh): ").strip()
    city = input("Enter City [Optional - Press Enter to Skip]: ").strip()
    keyword = input("Enter Business Keyword (e.g., Furniture Stores, Mobile Shops): ").strip()

    if not country or not state or not keyword:
        logging.error("Missing mandatory parameter bounds. Country, State, and Keyword are required inputs.")
        sys.exit(1)

    # Step 1: Execute Modular Scraping Operations Pipeline
    scraper = GoogleMapsScraper(country, state, city, keyword)
    raw_data_csv = scraper.execute_sync()

    if not raw_data_csv:
        logging.error("Scraper execution halted without saving record contexts. Analytics pipeline aborted.")
        sys.exit(1)

    # Step 2: Trigger Independent Structural Data Reports Extraction Engine
    analytics_unit = LeadAnalyticsEngine(raw_data_csv)
    summary_report = analytics_unit.generate_metrics_and_plots()

    if summary_report:
        print(f"\n[Success] Pipeline execution complete.")
        print(f"-> Raw Records Saved: {raw_data_csv}")
        print(f"-> Metrics Report Generated: {summary_report}")

if __name__ == "__main__":
    run_pipeline()