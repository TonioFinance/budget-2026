import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

    .stTabs [data-baseweb="tab"]::before {
        font-family: "phosphor-regular" !important;
        font-size: 22px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:nth-child(1)::before { content: "\\e0da"; }
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
    .cat-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; width: 100%; }
    .cat-label { color: #FFFFFF !important; font-size: 16px !important; font-weight: 700; }
    .cat-amount { color: #FFFFFF !important; font-size: 15px; font-weight: 700; text-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }
    .cat-prevu-sub { color: #64748B; font-size: 13px; font-weight: 600; }
    .cat-sub-row { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 12px; font-weight: 700; }
    .cat-badge-ok { background: rgba(16, 185, 129, 0.12); color: #34D399; padding: 2px 8px; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.25); }
    .cat-badge-warn { background: rgba(245, 158, 11, 0.12); color: #FBBF24; padding: 2px 8px; border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.25); }
    .cat-badge-over { background: rgba(225, 29, 72, 0.15); color: #FB7185; padding: 2px 8px; border-radius: 8px; border: 1px solid rgba(225, 29, 72, 0.3); }

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

    /* --- INVESTMENT CARDS --- */
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

    /* --- NET WORTH SECTION --- */
    .networth-container {
        display: flex;
        gap: 12px;
        margin-top: 25px;
    }
    .nw-card {
        flex: 1;
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 15px;
        text-align: center;
    }
    .nw-title { font-size: 12px; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 5px;}
    .nw-value { font-size: 18px; font-weight: 900; }

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
        text-align: center;
    }
    
    /* Input & Number Styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }

       /* --- MONTH PICKER (dégradé bleu, identique au bouton) --- */
    /* Racine du select : porte le dégradé */
    [class*="st-key-header_month_picker"] [data-baseweb="select"] {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        border-radius: 16px !important;
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.2), inset 0 1px 2px rgba(255,255,255,0.2) !important;
        overflow: hidden !important;
    }
    /* Contrôle (premier enfant) : même dégradé + bordure */
    [class*="st-key-header_month_picker"] [data-baseweb="select"] > div {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 16px !important;
        min-height: 3.8rem !important;
    }
    /* Tout ce qui est à l'intérieur : transparent, texte blanc */
    [class*="st-key-header_month_picker"] [data-baseweb="select"] * {
        background: transparent !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
    }
    [class*="st-key-header_month_picker"] [data-baseweb="select"] svg {
        fill: #FFFFFF !important;
    }

    /* Liste déroulante assortie */
    div[data-baseweb="popover"] ul {
        background: #0F172A !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 14px !important;
    }
    div[data-baseweb="popover"] li { color: #FFFFFF !important; background: transparent !important; }
    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
    }

    /* --- BLUE GLOW BUTTON (CONFIRM / SYNC) --- */
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
        text-align: center;
    }
    
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    @media (max-width: 768px) {
        .hero-main-value { font-size: 42px !important; }
        .hero-card { padding: 25px 20px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; padding: 5px 10px; }
        .stTabs [data-baseweb="tab"] { padding: 0 15px !important; font-size: 13px !important; }
        .stExpander details summary { font-size: 14px !important; }
        .chart-container { padding: 15px 5px; } 
        .networth-container { flex-wrap: wrap; }
        .nw-card { flex-basis: 40%; }
    }
    </style>
""", unsafe_allow_html=True)

# --- FORMATTING HELPERS ---
def parse_amount(val):
    if not val or str(val).lower() in ["nan", "none", ""]: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

def format_chf(value):
    try:
        return f"{float(value):,.2f}".replace(",", "'")
    except ValueError:
        return "0.00"

def parse_trend_date(d_str, year, start_month=None):
    d_str = str(d_str).strip().replace('.', '/')
    if not d_str: return pd.NaT
    if '-' in d_str or d_str.count('/') == 2:
        return pd.to_datetime(d_str, dayfirst=True, errors='coerce')
    parts = d_str.split('/')
    if len(parts) == 2:
        inferred_year = year
        try:
            m_val = int(parts[1])
            if start_month == 12 and m_val == 1:
                inferred_year = year + 1
        except ValueError:
            pass
        return pd.to_datetime(f"{parts[0]}/{parts[1]}/{inferred_year}", format='%d/%m/%Y', errors='coerce')
    return pd.to_datetime(d_str, errors='coerce')

def get_progress_html(name, reel, prevu):
    if prevu > 0: percent = reel / prevu
    else: percent = 1.0 if reel > 0 else 0.0
    pct_str = f"{min(percent*100, 100):.1f}%"
    bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" if percent >= 1.0 else "linear-gradient(90deg, #B45309, #F59E0B)" if percent >= 0.66 else "linear-gradient(90deg, #059669, #10B981)" 
    cat_ui_map = {
        "Courses": ("Groceries", "ph-shopping-cart"),
        "Sorties/Restos": ("Dining", "ph-fork-knife"),
        "Transport": ("Transport", "ph-car"),
        "Loisirs": ("Leisure", "ph-game-controller"),
        "Imprévus": ("Unexpected", "ph-warning-circle"),
        "Shopping": ("Shopping", "ph-tote"),
        "Hygiène": ("Hygiene", "ph-drop"),
        "Hygiène/Entretien": ("Hygiene", "ph-drop")
    }
    ui_name, icon = cat_ui_map.get(name.strip(), (name, "ph-wallet"))
    
    diff = prevu - reel
    if prevu > 0:
        if diff >= 0:
            badge_cls = "cat-badge-warn" if percent >= 0.66 else "cat-badge-ok"
            badge_txt = f"{format_chf(diff)} CHF left"
        else:
            badge_cls = "cat-badge-over"
            badge_txt = f"+{format_chf(abs(diff))} CHF over"
        pct_label = f"{percent*100:.0f}% used"
    else:
        badge_cls = "cat-badge-over" if reel > 0 else "cat-badge-ok"
        badge_txt = "Unplanned" if reel > 0 else "0.00 CHF"
        pct_label = "No limit set"

    return f"""<div class="cat-card"><div class="cat-container"><div style="display:flex; align-items:center; gap:10px;"><i class="ph {icon}" style="font-size:22px; color:#60A5FA;"></i><span class="cat-label">{ui_name}</span></div><div><span class="cat-amount">{format_chf(reel)}</span> <span class="cat-prevu-sub">/ {format_chf(prevu)} CHF</span></div></div><div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden;"><div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div></div><div class="cat-sub-row"><span style="color:#64748B;">{pct_label}</span><span class="{badge_cls}">{badge_txt}</span></div></div>"""

def get_transaction_html(date, merchant, amount, category, note=""):
    cat_ui_map = {
        "Courses": ("Groceries", "ph-shopping-cart"),
        "Sorties/Restos": ("Dining", "ph-fork-knife"),
        "Transport": ("Transport", "ph-car"),
        "Loisirs": ("Leisure", "ph-game-controller"),
        "Imprévus": ("Unexpected", "ph-warning-circle"),
        "Shopping": ("Shopping", "ph-tote"),
        "Hygiène": ("Hygiene", "ph-drop"),
        "Hygiène/Entretien": ("Hygiene", "ph-drop")
    }
    ui_category, icon = cat_ui_map.get(category.strip(), (category, "ph-wallet"))
    note_str = f" • <span style='color:#94A3B8; font-style:italic;'>{note}</span>" if note and str(note).strip() else ""
    return f"""<div class="transaction-card"><div style="display:flex; align-items:center; gap:15px;"><div style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2); width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;"><i class="ph {icon}" style="font-size:20px; color:#60A5FA;"></i></div><div style="text-align: left;"><div style="color: #FFFFFF; font-weight: 700; font-size: 15px;">{merchant}</div><div style="color: #64748B; font-size: 12px; margin-top:2px;">{date} • {ui_category}{note_str}</div></div></div><div class="trans-amount">{amount}</div></div>"""

# --- CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets: return None
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception: return None

SHEET_ID = "1RIue5DT0RyOWlXTdMXYqRrffHogMOH8lkRyX_z-We_c"
client = get_gsheet_client()
if not client: st.stop()
try: sh = client.open_by_key(SHEET_ID)
except Exception: st.error("Access Denied"); st.stop()

# --- SMART CACHING FUNCTIONS (5 MINUTES TTL) ---
@st.cache_data(ttl=300, show_spinner=False)
def fetch_sheet_titles(sheet_id):
    _sh = get_gsheet_client().open_by_key(sheet_id)
    return [s.title for s in _sh.worksheets()]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_worksheet_data(sheet_id, worksheet_title):
    _sh = get_gsheet_client().open_by_key(sheet_id)
    _ws = _sh.worksheet(worksheet_title)
    return _ws.get_all_values()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_portfolio_data(sheet_id):
    _total_val = 0.0
    _total_cost = 0.0
    _total_fees = 0.0
    _enriched = []
    try:
        _sh = get_gsheet_client().open_by_key(sheet_id)
        ws_inv = _sh.worksheet("Portfolio")
        all_inv_rows = ws_inv.get_all_values()
        
        header_row_idx = -1
        for i, row in enumerate(all_inv_rows):
            row_str_lower = " ".join([str(c).lower() for c in row])
            if "ticker" in row_str_lower or "isin" in row_str_lower:
                header_row_idx = i
                break
                
        if header_row_idx != -1:
            headers = [str(h).strip() for h in all_inv_rows[header_row_idx]]
            df_inv = pd.DataFrame(all_inv_rows[header_row_idx+1:], columns=headers)
            
            for index, row in df_inv.iterrows():
                ticker = str(row.get("Ticker / ISIN", "")).strip()
                if not ticker or ticker.lower() in ["nan", "none"]:
                    continue
                    
                asset_name = str(row.get("Nom", ticker))
                currency = str(row.get("Currency", "")).strip()
                
                qty = parse_amount(row.get("Units", "0"))
                invested = parse_amount(row.get("Total Invested", "0"))
                fees = parse_amount(row.get("Fees", "0"))
                entry_price = parse_amount(row.get("Entry Price", row.get("Amount", "0")))
                
                if qty > 0:
                    try:
                        stock = yf.Ticker(ticker)
                        current_price = 0.0
                        try:
                            fast_price = stock.fast_info.get('last_price', 0.0)
                            if pd.notna(fast_price): current_price = float(fast_price)
                        except: pass
                        
                        if current_price <= 0.0 or pd.isna(current_price):
                            hist = stock.history(period="5d")
                            if not hist.empty:
                                hist_price = float(hist['Close'].iloc[-1])
                                if pd.notna(hist_price): current_price = hist_price
                                
                        if pd.isna(current_price): current_price = 0.0
                        
                        value = current_price * qty
                        cost_basis = invested + fees
                        
                        _total_val += value
                        _total_cost += cost_basis
                        _total_fees += fees
                        pnl_chf = value - cost_basis
                        
                        if entry_price > 0: unit_perf = ((current_price - entry_price) / entry_price) * 100
                        else: unit_perf = 0.0
                            
                        _enriched.append({
                            "asset_name": asset_name, "ticker": ticker, "currency": currency,
                            "qty": qty, "current_price": current_price, "value": value,
                            "entry_price": entry_price, "pnl_chf": pnl_chf, "unit_perf": unit_perf
                        })
                    except Exception:
                        pass
    except Exception:
        pass
    return _total_val, _total_cost, _total_fees, _enriched

# --- NAVIGATION & SESSION SYNC (CYCLE COMPTABLE DU 15 AU 15) ---
months_map = {"January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril", "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août", "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"}
months_list_en = list(months_map.keys())
now = datetime.now()

CYCLE_START_DAY = 15
if now.day < CYCLE_START_DAY:
    default_month_idx = now.month - 2
else:
    default_month_idx = now.month - 1

if default_month_idx < 0:
    default_month_idx = 11

if "active_month_en" not in st.session_state:
    st.session_state.active_month_en = months_list_en[default_month_idx]

# CALLBACK : Change le mois ET vide automatiquement le cache pour forcer la synchro des datas
def sync_on_month_change():
    st.session_state.active_month_en = st.session_state.header_month_picker
    st.session_state.sidebar_month_picker = st.session_state.header_month_picker
    st.cache_data.clear()

def sync_on_sidebar_change():
    st.session_state.active_month_en = st.session_state.sidebar_month_picker
    st.session_state.header_month_picker = st.session_state.sidebar_month_picker
    st.cache_data.clear()

selected_month_en = st.sidebar.selectbox(
    "Select Month",
    months_list_en,
    index=months_list_en.index(st.session_state.active_month_en),
    key="sidebar_month_picker",
    on_change=sync_on_sidebar_change
)
selected_month = months_map[st.session_state.active_month_en]

# Calcul des bornes exactes de la période comptable sélectionnée (15/M -> 15/M+1)
curr_m_num = list(months_map.values()).index(selected_month) + 1
curr_y_num = now.year - 1 if (now.month == 1 and now.day < CYCLE_START_DAY and curr_m_num == 12) else now.year
period_start_dt = datetime(curr_y_num, curr_m_num, CYCLE_START_DAY)
next_m_num = curr_m_num + 1 if curr_m_num < 12 else 1
next_y_num = curr_y_num if curr_m_num < 12 else curr_y_num + 1
period_end_dt = datetime(next_y_num, next_m_num, CYCLE_START_DAY)

available_titles = fetch_sheet_titles(SHEET_ID)
matched_title = next((s for s in available_titles if selected_month.lower() in s.lower()), None)
if not matched_title:
    matched_title = next((s for s in available_titles if s.lower() not in ["data", "portfolio", "investment", "old factures"]), available_titles[0])
    st.sidebar.warning(f"Onglet '{selected_month}' introuvable. Affichage de '{matched_title}'.")
ws = sh.worksheet(matched_title)

# --- DATA EXTRACTION (USING CACHED DATA) ---
all_rows = fetch_worksheet_data(SHEET_ID, matched_title)
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
    if len(row) > 1 and str(row[0]).strip().lower() == "date":
        row_str_lower = " ".join([str(c).lower() for c in row])
        if "lieu" in row_str_lower or "merchant" in row_str_lower:
            row_history_start = i + 1
            break

if row_history_start != -1:
    for i in range(row_history_start, min(row_history_start + 90, len(all_rows))):
        row = all_rows[i]
        if len(row) > 0 and str(row[0]).strip().lower() == "date": break 
        if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
            if "total" in str(row[0]).lower(): continue
            amt_val = parse_amount(row[2])
            raw_expenses.append({
                "Date": row[0],
                "Merchant": row[1],
                "Amount": amt_val,
                "Note": row[3] if len(row) > 3 else "",
                "Category": row[4],
                "sheet_row": i + 1
            })

daily_summary_data = []
if len(all_rows) > 149:
    trend_rows = all_rows[149:250]
    for row in trend_rows:
        if len(row) >= 2:
            date_val = str(row[0]).strip()
            amt_val = parse_amount(row[1])
            if date_val and date_val.lower() != "date" and "total" not in date_val.lower() and "dépense" not in date_val.lower() and "depense" not in date_val.lower():
                daily_summary_data.append({"Date": date_val, "Amount": amt_val})
elif raw_expenses:
    daily_summary_data = [{"Date": exp["Date"], "Amount": exp["Amount"]} for exp in raw_expenses]

total_portfolio_value, total_cost_basis, total_fees, enriched_portfolio_data = fetch_portfolio_data(SHEET_ID)

cash_remaining = 0.0
if len(all_rows) > 41 and len(all_rows[41]) > 9:
    cash_remaining = parse_amount(all_rows[41][9])
if cash_remaining == 0.0:
    cash_remaining = prevu_var - reel_var

emergency_fund = 0.0
if len(all_rows) > 9 and len(all_rows[9]) > 2:
    emergency_fund = parse_amount(all_rows[9][2])
for r in all_rows[:15]:
    if len(r) > 3 and "emergency fund" in str(r[0]).lower():
        val_reel_ef = parse_amount(r[3])
        val_prevu_ef = parse_amount(r[2])
        val_debut_ef = parse_amount(r[1])
        emergency_fund = val_reel_ef if val_reel_ef > 0 else (val_prevu_ef if val_prevu_ef > 0 else val_debut_ef)
        break

total_debts = 0.0
if len(all_rows) > 58 and len(all_rows[58]) > 9:
    total_debts = parse_amount(all_rows[58][9])
if total_debts == 0.0:
    try:
        data_rows = fetch_worksheet_data(SHEET_ID, "Data")
        for r in data_rows[3:7]:
            if len(r) > 1:
                total_debts += parse_amount(r[1])
    except Exception:
        pass

total_net_worth = cash_remaining + emergency_fund + total_portfolio_value - total_debts

# --- TABS SYSTEM ---
tab_dashboard, tab_investments = st.tabs(["Dashboard", "Investments"])

with tab_dashboard:
    restant = prevu_var - reel_var
    percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0
    insight_html = f"<div class='insight-banner insight-red'><i class='ph ph-warning'></i> Critical: {percent*100:.0f}% consumed</div>" if percent >= 0.80 else f"<div class='insight-banner insight-orange'><i class='ph ph-info'></i> Careful: {percent*100:.0f}% consumed</div>" if percent >= 0.66 else f"<div class='insight-banner insight-green'><i class='ph ph-check-circle'></i> On track</div>"

    period_badge = f"{period_start_dt.strftime('%d/%m/%Y')} → {period_end_dt.strftime('%d/%m/%Y')}"
    st.markdown(f"""<div style="text-align: center; margin-bottom: 15px;"><div style="color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -1px; line-height: 1.2;">OVERVIEW</div><div style="color: #94A3B8; font-size: 18px; font-weight: 400; margin-top: 5px;">{st.session_state.active_month_en} {curr_y_num} • <span style="color:#60A5FA; font-weight:700;">{matched_title}</span></div><div style="color: #64748B; font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-top: 4px; text-transform: uppercase;">Cycle: {period_badge}</div></div>""", unsafe_allow_html=True)

        # Sélecteur de mois : la synchro des données se fait automatiquement au changement (cf. sync_on_month_change)
    hdr_col1, hdr_col2, hdr_col3 = st.columns([1.2, 2.2, 1.2])
    with hdr_col2:
        st.selectbox(
            "Accounting Period",
            months_list_en,
            index=months_list_en.index(st.session_state.active_month_en),
            key="header_month_picker",
            on_change=sync_on_month_change,
            label_visibility="collapsed"
        )

    bar_color = 'linear-gradient(90deg, #9F1239, #E11D48)' if percent >= 0.8 else 'linear-gradient(90deg, #B45309, #F59E0B)' if percent >= 0.66 else 'linear-gradient(90deg, #059669, #10B981)'

    st.markdown(f"""<div class="hero-card"><div class="hero-top-metrics"><div><span>SPENT</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(reel_var)} CHF</span></div><div><span>PLANNED</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(prevu_var)} CHF</span></div></div><div class="hero-main-value">{format_chf(restant)} <span style="font-size:24px; color:#60A5FA;">CHF</span></div><div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden;"><div style="background: {bar_color}; width: {percent*100}%; height: 100%; border-radius: 10px;"></div></div>{insight_html}</div>""", unsafe_allow_html=True)

    form_cat_map = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs", "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène/Entretien"}
    
    with st.expander("ADD NEW EXPENSE", expanded=False):
        with st.form("add_expense_form", clear_on_submit=True):
            expense_date = st.date_input("Date", value=datetime.now())
            lib = st.text_input("Merchant", placeholder="Apple, Migros...")
            amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f", value=None)
            cat_en = st.selectbox("Category", list(form_cat_map.keys()))
            note = st.text_input("Note")
            
            submitted = st.form_submit_button("CONFIRM TRANSACTION", width='stretch')
            if submitted:
                if lib and amt is not None and amt > 0:
                    col_b = ws.col_values(2)
                    start_search_row = (row_history_start + 1) if row_history_start != -1 else 60
                    target = start_search_row
                    for r in range(start_search_row, 149):
                        if r > len(col_b) or not str(col_b[r-1]).strip(): target = r; break
                    
                    formatted_date = expense_date.strftime("%d/%m/%Y")
                    new_data = [[formatted_date, lib, amt, note, form_cat_map[cat_en]]]
                    ws.update(values=new_data, range_name=f"A{target}:E{target}", value_input_option="USER_ENTERED")
                    
                    st.toast("Expenses added! ✅")
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    time.sleep(1.0)
                    st.rerun()

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<h3 style='font-size: 20px; margin-bottom: 20px; text-align: center;'>Category Breakdown</h3>", unsafe_allow_html=True)
        for cat in sorted(category_progress, key=lambda x: (x['reel'] > 0, x['prevu']), reverse=True): st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)
    with c2:
        st.markdown("<h3 style='font-size: 20px; margin-bottom: 12px; text-align: center;'>Recent Activity</h3>", unsafe_allow_html=True)
        
        flt_col1, flt_col2 = st.columns([1.4, 1])
        with flt_col1:
            search_query = st.text_input("Search", placeholder="🔍 Filter merchant, note...", label_visibility="collapsed", key="act_search")
        with flt_col2:
            filter_cat_options = ["All"] + list(form_cat_map.keys())
            selected_filter_cat = st.selectbox("Filter Category", filter_cat_options, label_visibility="collapsed", key="act_cat_filter")

        if raw_expenses:
            filtered_expenses = raw_expenses[::-1]
            if selected_filter_cat != "All":
                target_fr_cat = form_cat_map[selected_filter_cat].lower()
                filtered_expenses = [
                    e for e in filtered_expenses
                    if target_fr_cat in str(e["Category"]).strip().lower() or str(e["Category"]).strip().lower() in target_fr_cat
                ]
            if search_query:
                q_low = search_query.strip().lower()
                filtered_expenses = [
                    e for e in filtered_expenses
                    if q_low in str(e["Merchant"]).lower()
                    or q_low in str(e.get("Note", "")).lower()
                    or q_low in str(e["Date"]).lower()
                    or q_low in str(e["Amount"]).lower()
                ]

            with st.container(height=420, border=False):
                if filtered_expenses:
                    for exp in filtered_expenses:
                        st.markdown(get_transaction_html(exp["Date"], exp["Merchant"], format_chf(exp["Amount"]) + " CHF", exp["Category"], exp.get("Note", "")), unsafe_allow_html=True)
                else:
                    st.caption("No matching transactions found.")

            last_exp = raw_expenses[-1]
            with st.expander(f"🗑️ Undo last entry ({last_exp['Merchant']} • {format_chf(last_exp['Amount'])} CHF)", expanded=False):
                st.caption(f"Row #{last_exp['sheet_row']} in '{matched_title}' ({last_exp['Date']})")
                if st.button("CONFIRM DELETE LAST ENTRY", key="btn_undo_last"):
                    row_idx = last_exp["sheet_row"]
                    ws.update(values=[["", "", "", "", ""]], range_name=f"A{row_idx}:E{row_idx}", value_input_option="USER_ENTERED")
                    st.toast("Last transaction removed! 🗑️")
                    st.cache_data.clear()
                    time.sleep(1.0)
                    st.rerun()
        else:
            st.caption("No transactions logged for this period yet.")

    st.divider()
    
    st.markdown("<div class='chart-container'><h3 style='color:#FFF; font-size:22px; margin-bottom:15px;'><i class='ph ph-trend-up'></i> Spending Trend</h3>", unsafe_allow_html=True)
    
    fig = go.Figure()
    
    if daily_summary_data:
        df_trends = pd.DataFrame(daily_summary_data)
        curr_y = curr_y_num
        curr_m = curr_m_num
        
        df_trends['DateObj'] = df_trends['Date'].apply(lambda x: parse_trend_date(x, curr_y, start_month=curr_m))
        df_trends = df_trends.dropna(subset=['DateObj']).sort_values('DateObj')
        df_trends = df_trends.groupby('DateObj', as_index=False)['Amount'].sum().sort_values('DateObj')
        
        if not df_trends.empty:
            start_d = period_start_dt
            end_d = period_end_dt
            period_days = max((end_d - start_d).days, 1)
            
            df_trends['Cumulative'] = df_trends['Amount'].cumsum()
            
            ideal_daily = prevu_var / period_days if prevu_var > 0 else 0
            df_trends['Days_Passed'] = (df_trends['DateObj'] - start_d).dt.days + 1
            df_trends['Days_Passed'] = df_trends['Days_Passed'].clip(lower=0, upper=period_days) 
            df_trends['Ideal'] = df_trends['Days_Passed'] * ideal_daily
            
            df_trends['Safe'] = df_trends.apply(lambda row: min(row['Cumulative'], row['Ideal']), axis=1)
            df_trends['Over'] = df_trends.apply(lambda row: max(row['Cumulative'] - row['Ideal'], 0), axis=1)
            
            last_valid_idx = df_trends[df_trends['Amount'] > 0].index.max()
            if pd.notna(last_valid_idx):
                df_plot = df_trends.loc[:last_valid_idx]
            else:
                df_plot = df_trends

            fig.add_trace(go.Scatter(x=[start_d, end_d], y=[0, prevu_var], mode='lines', name='Ideal Budget Limit (15 → 15)', line=dict(color='#64748B', width=2, dash='dash')))
            
            fig.add_trace(go.Scatter(
                x=df_plot['DateObj'], 
                y=df_plot['Safe'], 
                mode='lines', 
                stackgroup='one',
                name='On Track', 
                line=dict(color='#10B981', width=0), 
                fillcolor='rgba(16, 185, 129, 0.3)' 
            ))
            
            fig.add_trace(go.Scatter(
                x=df_plot['DateObj'], 
                y=df_plot['Over'], 
                mode='lines', 
                stackgroup='one',
                name='Overbudget', 
                line=dict(color='#E11D48', width=0), 
                fillcolor='rgba(225, 29, 72, 0.4)' 
            ))
            
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#F8FAFC"))
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='chart-container'><h3 style='color:#FFF; font-size:22px; margin-bottom:5px;'><i class='ph ph-chart-donut'></i> Distribution</h3>", unsafe_allow_html=True)
    if category_progress:
        labels = [c["name"] for c in category_progress if c["reel"] > 0]
        values = [c["reel"] for c in category_progress if c["reel"] > 0]
        if values:
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values, 
                hole=.75, 
                marker=dict(colors=['#3B82F6', '#60A5FA', '#93C5FD', '#1D4ED8', '#2563EB', '#1E3A8A']),
                textinfo='label+percent',
                textfont=dict(color='#FFFFFF', size=12),
                hoverinfo='label+value'
            )])
            fig_pie.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                height=350, 
                margin=dict(t=20, b=20, l=20, r=20), 
                annotations=[dict(text=f"<b>{format_chf(reel_var)}</b><br>CHF", x=0.5, y=0.5, font_size=24, showarrow=False, font=dict(color="#FFFFFF"))]
            )
            st.plotly_chart(fig_pie, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- NET WORTH SNAPSHOT RENDER ---
    st.markdown("<h3 style='font-size: 22px; color: #FFF; margin-top: 50px; margin-bottom: 20px; text-align: center;'><i class='ph ph-scales'></i> Net Worth Snapshot</h3>", unsafe_allow_html=True)
    
    nw_html = f"""<div class="hero-card" style="margin-bottom: 10px; border-color: rgba(16, 185, 129, 0.4); background: linear-gradient(160deg, rgba(16, 185, 129, 0.1) 0%, rgba(3, 7, 18, 0.8) 100%);">
<div class="hero-top-metrics" style="justify-content: center; margin-bottom: 15px;">
<span style="color:#34D399; letter-spacing: 2px;">TOTAL NET WORTH</span>
</div>
<div class="hero-main-value" style="color:#FFFFFF; margin-bottom: 30px;">
{format_chf(total_net_worth)} <span style="font-size:20px; color:#34D399;">CHF</span>
</div>
<div class="networth-container">
<div class="nw-card">
<div class="nw-title">Cash (Rem.)</div>
<div class="nw-value" style="color:#38BDF8;">{format_chf(cash_remaining)}</div>
</div>
<div class="nw-card">
<div class="nw-title">Emergency</div>
<div class="nw-value" style="color:#818CF8;">{format_chf(emergency_fund)}</div>
</div>
<div class="nw-card">
<div class="nw-title">Investments</div>
<div class="nw-value" style="color:#A78BFA;">{format_chf(total_portfolio_value)}</div>
</div>
<div class="nw-card">
<div class="nw-title">Debts</div>
<div class="nw-value" style="color:#FB7185;">{format_chf(total_debts)}</div>
</div>
</div>
</div>"""
    st.markdown(nw_html, unsafe_allow_html=True)

    # --- EVOLUTION TRACKER ---
    st.markdown("<div class='chart-container' style='margin-top: 15px;'><h3 style='color:#FFF; font-size:18px; margin-bottom:5px;'><i class='ph ph-chart-line-up'></i> Evolution Tracker</h3><p style='font-size: 12px; color: #64748B;'>Simulated data based on current net worth. Connect to a history tab later.</p>", unsafe_allow_html=True)
    
    mock_dates = [(now.replace(day=1) - timedelta(days=30 * i)).strftime('%b %Y') for i in range(5, -1, -1)]
    mock_values = [total_net_worth * 0.75, total_net_worth * 0.78, total_net_worth * 0.85, total_net_worth * 0.82, total_net_worth * 0.93, total_net_worth]
    
    fig_nw = go.Figure()
    fig_nw.add_trace(go.Scatter(
        x=mock_dates, 
        y=mock_values, 
        mode='lines+markers',
        name='Net Worth',
        line=dict(color='#34D399', width=3, shape='spline'),
        marker=dict(size=8, color='#FFFFFF', line=dict(width=2, color='#34D399')),
        fill='tozeroy',
        fillcolor='rgba(52, 211, 153, 0.1)'
    ))
    
    fig_nw.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=250, 
        margin=dict(t=10, b=10, l=10, r=10), 
        xaxis=dict(showgrid=False, color="#94A3B8"), 
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#94A3B8", tickprefix="CHF "), 
        showlegend=False
    )
    st.plotly_chart(fig_nw, width='stretch', config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)


