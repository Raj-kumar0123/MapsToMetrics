import os
import pandas as pd
import matplotlib
# Headless mode active kar rahe hain taaki background me bina crash hue safe PNG image bane
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from config import REPORT_DIR, logging

class LeadAnalyticsEngine:
    def __init__(self, csv_file_path: str):
        self.csv_path = csv_file_path
        self.df = pd.read_csv(csv_file_path) if os.path.exists(csv_file_path) else pd.DataFrame()

    def generate_metrics_and_plots(self) -> str:
        if self.df.empty:
            logging.error("Empty tracking reference context supplied to Analytics Suite.")
            return None

        # Ensure karenge ki reports folder system me exist karta ho
        os.makedirs(REPORT_DIR, exist_ok=True)

        # ---- DYNAMIC COLUMN MATCHING (Lafda Proof) ----
        # Column names ko lowercase karke match karenge taaki phone/phone_number ka chakkar khatam ho sake
        cols_lower = {c.lower(): c for c in self.df.columns}
        
        web_col = cols_lower.get('website', cols_lower.get('web', None))
        email_col = cols_lower.get('email', None)
        phone_col = cols_lower.get('phone_number', cols_lower.get('phone', cols_lower.get('contact', None)))

        total_leads = len(self.df)
        has_web = self.df[web_col].notna().sum() if web_col else 0
        has_email = self.df[email_col].notna().sum() if email_col else 0
        has_phone = self.df[phone_col].notna().sum() if phone_col else 0

        web_perc = (has_web / total_leads) * 100 if total_leads > 0 else 0
        email_perc = (has_email / total_leads) * 100 if total_leads > 0 else 0
        phone_perc = (has_phone / total_leads) * 100 if total_leads > 0 else 0

        # Base name nikal rahe hain chart/report ke filenaming ke liye
        base_name = os.path.basename(self.csv_path).replace(".csv", "")
        chart_filename = f"chart_{base_name}.png"
        chart_path = os.path.join(REPORT_DIR, chart_filename)

        # ---- MATPLOTLIB IMAGE GENERATION ----
        try:
            plt.style.use('ggplot')
            fig, ax = plt.subplots(figsize=(8, 5))
            
            metrics = ['With Website', 'With Email', 'With Phone']
            percentages = [web_perc, email_perc, phone_perc]
            
            ax.bar(metrics, percentages, color=['#3498db', '#2ecc71', '#e67e22'])
            ax.set_ylabel('Percentage Presence (%)')
            ax.set_title('Lead Enrichment Completeness Assessment Metric')
            ax.set_ylim(0, 100)

            # Image ko disk par safe save kar rahe hain
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            logging.info(f"📊 Analytics Chart image successfully created at: {chart_path}")
        except Exception as chart_err:
            logging.error(f"❌ Matplotlib chart image nahi bana paya: {str(chart_err)}")
            chart_filename = "N/A (Generation Failed)"

        # ---- MARKDOWN REPORT GENERATION ----
        report_filename = f"report_{base_name}.md"
        report_path = os.path.join(REPORT_DIR, report_filename)
        
        markdown_content = f"""# Executive Data Quality Summary Report
**Source Context Reference File:** `{os.path.basename(self.csv_path)}`  
**Generated On:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Quantitative Distribution Metrics
* **Total Business Leads Harvested:** {total_leads}
* **Valid Telephone Reachability Mapping:** {has_phone} ({phone_perc:.1f}%)
* **Active Public Web Domain Signatures:** {has_web} ({web_perc:.1f}%)
* **Identified Outbound Business Email Addresses:** {has_email} ({email_perc:.1f}%)

## Asset Maps
Visual distribution plots tracking structural gaps across the target parameter vector are rendered directly to structural visualization asset pathways:
* Component Data Asset Path: `outputs/reports/{chart_filename}`
"""
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logging.info(f"Analytics engine report processing complete. Saved to: {report_path}")
        return report_path