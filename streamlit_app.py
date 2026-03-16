import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & AZURE (SAAS EDITION) ---
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
        cursor: pointer;
    }
    .transaction-card:hover {
        transform: translateX(6px) scale(1.01);
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
    }
    .trans-amount { color: #FFFFFF !important; font-weight: 800; font-size: 15px; }

    /* --- BLUE GLOW BUTTON --- */
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 16px !important;
        height: 3.8rem !important;
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.2), inset 0 1px 2px rgba(255,255,255,0.2) !important;
        margin-bottom: 30px !important;
        transition: all 0.2s ease-out !important;
    }
    div[data-testid="stButton"] > button p {
        color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 16px !important;
        letter-spacing: 1.5px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5) !important;
        margin: 0 !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(90deg, #2563EB 0%, #3B82F6 100%) !important; 
        border-color: rgba(96, 165, 250, 0.6) !important;
        box-shadow: 0 0 8px rgba(96, 165, 250, 0.3), 0 6px 15px rgba(37, 99, 235, 0.2) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }
    
    /* --- GLASS FORM & DIALOG --- */
    div[data-testid="stDialog"] > div {
        background: linear-gradient(160deg, rgba(30, 58, 138, 0.9) 0%, rgba(3, 7, 18, 0.95) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.4) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(20px) !important;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* Donut Chart Glass Container */
    .chart-container {
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 24px;
        padding: 20px;
        margin-top: 20px;
    }

    /* --- MOBILE RESPONSIVENESS --- */
    @media (max-width: 768px) {
        .hero-card { padding: 25px 15px; } 
        .hero-top-metrics { font-size: 11px; letter-spacing: 0.5px; }
        .hero-top-metrics > div { 
            display: flex; 
            flex-direction: column; 
            gap: 4px; 
            text-align: center;
        }
        .hero-main-value { font-size: 42px; }
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
    if percent >= 0.80: bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" 
    elif percent >= 0.50: bar_color = "linear-gradient(90deg, #B45309, #F59E0B)" 
    else: bar_color = "linear-gradient(90deg, #059669, #10B981)" 
    
    cat_ui_map = {"Courses": ("Groceries", "ph-shopping-cart"), "Sorties/Restos": ("Dining", "ph-fork-knife"), "Transport": ("Transport", "ph-car"), "Loisirs": ("Leisure", "ph-game-controller"), "Imprévus": ("Unexpected", "ph-warning-circle"), "Shopping": ("Shopping", "ph-tote"), "Hygiène": ("Hygiene", "ph-drop")}
    ui_name, icon = cat_ui_map.get(name.strip(), (name, "ph-wallet"))

    return f"""
<div class="cat-card">
    <div class="cat-container">
        <div style="display:flex; align-items:center; gap:10px;">
            <i class="ph {icon}" style="font-size:22px; color:#60A5FA;"></i>
            <span class="cat-label">{ui_name}</span>
        </div>
        <span class="cat-amount">{format_chf(reel)} CHF</span>
    </div>
    <div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden;">
        <div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 10px;"></div>
    </div>
</div>"""

def get_transaction_html(date, merchant, amount, category):
    cat_ui_map = {"Courses": ("Groceries", "ph-shopping-cart"), "Sorties/Restos": ("Dining", "ph-fork-knife"), "Transport": ("Transport", "ph-car"), "Loisirs": ("Leisure", "ph-game-controller"), "Imprévus": ("Unexpected", "ph-warning-circle"), "Shopping": ("Shopping", "ph-tote"), "Hygiène": ("Hygiene", "ph-drop")}
    ui_category, icon = cat_ui_map.get(category.strip(), (category, "ph-wallet"))
    return f"""
<div class="transaction-card">
    <div style="display:flex; align-items:center; gap:15px;">
        <div style="background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.2); width:40px; height:40px; border-radius:12px; display:flex; align-items:center; justify-content:center;">
            <i class="ph {icon}" style="font-size:20px; color:#60A5FA;"></i>
        </div>
        <div>
            <div style="color: #FFFFFF; font-weight: 700; font-size: 15px;">{merchant}</div>
            <div style="color: #64748B; font-size: 12px;">{date} • {ui_category}</div>
        </div>
    </div>
    <div class="trans-amount">{amount}</div>
</div>"""

# --- CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets: return None
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"
client = get_gsheet_client()
if not client: st.stop()
sh = client.open_by_key(SHEET_ID)

# --- NAVIGATION ---
months_map = {"January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril", "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août", "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"}
selected_month_en = st.sidebar.selectbox("Select Month", list(months_map.keys()), index=datetime.now().month - 1)
selected_month = months_map[selected_month_en]
ws = sh.worksheet(next((s for s in [s.title for s in sh.worksheets()] if selected_month.lower() in s.lower()), sh.worksheets()[0].title))

# --- DATA EXTRACTION ---
all_rows = ws.get_all_values()
category_progress = []
expenses_list = []
col_var, col_prevu, col_actuel, row_var_start = -1, -1, -1, -1

for i, row in enumerate(all_rows):
    if "charges variables" in str(row).lower():
        col_var, row_var_start = 0, i
        for j, cell in enumerate(row):
            if "prévu" in str(cell).lower(): col_prevu = j
            if "actuel" in str(cell).lower() or "réel" in str(cell).lower(): col_actuel = j
        break

if col_var != -1:
    for i in range(row_var_start + 1, len(all_rows)):
        row = all_rows[i]
        cat = str(row[col_var]).strip()
        if "total" in cat.lower() or not cat: break
        if "vacance" not in cat.lower():
            p_val = parse_amount(row[col_prevu]) if len(row) > col_prevu else 0.0
            r_val = parse_amount(row[col_actuel]) if len(row) > col_actuel else 0.0
            category_progress.append({"name": cat, "prevu": p_val, "reel": r_val})

prevu_var = sum(c["prevu"] for c in category_progress)
reel_var = sum(c["reel"] for c in category_progress)
restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# History
for i, row in enumerate(all_rows):
    if len(row) > 0 and str(row[0]).strip().lower() == "date":
        for r in all_rows[i+1:]:
            if len(r) > 4 and r[0] and "total" not in str(r[0]).lower():
                expenses_list.append({"Date": r[0], "Marchand": r[1], "Montant": format_chf(parse_amount(r[2])) + " CHF", "Catégorie": r[4]})
        break

# --- UI DASHBOARD ---
st.markdown(f"""<div style="text-align: center; margin-bottom: 30px;">
    <div style="color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -1px;">Dashboard</div>
    <div style="color: #94A3B8; font-size: 20px; font-weight: 400;">{selected_month_en} {datetime.now().year}</div>
</div>""", unsafe_allow_html=True)

bar_color = 'linear-gradient(90deg, #059669, #10B981)'
if percent >= 0.8: bar_color = 'linear-gradient(90deg, #9F1239, #E11D48)'
elif percent >= 0.5: bar_color = 'linear-gradient(90deg, #B45309, #F59E0B)'

insight_html = "<div class='insight-banner insight-green'><i class='ph ph-check-circle'></i> Finances are on track</div>"
if percent >= 0.8: insight_html = f"<div class='insight-banner insight-red'><i class='ph ph-warning'></i> Critical: {percent*100:.0f}% used</div>"

hero_html = f"""
<div class="hero-card">
    <div class="hero-top-metrics">
        <div><span>REMAINING</span> <span style="color:#FFFFFF; font-size: 14px;">{format_chf(restant)}&nbsp;CHF</span></div>
        <div><span>PLANNED</span> <span style="color:#FFFFFF; font-size: 14px;">{format_chf(prevu_var)}&nbsp;CHF</span></div>
    </div>
    <div class="hero-main-value">{format_chf(reel_var)} <span style="font-size:24px; color:#60A5FA;">CHF</span></div>
    <div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden;">
        <div style="background: {bar_color}; width: {percent*100}%; height: 100%; border-radius: 10px;"></div>
    </div>
    {insight_html}
</div>"""
st.markdown(hero_html, unsafe_allow_html=True)

@st.dialog("Add New Transaction")
def add_transaction_modal():
    lib = st.text_input("Merchant", placeholder="Apple, Migros...")
    amt = st.number_input("Amount (CHF)", min_value=0.0, format="%.2f")
    cat_en = st.selectbox("Category", ["Groceries", "Dining", "Transport", "Leisure", "Unexpected", "Shopping", "Hygiene"])
    if st.button("CONFIRM EXPENSE", use_container_width=True):
        if lib and amt > 0:
            target = len(ws.col_values(2)) + 1
            ws.update(values=[[datetime.now().strftime("%Y-%m-%d"), lib, amt, "", cat_en]], range_name=f"A{target}:E{target}")
            st.rerun()

if st.button("+ ADD NEW EXPENSE", use_container_width=True): add_transaction_modal()

# --- LAYOUT CATEGORIES & HISTORY ---
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("### <i class='ph ph-list-dashes'></i> Category Breakdown", unsafe_allow_html=True)
    with st.container(height=480, border=False):
        for cat in sorted(category_progress, key=lambda x: x['reel'], reverse=True):
            st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)

with col2:
    st.markdown("### <i class='ph ph-clock-counter-clockwise'></i> Recent Activity", unsafe_allow_html=True)
    with st.container(height=480, border=False):
        for exp in expenses_list[::-1]:
            st.markdown(get_transaction_html(exp["Date"], exp["Marchand"], exp["Montant"], exp["Catégorie"]), unsafe_allow_html=True)

# --- CHART ---
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
labels = [c["name"] for c in category_progress if c["reel"] > 0]
values = [c["reel"] for c in category_progress if c["reel"] > 0]
if values:
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7, marker=dict(colors=['#3B82F6','#60A5FA','#93C5FD','#1D4ED8'], line=dict(color='#030712', width=5)))])
    fig.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(t=0, b=0),
                      annotations=[dict(text=f"<b>{format_chf(reel_var)}</b><br>CHF", x=0.5, y=0.5, font_size=24, showarrow=False)])
    st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
