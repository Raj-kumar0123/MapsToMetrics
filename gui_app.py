import os
import streamlit as st
import pandas as pd
import glob
from datetime import datetime
from scraper import GoogleMapsScraper

# 1. Page Configuration (UI ka basic setup)
st.set_page_config(
    page_title="Google Maps Pro Scraper",
    page_icon="📍",
    layout="wide"
)

# Sidebar - Inputs ke liye
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=80)
st.sidebar.title("Scraper Controls")
st.sidebar.markdown("---")

keyword = st.sidebar.text_input("🔑 Kya Search Karna Hai?", "Mobile Shops", help="e.g., Mobile Shops, Gyms, Cafes")
city = st.sidebar.text_input("🏙️ City Name", "Aligarh")
state = st.sidebar.text_input("🗺️ State", "Uttar Pradesh")
country = st.sidebar.text_input("🌍 Country", "India")

# ---- DYNAMIC RESULTS LIMIT FEATURE ----
max_results = st.sidebar.number_input(
    "📊 Kitni Leads Chahiye?", 
    min_value=5, 
    max_value=1000, 
    value=20, 
    step=5, 
    help="Jitni zyada leads enter karoge, bot utna zyada scroll karega."
)

st.sidebar.markdown("---")
start_btn = st.sidebar.button("🚀 Start Scraping", use_container_width=True)

# Main Screen Layout
st.title("📍 Google Maps Lead Generation Dashboard")
st.caption("Backend engine connected successfully. Ready to hunt leads!")
st.markdown("---")

# Jab user 'Start Scraping' button dabayega
if start_btn:
    if not keyword or not state or not country:
        st.error("🚨 Bhai! Keyword, State, aur Country fields fill karna zaroori hai.")
    else:
        # Dynamic alerts aur progress status ke liye placeholders
        status_box = st.info(f"⏳ Processing shuru ho gayi hai: **{keyword}** in **{city}, {state}** (Target: {max_results} leads)")
        progress_bar = st.progress(10)
        
        try:
            # Step 1: Scraper Object initialize ho rha hai
            progress_bar.progress(30)
            status_box.info("🤖 Browser launch ho raha hai aur maps par direct query search ho rahi hai...")
            
            # Backend class me max_results ki dynamic limit bhej rahe hain
            scraper = GoogleMapsScraper(
                country=country, 
                state=state, 
                city=city, 
                keyword=keyword, 
                max_results=int(max_results)
            )
            
            # Step 2: Live Scraping execution
            progress_bar.progress(60)
            status_box.info("🕵️‍♂️ Maps se data nikal kar websites deep-crawl ki jaa rhi hain (Email/Phone extraction)...")
            
            csv_path = scraper.execute_sync()
            
            # ==============================================================
            # 🔥 BACKGROUND ENGINE INTEGRATION (Chart/Report Asset Builders)
            # ==============================================================
            try:
                if csv_path and os.path.exists(csv_path):
                    from analytics import LeadAnalyticsEngine
                    engine = LeadAnalyticsEngine(csv_path)
                    engine.generate_metrics_and_plots()  # Yeh lines backend me static report/PNG images banayengi
            except Exception as engine_err:
                import logging
                logging.error(f"Background me report/chart asset banane me lafda hua: {str(engine_err)}")
            # ==============================================================
            
            # Step 3: Success aur Data preview
            if csv_path and os.path.exists(csv_path):
                progress_bar.progress(100)
                status_box.success("🎉 Mubarak ho bhai! Lead extraction complete ho gaya hai.")
                
                # CSV read karke frontend par table dikhana
                df = pd.read_csv(csv_path)
                
                # Column names handling (Kuch bhi uppercase/lowercase ho, safe rahega)
                cols_lower = {c.lower(): c for c in df.columns}
                email_col = cols_lower.get('email', None)
                phone_col = cols_lower.get('phone', cols_lower.get('phone_number', cols_lower.get('contact', None)))
                web_col = cols_lower.get('website', cols_lower.get('web', None))

                # Counts nikalna metrics ke liye
                total_leads = len(df)
                valid_emails = df[email_col].dropna().count() if email_col else 0
                valid_phones = df[phone_col].dropna().count() if phone_col else 0
                valid_webs = df[web_col].dropna().count() if web_col else 0
                
                # Metrics (Chote summary cards)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Total Leads Extracted", value=total_leads)
                with col2:
                    st.metric(label="Emails Found", value=valid_emails)
                
                st.markdown("### 📋 Data Preview (Top 10 Rows)")
                st.dataframe(df.head(10), use_container_width=True)
                
                # ---- SUPER SOLID NATIVE LIVE CHART (NO FILE DEPENDENCY) ----
                st.markdown("---")
                st.markdown("### 📊 Live Lead Enrichment Analytics")
                
                # Live data se naya DataFrame chart ke liye pipeline banana
                chart_df = pd.DataFrame({
                    "Data Metrics": ["Total Leads", "Websites Found", "Phones Found", "Emails Found"],
                    "Count": [total_leads, valid_webs, valid_phones, valid_emails]
                })
                
                # Streamlit ka clean interactive bar chart render karna
                st.bar_chart(
                    chart_df, 
                    x="Data Metrics", 
                    y="Count", 
                    color="#29B5E8"
                )
                st.caption("💡 Yeh chart live aapki sheet ke data se bana hai. Har baar 100% load hoga!")
                
                # Download Button
                st.markdown("---")
                st.markdown("### 📥 File Download")
                with open(csv_path, "rb") as file:
                    st.download_button(
                        label="🔥 Download Full CSV Report",
                        data=file,
                        file_name=os.path.basename(csv_path),
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                progress_bar.progress(0)
                status_box.error("❌ Koi data nahi mila ya pipeline beech me ruk gayi. Check logs!")
                
        except Exception as e:
            progress_bar.progress(0)
            status_box.error(f"💥 Kuch bada lafda hua hai code me: {str(e)}")
else:
    # Default Welcome Screen jab tak button click na ho
    st.info("👈 **Shuru karne ke liye:** Left sidebar me details daalkar **Start Scraping** par click karo. Live data yahan show hoga!")
    
    st.markdown("### 🛠️ System Workflow")
    
    # Clean, professional cards bina kisi background clutter ke
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; border-left: 5px solid #FF4B4B; min-height: 150px;">
            <h4 style="margin-top:0;">1. Target Setup 🎯</h4>
            <p style="color: #A3A8B4; font-size: 14px; line-height: 1.4;">
                Sidebar mein apna target keyword, location aur jitni leads chahiye wo limit set karein.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; border-left: 5px solid #29B5E8; min-height: 150px;">
            <h4 style="margin-top:0;">2. Deep Crawling 🤖</h4>
            <p style="color: #A3A8B4; font-size: 14px; line-height: 1.4;">
                Bot automatically Maps tab tak scroll karega jab tak target limit poori na ho jaye, aur websites se emails niklega.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; border-left: 5px solid #00E676; min-height: 150px;">
            <h4 style="margin-top:0;">3. Instant Export 📥</h4>
            <p style="color: #A3A8B4; font-size: 14px; line-height: 1.4;">
                Process khatam hote hi aapko data ka live preview dikhega aur aap direct clean CSV file download kar sakenge.
            </p>
        </div>
        """, unsafe_allow_html=True)