with tab_investments:
    st.markdown("<div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'><h2 style='font-size: 32px;'>📈 PORTFOLIO TRACKING</h2></div>", unsafe_allow_html=True)
    
    main_inv_container = st.container()
    
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        show_amounts = st.checkbox("Show Real Amounts", value=False)
    
    with main_inv_container:
        cards_html = ""
        if enriched_portfolio_data:
            for item in enriched_portfolio_data:
                unit_perf_class = "text-green" if item['unit_perf'] >= 0 else "text-red"
                unit_perf_sign = "+" if item['unit_perf'] >= 0 else ""
                
                clean_fb_name = item['asset_name'].replace("'", "").replace('"', '').replace(' ', '+')
                logo_url = f"https://ui-avatars.com/api/?name={clean_fb_name}&background=0F172A&color=60A5FA&rounded=true&bold=true&font-size=0.4"
                img_tag = f'<img src="{logo_url}" class="inv-logo">'
                
                curr_disp = f" {item['currency']}" if item['currency'] else ""
                
                if show_amounts:
                    qty_formatted = f"{item['qty']:.6f}".rstrip('0').rstrip('.') if item['qty'] < 1 else f"{item['qty']:.4f}".rstrip('0').rstrip('.')
                    price_display = f"{format_chf(item['value'])} CHF"
                    pnl_sign = "+" if item['pnl_chf'] >= 0 else ""
                    perf_display = f"{unit_perf_sign}{item['unit_perf']:.2f}%<br>{pnl_sign}{format_chf(item['pnl_chf'])} CHF"
                    ticker_display = f"{item['ticker']} • {qty_formatted} Units"
                else:
                    if item['current_price'] > 0:
                        price_display = f"{format_chf(item['current_price'])}{curr_disp}"
                    else:
                        price_display = "Market Down"
                    perf_display = f"{unit_perf_sign}{item['unit_perf']:.2f}%"
                    ticker_display = f"{item['ticker']}"

                cards_html += f"""<div class="inv-card">
<div class="inv-left">
{img_tag}
<div style="text-align: left;">
<div class="inv-name">{item['asset_name']}</div>
<div class="inv-ticker">{ticker_display}</div>
</div>
</div>
<div class="inv-right">
<div class="inv-top-val">{price_display}</div>
<div class="inv-bottom-val" style="margin-top: 4px;"><span class='{unit_perf_class}'>{perf_display}</span></div>
</div>
</div>"""
                
        perf_total = ((total_portfolio_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
        perf_color = "#34D399" if perf_total >= 0 else "#FB7185"
        perf_sign = "+" if perf_total >= 0 else ""

        if show_amounts:
            main_metric_label = "TOTAL PORTFOLIO"
            main_metric_value = f"{format_chf(total_portfolio_value)} <span style='font-size:24px; color:#60A5FA;'>CHF</span>"
            fees_label = f"Total Fees: {format_chf(total_fees)} CHF"
        else:
            main_metric_label = "TOTAL PORTFOLIO"
            main_metric_value = f"*** <span style='font-size:24px; color:#60A5FA;'>CHF</span>"
            fees_label = "Total Fees: *** CHF"
            
        sub_metric_html = f"<span style='color:{perf_color}; font-weight:700;'>{perf_sign}{perf_total:.2f}%</span><br><span style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>{fees_label}</span>"

        st.markdown(f"""<div class="hero-card"><div class="hero-top-metrics"><div><span>{main_metric_label}</span></div><div style="text-align: right;"><span>PERFORMANCE</span><br>{sub_metric_html}</div></div><div class="hero-main-value">{main_metric_value}</div></div>""", unsafe_allow_html=True)
        
        if cards_html:
            st.markdown(cards_html, unsafe_allow_html=True)
        elif not enriched_portfolio_data:
            st.info("💡 The 'Portfolio' tab is missing or empty. Make sure columns 'Nom', 'Ticker / ISIN', 'Amount' (or 'Entry Price'), 'Units', 'Fees', and 'Total Invested' are present.")

st.sidebar.caption(f"Network Secure • Last sync: {datetime.now().strftime('%H:%M')}")
