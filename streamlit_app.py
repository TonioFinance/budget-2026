import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & AZURE WITH DYNAMIC GLOW (LATO FONT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');

    .stApp { 
        background-color: #030712;
        background-image: radial-gradient(circle at 50% -20%, #172554 0%, #030712 85%);
        color: #F8FAFC; 
        font-family: 'Lato', sans-serif;
    }

    /* --- ULTRA-FAST HOVER ANIMATION (0.15s) --- */
    * { transition: all 0.15s ease-out; }

    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    
    /* Metrics Top (Blue Glow effect) */
    div[data-testid="stMetricValue"] { 
        font-family: 'Lato', sans-serif;
        font-size: 40px !important; 
        font-weight: 900 !important;
        color: #FFFFFF !important; 
        text-shadow: 0 0 10px rgba(255,255,255,0.2), 0 0 30px rgba(59, 130, 246, 0.3); 
    }
    
    div[data-testid="stMetricLabel"] { 
        font-weight: 700;
        color: #60A5FA !important; /* Azure Label */
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        font-size: 11px;
    }
    
    .stMetric { 
        background: rgba(15, 23, 42, 0.4) !important; 
        backdrop-filter: blur(15px);
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.05) !important; 
        border-top: 1.5px solid rgba(59, 130, 246, 0.4) !important;
        padding: 15px 20px !important;
    }
    
    .stMetric:hover {
        transform: translateY(-3px);
        border-top: 1.5px solid rgba(59, 130, 246, 0.8) !important;
        background: rgba(15, 23, 42, 0.6) !important;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
    }

    /* PROGRESS BARS */
    .stProgress > div > div > div > div { 
        border-radius: 10px;
        height: 14px !important;
    }

    /* --- CATEGORY CARD SYSTEM --- */
    .cat-card {
        background: rgba(255,255,255,0.02);
        padding: 14px 20px;
        border-radius: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.03);
        cursor: pointer;
    }
    .cat-card:hover {
        background: rgba(59, 130, 246, 0.08);
        transform: scale(1.02);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .cat-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        width: 100%;
    }
    
    .cat-label {
        color: #FFFFFF !important;
        font-size: 18px !important;
        font-weight: 700;
    }
    
    .cat-amount {
        color: #FFFFFF !important;
        font-size: 16px;
        font-weight: 700;
        text-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
    }

    /* --- RECENT ACTIVITY (TRANSACTION CARDS WITH BLUE GLOW) --- */
    .transaction-card {
        background: rgba(15, 23, 42, 0.4); 
        border-radius: 18px; 
        padding: 15px 20px; 
        margin-bottom: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        border: 1px solid rgba(255,255,255,0.02);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.05);
        cursor: pointer;
    }
    .transaction-card:hover {
        transform: translateX(6px) scale(1.01);
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.4);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    
    .trans-amount {
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 16px;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }

    /* Form Design */
    div[data-testid="stForm"] { 
        background: rgba(15, 23, 42, 0.3) !important;
        padding: 25px; border-radius: 25px; 
        border: 1px solid rgba(59, 130, 246, 0.15) !important; 
    }
    
    input, select { font-family: 'Lato', sans-serif !important; }
    
    /* Blue Button */
    .stButton>button {
        background: linear-gradient(90deg, #1D4ED8 0%, #3B82F6 100%);
        color: white !important;
        border-radius: 12px;
        font-weight: 700;
        border: none;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

def get_progress_html(name, reel, prevu):
    if prevu > 0: percent = reel / prevu
    else: percent = 1.0 if reel > 0 else 0.0
    pct_str = f"{min(percent*100, 100):.1f}%"
    
    # Logic: Blue -> Orange (66%) -> Red (100%)
    if percent >= 1.0: 
        bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" 
    elif percent >= 0.66: 
        bar_color = "linear-gradient(90deg, #B45309, #F59E0B)"
    else: 
        bar_color = "linear-gradient(90deg, #1D4ED8, #3B82F6)" 
    
    cat_ui_map = {"Courses": "Groceries", "Sorties/Restos": "Dining", "Transport": "Transport", "Loisirs": "Leisure", "Imprévus": "Unexpected", "Shopping": "Shopping", "Hygiène": "Hygiene"}
    ui_name = cat_ui_map.get(name.strip(), name)

    return f"""
    <div class="cat-card">
        <div class="cat-container">
            <span class="cat-label">{ui_name}</span>
            <span class="cat-amount">{reel:.0f} / {prevu:.0f} CHF</span>
        </div>
        <div style="background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 14px; border: 1px solid rgba(255,255,255,0.03); overflow: hidden;">
            <div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
        </div>
    </div>
    """

def get_transaction_html(date, merchant, amount, category):
    cat_ui_map = {"Courses": "Groceries", "Sorties/Restos": "Dining", "Transport": "Transport", "Loisirs": "Leisure", "Imprévus": "Unexpected", "Shopping": "Shopping", "Hygiène": "Hygiene"}
    ui_category = cat_ui_map.get(category.strip(), category)
    return f"""
    <div class="transaction-card">
        <div>
            <div style="color: #FFFFFF; font-weight: 700; font-size: 15px;">{merchant}</div>
            <div style="color: #64748B; font-size: 12px;">{date} • {ui_category}</div>
        </div>
        <div class="trans-amount">{amount}</div>
    </div>
    """

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

try:
    ws = sh.worksheet(next((s for s in [s.title for s in sh.worksheets()] if selected_month.lower() in s.lower()), None))
except Exception: st.error("Tab not found"); st.stop()

# --- DATA EXTRACTION ---
all_rows = ws.get_all_values()
prevu_var, reel_var = 0.0, 0.0
expenses_list = []
category_progress = []

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
        if "total" in cat.lower():
            prevu_var, reel_var = parse_amount(row[col_prevu]), parse_amount(row[col_actuel])
            break
        elif cat and cat.lower() not in ["", "nan"]:
            category_progress.append({"name": cat, "prevu": parse_amount(row[col_prevu]), "reel": parse_amount(row[col_actuel])})

row_history_start = -1
for i, row in enumerate(all_rows):
    if len(row) > 0 and str(row[0]).strip().lower() == "date":
        row_history_start = i + 1
        break

if row_history_start != -1:
    for i in range(row_history_start, len(all_rows)):
        row = all_rows[i]
        if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
            if "total" in str(row[0]).lower() or "total" in str(row[1]).lower(): continue
            expenses_list.append({"Date": row[0], "Marchand": row[1], "Montant": f"{parse_amount(row[2]):.2f} CHF", "Catégorie": row[4]})

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- MAIN UI ---
st.title(f"⚡ {selected_month_en} {now.year}")
c1, c2 = st.columns(2)
with c1: st.metric("Remaining", f"{restant:.2f} CHF", delta=f"{restant:.2f}")
with c2: st.metric("Budget Plan", f"{prevu_var:.0f} CHF")

st.write("")
st.markdown(f"**Total Spending:** <span style='color: #FFFFFF; font-weight: 800; font-size: 20px; text-shadow: 0 0 10px rgba(255,255,255,0.3);'>{reel_var:.2f} CHF</span>", unsafe_allow_html=True)

main_bar_color = "#3B82F6"
if percent >= 1.0: main_bar_color = "#E11D48"
elif percent >= 0.66: main_bar_color = "#F59E0B"

st.markdown(f"""
    <style>
    .stProgress > div > div > div > div {{ background: {main_bar_color} !important; box-shadow: 0 0 10px {main_bar_color}66; }}
    </style>
""", unsafe_allow_html=True)
st.progress(percent)

st.divider()

# --- CATEGORIES TRACKER ---
st.markdown("<h3 style='color: #FFFFFF; font-size: 24px; margin-bottom: 25px;'>📊 Categories</h3>", unsafe_allow_html=True)
if category_progress:
    sorted_categories = sorted(category_progress, key=lambda x: (x['reel'] > 0, x['prevu']), reverse=True)
    for cat in sorted_categories:
        st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)

st.divider()

# --- FORM & HISTORY ---
col_form, col_hist = st.columns([1.1, 1])
form_cat_map = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs", "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène"}

with col_form:
    with st.form("new_exp", clear_on_submit=True):
        st.markdown("<h4 style='color: #FFFFFF; font-size: 18px;'>➕ New Entry</h4>", unsafe_allow_html=True)
        lib = st.text_input("Merchant", placeholder="Apple, Migros...")
        amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f")
        cat_en = st.selectbox("Category", list(form_cat_map.keys()))
        note = st.text_input("Note")
        
        if st.form_submit_button("CONFIRM"):
            if lib and amt > 0:
                col_b = ws.col_values(2)
                target = 60
                for r in range(60, 150):
                    if r > len(col_b) or not str(col_b[r-1]).strip():
                        target = r
                        break
                new_data = [[datetime.now().strftime("%Y-%m-%d"), lib, amt, note, form_cat_map[cat_en]]]
                ws.update(values=new_data, range_name=f"A{target}:E{target}", value_input_option="USER_ENTERED")
                st.cache_resource.clear()
                st.rerun()

with col_hist:
    st.markdown("<h4 style='color: #FFFFFF; font-size: 18px;'>📡 History</h4>", unsafe_allow_html=True)
    if expenses_list:
        for exp in expenses_list[::-1][:5]:
            st.markdown(get_transaction_html(exp["Date"], exp["Marchand"], exp["Montant"], exp["Catégorie"]), unsafe_allow_html=True)

st.sidebar.caption(f"Last sync: {datetime.now().strftime('%H:%M')}")
