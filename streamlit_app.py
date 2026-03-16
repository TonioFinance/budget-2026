import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026", page_icon="🟢", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & EMERALD (BLACK / WHITE / GREEN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    .stApp { 
        background-color: #020617;
        background-image: radial-gradient(circle at 50% -20%, #064e3b 0%, #020617 75%);
        color: #F8FAFC; 
        font-family: 'Space Grotesk', sans-serif;
    }
    
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    p, label { color: #94A3B8 !important; }
    
    /* Metrics Top */
    div[data-testid="stMetricValue"] { 
        font-family: 'Space Grotesk', sans-serif;
        font-size: 44px; 
        font-weight: 700; 
        color: #FFFFFF !important; 
        text-shadow: 0 0 10px rgba(255,255,255,0.2), 0 0 20px rgba(16, 185, 129, 0.4); 
    }
    div[data-testid="stMetricLabel"] {
        color: #34d399 !important; /* Emerald Label */
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    .stMetric { 
        background: rgba(15, 23, 42, 0.6); 
        backdrop-filter: blur(12px);
        padding: 24px; 
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-top: 1px solid rgba(16, 185, 129, 0.5); /* Glowing Green Top */
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); 
        transition: all 0.4s ease;
    }
    .stMetric:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.2); 
        border-color: rgba(16, 185, 129, 0.4);
    }

    /* Main Progress Bar (Thicker & Green) */
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #064e3b, #10b981, #d1fae5); 
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.8);
        border-radius: 12px;
        height: 14px !important;
    }

    /* Form */
    div[data-testid="stForm"] { 
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.5) 0%, rgba(2, 6, 23, 0.9) 100%);
        padding: 30px; 
        border-radius: 24px; 
        border: 1px solid rgba(16, 185, 129, 0.2); 
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.9); 
    }

    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: rgba(2, 6, 23, 0.8) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4) !important;
    }

    /* Button (Glowing Green) */
    .stButton>button { 
        background: linear-gradient(90deg, #059669 0%, #10b981 100%);
        color: #FFFFFF !important; 
        border-radius: 14px; 
        height: 3.8em; 
        font-weight: 700; 
        letter-spacing: 2px; 
        width: 100%; 
        border: none; 
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3); 
        transition: all 0.3s ease; 
    }
    .stButton>button:hover { 
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.6); 
        transform: scale(1.02); 
    }
    
    /* Transaction Card */
    .transaction-card {
        background: rgba(15, 23, 42, 0.5); 
        border: 1px solid rgba(16, 185, 129, 0.1); 
        border-radius: 16px; 
        padding: 16px 20px; 
        margin-bottom: 12px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        transition: all 0.3s ease; 
    }
    .transaction-card:hover {
        transform: translateX(8px);
        background: rgba(16, 185, 129, 0.05);
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .icon-box {
        background: rgba(16, 185, 129, 0.1); 
        width: 44px; 
        height: 44px; 
        border-radius: 12px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 20px; 
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    hr { border-color: rgba(16, 185, 129, 0.1) !important; margin: 2rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

def get_progress_html(name, reel, prevu):
    if prevu > 0: percent = reel / prevu
    else: percent = 1.0 if reel > 0 else 0.0
    
    pct_str = f"{min(percent*100, 100):.1f}%"
    
    # Color Logic: Green -> Orange -> Red
    if percent >= 1.0: bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" # Red
    elif percent > 0.8: bar_color = "linear-gradient(90deg, #B45309, #F59E0B)" # Orange
    else: bar_color = "linear-gradient(90deg, #059669, #10B981)" # Emerald Green

    cat_ui_map = {
        "Courses": "Groceries", "Sorties/Restos": "Dining", 
        "Transport": "Transport", "Loisirs": "Leisure", 
        "Imprévus": "Unexpected", "Shopping": "Shopping", "Hygiène": "Hygiene"
    }
    ui_name = cat_ui_map.get(name.strip(), name)

    return f"""
    <div style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #F8FAFC; font-size: 15px; font-weight: 600;">{ui_name}</span>
            <span style="color: #34d399; font-size: 14px; font-weight: 700;">{reel:.0f} / {prevu:.0f} CHF</span>
        </div>
        <div style="background: rgba(2, 6, 23, 0.8); border-radius: 20px; width: 100%; height: 14px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
            <div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 20px; box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);"></div>
        </div>
    </div>
    """

def get_transaction_icon(category):
    cat = str(category).lower()
    if any(x in cat for x in ["course", "grocer"]): return "🛒"
    if any(x in cat for x in ["resto", "sortie", "dining"]): return "🍔"
    if "transport" in cat: return "🚕"
    if any(x in cat for x in ["loisir", "leisure"]): return "🎮"
    if any(x in cat for x in ["shopping", "habit"]): return "🛍️"
    if any(x in cat for x in ["hygiene", "entretien"]): return "🧼"
    if "vacance" in cat: return "✈️"
    return "💸"

def get_transaction_html(date, merchant, amount, category):
    icon = get_transaction_icon(category)
    cat_ui_map = {"Courses": "Groceries", "Sorties/Restos": "Dining", "Transport": "Transport", "Loisirs": "Leisure", "Imprévus": "Unexpected", "Shopping": "Shopping", "Hygiène": "Hygiene"}
    ui_category = cat_ui_map.get(category.strip(), category)
    
    return f"""
    <div class="transaction-card">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div class="icon-box">{icon}</div>
            <div>
                <div style="color: #F8FAFC; font-weight: 600; font-size: 15px;">{merchant}</div>
                <div style="color: #64748B; font-size: 13px; font-weight: 500;">{date} • {ui_category}</div>
            </div>
        </div>
        <div style="color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px;">
            {amount}
        </div>
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
except Exception as e: st.error(f"Access Denied: {e}"); st.stop()

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
                    cell_val = str(row[k]).strip().lower()
                    if "prévu" in cell_val or "prevu" in cell_val: col_prevu = k
                    elif any(x in cell_val for x in ["actuel", "réel", "reel"]): col_actuel = k
                break
    if col_var != -1: break

if col_var != -1 and row_var_start != -1:
    for i in range(row_var_start + 1, min(row_var_start + 20, len(all_rows))):
        row = all_rows[i]
        cat_name = str(row[col_var]).strip()
        if "total" in cat_name.lower():
            prevu_var, reel_var = parse_amount(row[col_prevu]), parse_amount(row[col_actuel])
            break
        elif cat_name and cat_name.lower() not in ["", "nan"]:
            category_progress.append({"name": cat_name, "prevu": parse_amount(row[col_prevu]), "reel": parse_amount(row[col_actuel])})

row_history_start = -1
for i in range(min(100, len(all_rows))):
    if len(all_rows[i]) > 0 and str(all_rows[i][0]).strip().lower() == "date":
        row_history_start = i + 1
        break

for i in range(row_history_start if row_history_start != -1 else 59, len(all_rows)):
    row = all_rows[i]
    if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
        if "total" in str(row[0]).strip().lower() or "total" in str(row[1]).strip().lower(): continue
        amt = parse_amount(row[2])
        if amt > 0: expenses_list.append({"Date": row[0], "Marchand": row[1], "Montant": f"{amt:.2f} CHF", "Catégorie": row[4]})

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- MAIN UI ---
st.title(f"⚡ {selected_month_en} {now.year}")

c1, c2 = st.columns(2)
with c1: st.metric("Remaining", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color="normal" if restant > 0 else "inverse")
with c2: st.metric("Planned Budget", f"{prevu_var:.1f} CHF")

st.write("")
st.markdown(f"**Current Spending:** <span style='color: #10b981; font-weight: 700; text-shadow: 0 0 10px rgba(16,185,129,0.5);'>{reel_var:.2f} CHF</span>", unsafe_allow_html=True)
st.progress(percent)

st.divider()

# --- TRACKER ---
st.markdown("<h3 style='color: #FFFFFF; font-size: 22px; margin-bottom: 25px; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);'>📊 Category Tracker</h3>", unsafe_allow_html=True)
if category_progress:
    col_c1, col_c2 = st.columns(2)
    for idx, cat in enumerate(category_progress):
        target_col = col_c1 if idx % 2 == 0 else col_c2
        with target_col: st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)

st.divider()

# --- ADD & HISTORY ---
col_form, col_hist = st.columns([1.2, 1])
form_cat_map = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs", "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène"}

with col_form:
    with st.form("new_exp", clear_on_submit=True):
        st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 15px;'>➕ New Expense</h4>", unsafe_allow_html=True)
        lib = st.text_input("Merchant / Place", placeholder="e.g. Migros, Apple...")
        amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f")
        cat_en = st.selectbox("Category", list(form_cat_map.keys()))
        note = st.text_input("Note (optional)")
        if st.form_submit_button("ADD TRANSACTION") and lib and amt > 0:
            ws.append_row([datetime.now().strftime("%Y-%m-%d"), lib, amt, note, form_cat_map[cat_en]], value_input_option="USER_ENTERED")
            st.success("✅ Added!")
            st.cache_resource.clear()
            st.rerun()

with col_hist:
    st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 15px;'>📡 Recent Activity</h4>", unsafe_allow_html=True)
    if expenses_list:
        for exp in expenses_list[::-1][:5]: st.markdown(get_transaction_html(exp["Date"], exp["Marchand"], exp["Montant"], exp["Catégorie"]), unsafe_allow_html=True)

st.sidebar.caption(f"Last sync: {datetime.now().strftime('%H:%M')}")
