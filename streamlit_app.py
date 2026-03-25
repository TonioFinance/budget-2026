import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
import time
import yfinance as yf
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026 Pro", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & AZURE (FULL SAAS PREMIUM EDITION) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');
    @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');

    .stApp { 
        background-color: #030712;
        background-image: radial-gradient(circle at 50% -20%, #172554 0%, #030712 85%);
        color: #F8FAFC; 
        font-family: 'Lato', sans-serif;
    }

    /* --- INSTANT HOVER ANIMATION (0.05s) --- */
    * { transition: all 0.05s ease-out; }

    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    
    /* --- CUSTOM TABS NAVIGATION (CENTERED & ICONIFIED) --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: rgba(15, 23, 42, 0.7);
        padding: 10px 20px;
        border-radius: 26px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(25px);
        margin-bottom: 50px;
        justify-content: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background-color: transparent !important;
        border-radius: 16px !important;
        color: #64748B !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0 35px !important;
        font-size: 15px !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Injection of Phosphor Pictograms via CSS */
    .stTabs [data-baseweb="tab"]::before {
        font-family: "phosphor-regular" !important;
        font-size: 22px;
        transition: all 0.2s ease;
    }
    /* Tab 1 Icon: ChartPie */
    .stTabs [data-baseweb="tab"]:nth-child(1)::before { content: "\\e0da"; }
    /* Tab 2 Icon: ChartLineUp (Investments) */
    .stTabs [data-baseweb="tab"]:nth-child(2)::before { content: "\\e0dc"; }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(37, 99, 235, 0.1) !important;
        color: #FFFFFF !important;
        font-weight: 900 !important;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
    }
    
    .stTabs [aria-selected="true"]::before {
        color: #60A5FA !important;
        filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.8));
        transform: scale(1.1);
    }

    /* --- HERO DASHBOARD (TOP CARD) --- */
    .hero-card {
        background: linear-gradient(160deg, rgba(30, 58, 138, 0.25) 0%, rgba(3, 7, 18, 0.8) 100%);
        padding: 35px 30px;
        border-radius: 24px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-top: 2px solid rgba(59, 130, 246, 0.7);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), inset 0 1px 20px rgba(59, 130, 246, 0.1);
        backdrop-filter: blur(15px);
        margin-bottom: 25px;
        text-align: center;
    }
    .hero-top-metrics {
        display: flex;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 13px;
        color: #93C5FD;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    .hero-main-value {
        font-size: 52px;
        font-weight: 900;
        color: #FFFFFF;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
        margin-bottom: 25px;
        letter-spacing: -1px;
    }
    
    /* Smart Insight Banner */
    .insight-banner {
        margin-top: 25px;
        padding: 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .insight-green { background: rgba(16, 185, 129, 0.1); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .insight-orange { background: rgba(245, 158, 11, 0.1); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .insight-red { background: rgba(225, 29, 72, 0.1); color: #FB7185; border: 1px solid rgba(225, 29, 72, 0.3); }

    /* --- CATEGORY CARD SYSTEM --- */
    .cat-card {
        background: rgba(255,255,255,0.02);
        padding: 16px 20px;
        border-radius: 18px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.04);
        cursor: pointer;
    }
    .cat-card:hover {
        background: rgba(59, 130, 246, 0.08);
        transform: scale(1.02);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .cat-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; width: 100%; }
    .cat-label { color: #FFFFFF !important; font-size: 16px !important; font-weight: 700; }
    .cat-amount { color: #FFFFFF !important; font-size: 15px; font-weight: 700; text-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }

    /* --- RECENT ACTIVITY CARDS --- */
    .transaction-card {
        background: rgba(255, 255, 255, 0.02); 
        border-radius: 16px; 
        padding: 14px 18px; 
        margin-bottom: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .transaction-card:hover {
        transform: translateX(8px) scale(1.01);
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .trans-amount { color: #FFFFFF !important; font-weight: 800; font-size: 15px; }

    /* --- INVESTMENT CARDS (REAL LOGOS DESIGN) --- */
    .inv-card {
        background: rgba(255, 255, 255, 0.02); 
        border-radius: 18px; 
        padding: 18px 22px; 
        margin-bottom: 14px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        border: 1px solid rgba(255,255,255,0.04);
        transition: all 0.2s ease;
    }
    .inv-card:hover {
        transform: translateY(-2px);
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
    }
    .inv-left { display: flex; align-items: center; gap: 16px; }
    
    /* Actual Real Image Styling */
    .inv-logo { 
        width: 48px; height: 48px; 
        border-radius: 50%; 
        object-fit: cover;
        background-color: #030712; 
        border: 2px solid rgba(96, 165, 250, 0.4);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        flex-shrink: 0;
    }
    
    .inv-name { color: #FFFFFF; font-weight: 800; font-size: 17px; letter-spacing: -0.2px; }
    .inv-ticker { color: #94A3B8; font-size: 13px; margin-top:3px; font-weight: 600; }
    .inv-right { text-align: right; }
    .inv-top-val { color: #FFFFFF; font-weight: 800; font-size: 17px; }
    .inv-bottom-val { margin-top: 4px; font-size: 14px; font-weight: 800; }
    .text-green { color: #34D399; }
    .text-red { color: #FB7185; }

    /* --- EXPANDER & FORM PREMIUM --- */
    .stExpander {
        background: rgba(15, 23, 42, 0.2) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 16px !important;
        margin-bottom: 15px !important;
        overflow: hidden;
    }
    .stExpander details summary {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        color: white !important;
        padding: 14px 20px !important;
        font-weight: 900 !important;
        letter-spacing: 1.5px !important;
        border-radius: 14px !important;
    }
    
    /* Input Styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }

    /* --- BLUE GLOW BUTTON (CONFIRM) --- */
    div[data-testid="stButton"] > button, div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 16px !important;
        height: 3.8rem !important;
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.2), inset 0 1px 2px rgba(255,255,255,0.2) !important;
        transition: all 0.2s ease-out !important;
        width: 100%;
        color: white !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px;
    }

    /* --- CHART GLASS CONTAINER --- */
    .chart-container {
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 24px;
        padding: 20px;
        margin-top: 20px;
        text-align: center; /* ALIGNEMENT CORRIGÉ DES TITRES */
    }
    
    /* Make dataframe look better in dark mode */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- FORMATTING HELPERS ---
def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

def format_chf(value):
    return f"{value:,.2f}".replace(",", "'")

def get_progress_html(name, reel, prevu):
    if prevu > 0: percent = reel / prevu
    else: percent = 1.0 if reel > 0 else 0.0
    pct_str = f"{min(percent*100, 100):.1f}%"
    bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" if percent >= 1.0 else "linear-gradient(90deg, #B45309, #F59E0B)" if percent >= 0.66 else "linear-gradient(90deg, #059669, #10B981)" 
    cat_ui_map = {"Courses": ("Groceries", "ph-shopping-cart"), "Sorties/Restos": ("Dining", "ph-fork-knife"), "Transport": ("Transport", "ph-car"), "Loisirs": ("Leisure", "ph-game-controller"), "Imprévus": ("Unexpected", "ph-warning-circle"), "Shopping": ("Shopping", "ph-tote"), "Hygiène": ("Hygiene", "ph-drop")}
    ui_name, icon = cat_ui_map.get(name.strip(), (name, "ph-wallet"))
    return f"""<div class="cat-card"><div class="cat-container"><div style="display:flex; align-items:center; gap:10px;"><i class="ph {icon}" style="font-size:22px; color:#60A5FA;"></i><span class="cat-label">{ui_name}</span></div><span class="cat-amount">{format_chf(reel)} CHF</span></div><div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden;"><div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div></div></div>"""

def get_transaction_html(date, merchant, amount, category):
    cat_ui_map = {"Courses": ("Groceries", "ph-shopping-cart"), "Sorties/Restos": ("Dining", "ph-fork-knife"), "Transport": ("Transport", "ph-car"), "Loisirs": ("Leisure", "ph-game-controller"), "Imprévus": ("Unexpected", "ph-warning-circle"), "Shopping": ("Shopping", "ph-tote"), "Hygiène": ("Hygiene", "ph-drop")}
    ui_category, icon = cat_ui_map.get(category.strip(), (category, "ph-wallet"))
    return f"""<div class="transaction-card"><div style="display:flex; align-items:center; gap:15px;"><div style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2); width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;"><i class="ph {icon}" style="font-size:20px; color:#60A5FA;"></i></div><div><div style="color: #FFFFFF; font-weight: 700; font-size: 15px;">{merchant}</div><div style="color: #64748B; font-size: 12px; margin-top:2px;">{date} • {ui_category}</div></div></div><div class="trans-amount">{amount}</div></div>"""

# --- LOGO MATCHER (SMART CACHED) ---
@st.cache_data(show_spinner=False, ttl=86400)
def get_asset_logo(ticker, asset_name):
    t_up = str(ticker).upper()
    n_up = str(asset_name).upper()
    
    if "BTC" in t_up or "BITCOIN" in n_up: return "https://cryptologos.cc/logos/bitcoin-btc-logo.png"
    if "ETH" in t_up or "ETHEREUM" in n_up: return "https://cryptologos.cc/logos/ethereum-eth-logo.png"
    if "SOL" in t_up or "SOLANA" in n_up: return "https://cryptologos.cc/logos/solana-sol-logo.png"
    
    try:
        info = yf.Ticker(ticker).info
        website = info.get('website', '')
        if website:
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            return f"https://logo.clearbit.com/{domain}"
    except:
        pass
        
    clean_name = str(asset_name).replace(' ', '+')
    return f"https://ui-avatars.com/api/?name={clean_name}&background=0F172A&color=60A5FA&rounded=true&bold=true"

def convert_google_drive_link(url):
    """
    Robustly converts Google Drive 'open?id=' or 'file/d/' links into direct download links.
    Returns the original URL if no conversion pattern matches.
    """
    if not isinstance(url, str): return url
    if "drive.google.com" not in url: return url

    # Case 1: URL with 'open?id='
    open_match = re.search(r"open\?id=([a-zA-Z0-9_-]+)", url)
    if open_match:
        file_id = open_match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    # Case 2: URL with 'file/d/.../view'
    file_match = re.search(r"file/d/([a-zA-Z0-9_-]+)", url)
    if file_match:
        file_id = file_match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"

    return url

def is_valid_custom_logo(url):
    """Checks if a custom logo URL looks valid enough to try rendering."""
    if not isinstance(url, str): return False
    url = url.strip()
    if not url: return False
    # If it's not a direct Drive uc? export link, and it doesn't look like a direct image extension, be wary
    # This prevents the broken image icon seen in images from drive 'open' links
    if "drive.google.com" in url:
        return "uc?export=view" in url
    # Simple check for direct image patterns or CLEARBIT
    return url.startswith("http") and (any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg", ".svg"]) or "clearbit" in url)

# --- CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets: return None
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception: return None

SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"
client = get_gsheet_client()
if not client: st.stop()
try: sh = client.open_by_key(SHEET_ID)
except Exception: st.error("Access Denied"); st.stop()

# --- NAVIGATION ---
months_map = {"January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril", "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août", "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"}
now = datetime.now()
selected_month_en = st.sidebar.selectbox("Select Month", list(months_map.keys()), index=now.month - 1)
selected_month = months_map[selected_month_en]
ws = sh.worksheet(next((s for s in [s.title for s in sh.worksheets()] if selected_month.lower() in s.lower()), None))

# --- DATA EXTRACTION ---
all_rows = ws.get_all_values()
category_progress, raw_expenses = [], []
col_var, col_prevu, col_actuel, row_var_start = -1, -1, -1, -1
for i, row in enumerate(all_rows):
    if i >= 65: break
    for j, cell in enumerate(row):
        if "charges variables" in str(cell).strip().lower():
            row_str = " ".join([str(x).lower() for x in row])
            if any(x in row_str for x in ["prévu", "actuel", "réel"]):
                col_var, row_var_start = j, i
                for k in range(j + 1, len(row)):
                    v = str(row[k]).strip().lower()
                    if "prévu" in v or "prevu" in v: col_prevu = k
                    elif any(x in v for x in ["actuel", "réel", "reel"]): col_actuel = k
                break
    if col_var != -1: break

if col_var != -1:
    for i in range(row_var_start + 1, min(row_var_start + 20, len(all_rows))):
        row = all_rows[i]
        cat = str(row[col_var]).strip()
        if "total" in cat.lower() or not cat: break
        elif cat and cat.lower() not in ["", "nan"]:
            if "vacance" not in cat.lower():
                category_progress.append({"name": cat, "prevu": parse_amount(row[col_prevu]), "reel": parse_amount(row[col_actuel])})

prevu_var, reel_var = sum(c["prevu"] for c in category_progress), sum(c["reel"] for c in category_progress)

row_history_start = -1
for i, row in enumerate(all_rows):
    if any(str(cell).strip().lower() == "date" for cell in row):
        row_history_start = i + 1
        break

if row_history_start != -1:
    for i in range(row_history_start, len(all_rows)):
        row = all_rows[i]
        if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
            if "total" in str(row[0]).lower(): continue
            amt_val = parse_amount(row[2])
            raw_expenses.append({"Date": row[0], "Merchant": row[1], "Amount": amt_val, "Category": row[4]})

# Extraction PLAGE EXACTA A100:B133 pour le Spending Trend
daily_summary_data = []
if len(all_rows) >= 99:
    # A100 = index 99, B133 = index 132
    trend_rows = all_rows[99:133] 
    for row in trend_rows:
        if len(row) >= 2:
            date_val = str(row[0]).strip()
            amt_val = parse_amount(row[1])
            if date_val and date_val.lower() != "date" and "total" not in date_val.lower() and "dépense" not in date_val.lower():
                daily_summary_data.append({"Date": date_val, "Amount": amt_val})

# --- TABS SYSTEM ---
tab_dashboard, tab_investments = st.tabs(["Dashboard", "Investments"])

with tab_dashboard:
    # --- DASHBOARD LOGIC ---
    restant = prevu_var - reel_var
    percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0
    insight_html = f"<div class='insight-banner insight-red'><i class='ph ph-warning'></i> Critical: {percent*100:.0f}% consumed</div>" if percent >= 0.80 else f"<div class='insight-banner insight-orange'><i class='ph ph-info'></i> Careful: {percent*100:.0f}% consumed</div>" if percent >= 0.66 else f"<div class='insight-banner insight-green'><i class='ph ph-check-circle'></i> On track</div>"

    st.markdown(f"""<div style="text-align: center; margin-bottom: 30px;"><div style="color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -1px; line-height: 1.2;">OVERVIEW</div><div style="color: #94A3B8; font-size: 20px; font-weight: 400; margin-top: 5px;">{selected_month_en} {now.year}</div></div>""", unsafe_allow_html=True)
    bar_color = 'linear-gradient(90deg, #9F1239, #E11D48)' if percent >= 0.8 else 'linear-gradient(90deg, #B45309, #F59E0B)' if percent >= 0.66 else 'linear-gradient(90deg, #059669, #10B981)'

    st.markdown(f"""<div class="hero-card"><div class="hero-top-metrics"><div><span>REMAINING</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(restant)} CHF</span></div><div><span>PLANNED</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(prevu_var)} CHF</span></div></div><div class="hero-main-value">{format_chf(reel_var)} <span style="font-size:24px; color:#60A5FA;">CHF</span></div><div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden;"><div style="background: {bar_color}; width: {percent*100}%; height: 100%; border-radius: 10px;"></div></div>{insight_html}</div>""", unsafe_allow_html=True)

    form_cat_map = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs", "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène"}
    
    with st.expander("➕ ADD NEW EXPENSE", expanded=False):
        with st.form("add_expense_form", clear_on_submit=True):
            lib = st.text_input("Merchant", placeholder="Apple, Migros...")
            amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f")
            cat_en = st.selectbox("Category", list(form_cat_map.keys()))
            note = st.text_input("Note")
            
            submitted = st.form_submit_button("CONFIRM TRANSACTION", use_container_width=True)
            if submitted:
                if lib and amt > 0:
                    col_b = ws.col_values(2); target = 60
                    for r in range(60, 150):
                        if r > len(col_b) or not str(col_b[r-1]).strip(): target = r; break
                    new_data = [[datetime.now().strftime("%d/%m/%Y"), lib, amt, note, form_cat_map[cat_en]]]
                    ws.update(values=new_data, range_name=f"A{target}:E{target}", value_input_option="USER_ENTERED")
                    
                    st.toast("Expenses added! ✅")
                    st.cache_resource.clear()
                    time.sleep(1.5)
                    st.rerun()

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<h3 style='font-size: 20px; margin-bottom: 20px;'>Category Breakdown</h3>", unsafe_allow_html=True)
        for cat in sorted(category_progress, key=lambda x: (x['reel'] > 0, x['prevu']), reverse=True): st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)
    with c2:
        st.markdown("<h3 style='font-size: 20px; margin-bottom: 20px;'>Recent Activity</h3>", unsafe_allow_html=True)
        if raw_expenses:
            with st.container(height=500, border=False):
                for exp in raw_expenses[::-1]: st.markdown(get_transaction_html(exp["Date"], exp["Merchant"], format_chf(exp["Amount"]) + " CHF", exp["Category"]), unsafe_allow_html=True)

    st.divider()
    
    st.markdown("<div class='chart-container'><h3 style='color:#FFF; font-size:22px; margin-bottom:15px;'><i class='ph ph-trend-up'></i> Spending Trend</h3>", unsafe_allow_html=True)
    
    fig = go.Figure()
    
    if daily_summary_data:
        df_trends = pd.DataFrame(daily_summary_data)
        curr_y = now.year
        # Nettoyage des points en slash pour forcer la lecture Jour/Mois/Année
        clean_dates = df_trends['Date'].astype(str).str.replace('.', '/')
        df_trends['DateObj'] = pd.to_datetime(clean_dates + '/' + str(curr_y), format='%d/%m/%Y', errors='coerce')
        df_trends = df_trends.dropna(subset=['DateObj']).sort_values('DateObj')
        
        if not df_trends.empty:
            # Setup base limits (for ideal line)
            curr_m = list(months_map.values()).index(selected_month) + 1
            start_d = datetime(curr_y, curr_m, 15)
            end_m = curr_m + 1 if curr_m < 12 else 1
            end_y = curr_y if curr_m < 12 else curr_y + 1
            end_d = datetime(end_y, end_m, 15)
            
            # Cumulative Spend
            df_trends['Cumulative'] = df_trends['Amount'].cumsum()
            
            # Dynamic Ideal Line mapping per row
            ideal_daily = prevu_var / 30 if prevu_var > 0 else 0
            df_trends['Days_Passed'] = (df_trends['DateObj'] - start_d).dt.days + 1
            df_trends['Days_Passed'] = df_trends['Days_Passed'].clip(lower=0) 
            df_trends['Ideal'] = df_trends['Days_Passed'] * ideal_daily
            
            # Split for Pro Green/Red Design (Correcting previous state)
            df_trends['Safe'] = df_trends.apply(lambda row: min(row['Cumulative'], row['Ideal']), axis=1)
            df_trends['Over'] = df_trends.apply(lambda row: max(row['Cumulative'] - row['Ideal'], 0), axis=1)
            
            # Cut off empty future dates
            last_valid_idx = df_trends[df_trends['Amount'] > 0].index.max()
            if pd.notna(last_valid_idx):
                df_plot = df_trends.loc[:last_valid_idx]
            else:
                df_plot = df_trends

            # 1. Background Ideal Line (Neutral Dark Blue/Grey)
            fig.add_trace(go.Scatter(x=[start_d, end_d], y=[0, prevu_var], mode='lines', name='Ideal Budget Limit', line=dict(color='#64748B', width=2, dash='dash')))
            
            # 2. Green Area (Safe Spend - Pro Emerald)
            fig.add_trace(go.Scatter(
                x=df_plot['DateObj'], 
                y=df_plot['Safe'], 
                mode='lines', 
                stackgroup='one',
                name='On Track', 
                line=dict(color='#10B981', width=0), 
                fillcolor='rgba(16, 185, 129, 0.3)' # Pro Emerald
            ))
            
            # 3. Red Area (Overbudget Spend - Pro Burgundy/Carmin)
            fig.add_trace(go.Scatter(
                x=df_plot['DateObj'], 
                y=df_plot['Over'], 
                mode='lines', 
                stackgroup='one',
                name='Overbudget', 
                line=dict(color='#E11D48', width=0), 
                fillcolor='rgba(225, 29, 72, 0.4)' # Pro Carmin
            ))
            
            # 4. Clean white top line for visual pop
            fig.add_trace(go.Scatter(
                x=df_plot['DateObj'], 
                y=df_plot['Cumulative'], 
                mode='lines', 
                name='Actual Spend', 
                line=dict(color='#F8FAFC', width=2), 
                showlegend=False
            ))
            
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=300, 
        margin=dict(t=10, b=10, l=10, r=10), 
        xaxis=dict(showgrid=False, color="#94A3B8"), 
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#94A3B8"), 
        showlegend=True, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='chart-container'><h3 style='color:#FFF; font-size:22px; margin-bottom:5px;'><i class='ph ph-chart-donut'></i> Distribution</h3>", unsafe_allow_html=True)
    if category_progress:
        labels = [c["name"] for c in category_progress if c["reel"] > 0]
        values = [c["reel"] for c in category_progress if c["reel"] > 0]
        if values:
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7, marker=dict(colors=['#3B82F6', '#60A5FA', '#93C5FD', '#1D4ED8', '#2563EB', '#1E3A8A']))])
            fig_pie.update_layout(
                showlegend=True, # LÉGENDES RENDUES VISIBLES
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                height=400, 
                margin=dict(t=0, b=0, l=0, r=0), 
                annotations=[dict(text=f"<b>{format_chf(reel_var)}</b><br>CHF", x=0.5, y=0.5, font_size=24, showarrow=False)],
                legend=dict(color="#F8FAFC", font=dict(color="#F8FAFC")) # Légende visible sur fond sombre
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

with tab_investments:
    st.markdown("<div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'><h2 style='font-size: 32px;'>📈 INVESTMENTS TRACKING</h2></div>", unsafe_allow_html=True)
    
    main_inv_container = st.container()
    
    st.write("<br>", unsafe_allow_html=True)
    show_amounts = st.checkbox("Show Real Amounts", value=False)
    
    with main_inv_container:
        try:
            ws_inv = sh.worksheet("Portfolio")
            all_inv_rows = ws_inv.get_all_values()
            
            header_row_idx = -1
            for i, row in enumerate(all_inv_rows):
                row_str_lower = " ".join([str(c).lower() for c in row])
                if "ticker" in row_str_lower or "isin" in row_str_lower:
                    header_row_idx = i
                    break
                    
            if header_row_idx != -1:
                headers = [str(h).strip() for h in all_inv_rows[header_row_idx]]
                data_rows = all_inv_rows[header_row_idx+1:]
                df_inv = pd.DataFrame(data_rows, columns=headers)
            else:
                df_inv = pd.DataFrame()
                
        except Exception as e:
            df_inv = pd.DataFrame()

        if not df_inv.empty and "Ticker / ISIN" in df_inv.columns:
            total_value = 0.0
            total_cost_basis = 0.0
            total_fees = 0.0
            cards_html = ""
            
            logo_col = next((col for col in df_inv.columns if "logo" in col.lower() or "image" in col.lower()), None)
            
            with st.spinner("Syncing live market data..."):
                for index, row in df_inv.iterrows():
                    ticker = str(row.get("Ticker / ISIN", "")).strip()
                    asset_name = str(row.get("Nom", ticker))
                    currency = str(row.get("Currency", "")).strip()
                    
                    qty_str = str(row.get("Units", "0")).replace(',', '.')
                    inv_str = str(row.get("Total Invested", "0")).replace(',', '.')
                    fees_str = str(row.get("Fees", "0")).replace(',', '.')
                    entry_price_str = str(row.get("Entry Price", row.get("Amount", "0"))).replace(',', '.')
                    
                    try: qty = float(qty_str)
                    except ValueError: qty = 0.0
                    
                    try: invested = float(inv_str)
                    except ValueError: invested = 0.0
                    
                    try: fees = float(fees_str)
                    except ValueError: fees = 0.0
                    
                    try: entry_price = float(entry_price_str)
                    except ValueError: entry_price = 0.0
                    
                    if ticker and qty > 0:
                        try:
                            # 1. Reliable Data Fetching
                            stock = yf.Ticker(ticker)
                            current_price = 0.0
                            
                            try:
                                current_price = float(stock.fast_info.get('last_price', 0.0))
                            except:
                                pass
                                
                            if current_price <= 0.0:
                                hist = stock.history(period="5d")
                                if not hist.empty:
                                    current_price = float(hist['Close'].iloc[-1])
                                    
                            if current_price <= 0.0:
                                continue # Skip strictly if asset price cannot be found anywhere
                            
                            # 2. Portfolio Calculations
                            value = current_price * qty
                            cost_basis = invested + fees
                            
                            total_value += value
                            total_cost_basis += cost_basis
                            total_fees += fees
                            pnl_chf = value - cost_basis
                            
                            if entry_price > 0:
                                unit_perf = ((current_price - entry_price) / entry_price) * 100
                            else:
                                unit_perf = 0.0
                                
                            unit_perf_class = "text-green" if unit_perf >= 0 else "text-red"
                            unit_perf_sign = "+" if unit_perf >= 0 else ""
                            
                            # 3. Handle custom user Logos or Fallback (CORRECTION ROBUSTE DES LOGOS)
                            raw_logo_url = str(row[logo_col]).strip() if logo_col else ""
                            custom_logo_url = convert_google_drive_link(raw_logo_url)
                            
                            # On ne génère le tag image QUE si le logo est détecté comme potentiellement valide
                            if is_valid_custom_logo(custom_logo_url):
                                img_tag = f'<img src="{custom_logo_url}" class="inv-logo" onerror="this.style.display=\'none\';">'
                            else:
                                # SINON: On n'affiche rien, et le fallback CSS (avatar) prendra le relais
                                img_tag = ''
                                
                            clean_fb_name = asset_name.replace("'", "").replace('"', '').replace(' ', '+')
                            fallback_url = f"https://ui-avatars.com/api/?name={clean_fb_name}&background=0F172A&color=60A5FA&rounded=true&bold=true"
                            
                            # Restauration du tag image avec fallback automatique
                            img_tag = f'<img src="{custom_logo_url if is_valid_custom_logo(custom_logo_url) else \'\'}" class="inv-logo" onerror="this.onerror=null; this.src=\'{fallback_url}\';">'
                            
                            curr_disp = f" {currency}" if currency else ""
                            ticker_display = f"{ticker} - {format_chf(current_price)}{curr_disp} - <span class='{unit_perf_class}'>{unit_perf_sign}{unit_perf:.2f}%</span>"
                            
                            if show_amounts:
                                qty_formatted = f"{qty:.6f}".rstrip('0').rstrip('.') if qty < 1 else f"{qty:.4f}".rstrip('0').rstrip('.')
                                qty_display = f" • {qty_formatted} Units"
                                
                                top_val = f"{format_chf(value)} CHF"
                                pnl_sign = "+" if pnl_chf >= 0 else ""
                                pnl_class = "text-green" if pnl_chf >= 0 else "text-red"
                                bottom_val = f"<span class='{pnl_class}'>P&L: {pnl_sign}{format_chf(pnl_chf)} CHF</span>"
                                
                                ticker_display += qty_display
                            else:
                                top_val = "*** CHF"
                                bottom_val = f"<span style='color: #94A3B8;'>P&L: *** CHF</span>"
                                
                            cards_html += f"""
                            <div class="inv-card">
                                <div class="inv-left">
                                    {img_tag}
                                    <div>
                                        <div class="inv-name">{asset_name}</div>
                                        <div class="inv-ticker">{ticker_display}</div>
                                    </div>
                                </div>
                                <div class="inv-right">
                                    <div class="inv-top-val">{top_val}</div>
                                    <div class="inv-bottom-val">{bottom_val}</div>
                                </div>
                            </div>
                            """
                            
                        except Exception:
                            pass
            
            perf_total = ((total_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
            perf_color = "#34D399" if perf_total >= 0 else "#FB7185"
            perf_sign = "+" if perf_total >= 0 else ""

            if show_amounts:
                main_metric_label = "TOTAL PORTFOLIO"
                main_metric_value = f"{format_chf(total_value)} <span style='font-size:24px; color:#60A5FA;'>CHF</span>"
                fees_label = f"Total Fees: {format_chf(total_fees)} CHF"
            else:
                main_metric_label = "TOTAL PORTFOLIO"
                main_metric_value = f"*** <span style='font-size:24px; color:#60A5FA;'>CHF</span>"
                fees_label = "Total Fees: *** CHF"
                
            sub_metric_html = f"<span style='color:{perf_color}; font-weight:700;'>{perf_sign}{perf_total:.2f}%</span><br><span style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>{fees_label}</span>"

            st.markdown(f"""<div class="hero-card"><div class="hero-top-metrics"><div><span>{main_metric_label}</span></div><div style="text-align: right;"><span>PERFORMANCE</span><br>{sub_metric_html}</div></div><div class="hero-main-value">{main_metric_value}</div></div>""", unsafe_allow_html=True)
            
            if cards_html:
                st.markdown(cards_html, unsafe_allow_html=True)

        else:
            st.markdown(f"""<div class="hero-card"><div class="hero-top-metrics"><div><span>TOTAL PORTFOLIO</span></div><div style="text-align: right;"><span>PERFORMANCE</span><br><span style="color:#34D399; font-weight:700;">+0.00%</span></div></div><div class="hero-main-value">0.00 <span style="font-size:24px; color:#60A5FA;">CHF</span></div></div>""", unsafe_allow_html=True)
            st.info("💡 The 'Portfolio' tab is missing or empty. Make sure columns 'Nom', 'Ticker / ISIN', 'Amount' (or 'Entry Price'), 'Units', 'Fees', and 'Total Invested' are present.")

st.sidebar.caption(f"Network Secure • Last sync: {datetime.now().strftime('%H:%M')}")
