import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026 Pro", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & AZURE (SAAS PREMIUM EDITION) ---
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
    
    /* --- CUSTOM TABS NAVIGATION --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 10px 15px;
        border-radius: 20px;
        border: 1px solid rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(10px);
        margin-bottom: 30px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border-radius: 12px !important;
        color: #94A3B8 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0 25px !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(37, 99, 235, 0.2) !important;
        color: #60A5FA !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
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
    .cat-label { color: #FFFFFF !important; font-size: 18px !important; font-weight: 700; }
    .cat-amount { color: #FFFFFF !important; font-size: 17px; font-weight: 700; text-shadow: 0 0 10px rgba(59, 130, 246, 0.3); }

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
        transform: translateX(8px) scale(1.01);
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .trans-amount { color: #FFFFFF !important; font-weight: 800; font-size: 16px; }

    /* --- EXPANDER (FULL WIDTH ADD EXPENSE) --- */
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
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* --- SCANNER STYLE --- */
    .scanner-zone {
        border: 2px dashed rgba(59, 130, 246, 0.4);
        border-radius: 28px;
        padding: 60px 20px;
        text-align: center;
        background: rgba(15, 23, 42, 0.2);
        margin-bottom: 25px;
    }

    /* Chart Glass Containers */
    .chart-container {
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 24px;
        padding: 20px;
        margin-top: 20px;
    }

    /* --- BUTTONS --- */
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.5) !important;
        border-radius: 16px !important;
        height: 3.5rem !important;
        box-shadow: 0 6px 15px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div { border-radius: 10px; height: 12px !important; }
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
    
    # Logic: Green -> Orange (2/3) -> Red (100%)
    if percent >= 1.0: bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" 
    elif percent >= 0.66: bar_color = "linear-gradient(90deg, #B45309, #F59E0B)" 
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
    <div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 12px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden;">
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
            <div style="color: #64748B; font-size: 12px; margin-top:2px;">{date} • {ui_category}</div>
        </div>
    </div>
    <div class="trans-amount">{amount}</div>
</div>"""

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
category_progress = []
raw_expenses = []

# FIND CHARGES VARIABLES
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

prevu_var = sum(c["prevu"] for c in category_progress)
reel_var = sum(c["reel"] for c in category_progress)

# HISTORY SCAN (Detect "Date" header)
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

# --- TABS SYSTEM ---
tab_dashboard, tab_scanner = st.tabs(["📊 DASHBOARD", "📸 RECEIPT SCANNER"])

with tab_dashboard:
    restant = prevu_var - reel_var
    percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

    # Insight Logic
    if percent >= 0.80: insight_html = f"<div class='insight-banner insight-red'><i class='ph ph-warning'></i> Critical: {percent*100:.0f}% consumed</div>"
    elif percent >= 0.66: insight_html = f"<div class='insight-banner insight-orange'><i class='ph ph-info'></i> Careful: {percent*100:.0f}% consumed</div>"
    else: insight_html = f"<div class='insight-banner insight-green'><i class='ph ph-check-circle'></i> Finances on track</div>"

    # Hero Card
    bar_color = 'linear-gradient(90deg, #059669, #10B981)'
    if percent >= 0.8: bar_color = 'linear-gradient(90deg, #9F1239, #E11D48)'
    elif percent >= 0.66: bar_color = 'linear-gradient(90deg, #B45309, #F59E0B)'

    st.markdown(f"""
    <div class="hero-card">
        <div class="hero-top-metrics">
            <div><span>REMAINING</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(restant)} CHF</span></div>
            <div><span>PLANNED</span> <span style="color:#FFFFFF; font-weight:700;">{format_chf(prevu_var)} CHF</span></div>
        </div>
        <div class="hero-main-value">{format_chf(reel_var)} <span style="font-size:24px; color:#60A5FA;">CHF</span></div>
        <div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 12px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden;">
            <div style="background: {bar_color}; width: {percent*100}%; height: 100%; border-radius: 10px;"></div>
        </div>
        {insight_html}
    </div>""", unsafe_allow_html=True)

    # ADD EXPENSE
    form_cat_map = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs", "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène"}
    with st.expander("ADD NEW EXPENSE", expanded=False):
        lib = st.text_input("Merchant", placeholder="Apple, Migros...")
        amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f")
        cat_en = st.selectbox("Category", list(form_cat_map.keys()))
        note = st.text_input("Note")
        if st.button("CONFIRM TRANSACTION", use_container_width=True):
            if lib and amt > 0:
                col_b = ws.col_values(2)
                target = 60
                for r in range(60, 150):
                    if r > len(col_b) or not str(col_b[r-1]).strip():
                        target = r
                        break
                new_data = [[datetime.now().strftime("%d/%m/%Y"), lib, amt, note, form_cat_map[cat_en]]]
                ws.update(values=new_data, range_name=f"A{target}:E{target}", value_input_option="USER_ENTERED")
                st.cache_resource.clear()
                st.rerun()

    # LAYOUT
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("<h3 style='font-size: 18px;'>Categories</h3>", unsafe_allow_html=True)
        sorted_cats = sorted(category_progress, key=lambda x: (x['reel'] > 0, x['prevu']), reverse=True)
        for cat in sorted_cats:
            st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)
    with c2:
        st.markdown("<h3 style='font-size: 18px;'>Activity</h3>", unsafe_allow_html=True)
        if raw_expenses:
            with st.container(height=450, border=False):
                for exp in raw_expenses[::-1]:
                    st.markdown(get_transaction_html(exp["Date"], exp["Merchant"], format_chf(exp["Amount"]) + " CHF", exp["Category"]), unsafe_allow_html=True)

    st.divider()

    # --- TREND CHART ---
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #FFFFFF; font-size: 22px; text-align: center; margin-bottom: 15px;'><i class='ph ph-trend-up'></i> Spending Trend</h3>", unsafe_allow_html=True)
    if raw_expenses:
        df_trends = pd.DataFrame(raw_expenses)
        df_trends['Date'] = pd.to_datetime(df_trends['Date'], dayfirst=True, errors='coerce')
        df_trends = df_trends.dropna(subset=['Date'])
        if not df_trends.empty:
            daily = df_trends.groupby('Date')['Amount'].sum().reset_index().sort_values('Date')
            daily['Cumulative'] = daily['Amount'].cumsum()
            fig = go.Figure(go.Scatter(x=daily['Date'], y=daily['Cumulative'], mode='lines', fill='tozeroy', line=dict(color='#60A5FA', width=4), fillcolor='rgba(96, 165, 250, 0.1)'))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=10, b=10, l=10, r=10), xaxis=dict(showgrid=False, color="#94A3B8"), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#94A3B8"))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- DONUT CHART ---
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #FFFFFF; font-size: 22px; text-align: center; margin-bottom: 5px;'><i class='ph ph-chart-donut'></i> Distribution</h3>", unsafe_allow_html=True)
    if category_progress:
        labels = [c["name"] for c in category_progress if c["reel"] > 0]
        values = [c["reel"] for c in category_progress if c["reel"] > 0]
        if values:
            azure_colors = ['#3B82F6', '#60A5FA', '#93C5FD', '#1D4ED8', '#2563EB', '#1E3A8A']
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.7, marker=dict(colors=azure_colors))])
            fig_pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(t=0, b=0, l=0, r=0), annotations=[dict(text=f"<b>{format_chf(reel_var)}</b><br>CHF", x=0.5, y=0.5, font_size=24, showarrow=False)])
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    st.markdown("</div>", unsafe_allow_html=True)

with tab_scanner:
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h2><i class='ph ph-camera-plus'></i> AI Receipt Scanner</h2>", unsafe_allow_html=True)
    st.markdown('<div class="scanner-zone">', unsafe_allow_html=True)
    up_file = st.file_uploader("Drop receipt here", type=["jpg", "png", "pdf"], label_visibility="collapsed")
    if not up_file:
        st.markdown('<i class="ph ph-scan" style="font-size: 80px; color: rgba(59,130,246,0.3);"></i>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    if up_file:
        st.info("Analysis in progress...")
        cs1, cs2 = st.columns(2)
        with cs1:
            st.text_input("Merchant", value="Detected Store")
            st.number_input("Amount", value=0.0)
        with cs2:
            st.selectbox("Category", list(form_cat_map.keys()), index=0)
            st.write("<br>", unsafe_allow_html=True)
            if st.button("SAVE DATA", use_container_width=True):
                st.success("Added!")
    st.markdown("</div>", unsafe_allow_html=True)

st.sidebar.caption(f"Last sync: {datetime.now().strftime('%H:%M')}")
