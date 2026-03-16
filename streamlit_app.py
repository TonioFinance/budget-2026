import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Budget 2026", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & AZURE (NOIR / BLANC / BLEU) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    .stApp { 
        background-color: #030712;
        background-image: radial-gradient(circle at 50% -20%, #172554 0%, #030712 70%);
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
        text-shadow: 0 0 10px rgba(255,255,255,0.2), 0 0 20px rgba(59, 130, 246, 0.5); 
    }
    div[data-testid="stMetricLabel"] {
        color: #60A5FA !important; 
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    .stMetric { 
        background: rgba(15, 23, 42, 0.4); 
        backdrop-filter: blur(10px);
        padding: 24px; 
        border-radius: 20px; 
        border: 1px solid rgba(255, 255, 255, 0.05); 
        border-top: 1px solid rgba(59, 130, 246, 0.5); 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8); 
        transition: all 0.4s ease;
    }
    .stMetric:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.3); 
        border-color: rgba(59, 130, 246, 0.4);
    }

    /* Main Progress */
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #1E3A8A, #3B82F6, #E0F2FE); 
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.8);
        border-radius: 10px;
    }

    /* Form */
    div[data-testid="stForm"] { 
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.4) 0%, rgba(3, 7, 18, 0.8) 100%);
        padding: 25px; 
        border-radius: 20px; 
        border: 1px solid rgba(59, 130, 246, 0.2); 
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.9); 
    }

    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: rgba(3, 7, 18, 0.8) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px;
        font-family: 'Space Grotesk', sans-serif;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
    }

    /* Button */
    .stButton>button { 
        background: linear-gradient(90deg, #1D4ED8 0%, #3B82F6 100%);
        color: #FFFFFF !important; 
        border-radius: 14px; 
        height: 3.5em; 
        font-size: 15px;
        font-weight: 700; 
        letter-spacing: 1.5px; 
        width: 100%; 
        border: none; 
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4); 
        transition: all 0.3s ease; 
    }
    .stButton>button:hover { 
        background: linear-gradient(90deg, #2563EB 0%, #60A5FA 100%);
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.8); 
        transform: scale(1.02); 
    }
    
    /* Transaction Card */
    .transaction-card {
        background: rgba(15, 23, 42, 0.5); 
        border: 1px solid rgba(59, 130, 246, 0.15); 
        border-radius: 16px; 
        padding: 16px 20px; 
        margin-bottom: 12px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        transition: all 0.3s ease; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .transaction-card:hover {
        transform: translateX(5px);
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(59, 130, 246, 0.4);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
    }
    .icon-box {
        background: rgba(59, 130, 246, 0.1); 
        width: 42px; 
        height: 42px; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 18px; 
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    hr { border-color: rgba(59, 130, 246, 0.15) !important; margin: 2rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTION DE NETTOYAGE ---
def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

# --- FONCTIONS UI (HTML CUSTOM) ---
def get_progress_html(name, reel, prevu):
    if prevu > 0: percent = reel / prevu
    else: percent = 1.0 if reel > 0 else 0.0
    
    pct_str = f"{min(percent*100, 100):.1f}%"
    
    if percent >= 1.0: bar_color = "linear-gradient(90deg, #9F1239, #E11D48)" # Rouge
    elif percent > 0.8: bar_color = "linear-gradient(90deg, #B45309, #F59E0B)" # Orange
    else: bar_color = "linear-gradient(90deg, #1D4ED8, #3B82F6)" # Bleu

    return f"""
    <div style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="color: #F8FAFC; font-size: 14px; font-weight: 600;">{name}</span>
            <span style="color: #94A3B8; font-size: 13px; font-weight: 500; font-family: 'Space Grotesk', sans-serif;">{reel:.0f} / {prevu:.0f} CHF</span>
        </div>
        <div style="background: rgba(15, 23, 42, 0.8); border-radius: 10px; width: 100%; height: 8px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);">
            <div style="background: {bar_color}; width: {pct_str}; height: 100%; border-radius: 10px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);"></div>
        </div>
    </div>
    """

def get_transaction_icon(category):
    cat = str(category).lower()
    if "course" in cat: return "🛒"
    if "resto" in cat or "sortie" in cat: return "🍔"
    if "transport" in cat: return "🚕"
    if "loisir" in cat: return "🎮"
    if "shopping" in cat or "habit" in cat: return "🛍️"
    if "hygiène" in cat or "entretien" in cat: return "🧼"
    if "vacance" in cat: return "✈️"
    return "💸"

def get_transaction_html(date, merchant, amount, category):
    icon = get_transaction_icon(category)
    return f"""
    <div class="transaction-card">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div class="icon-box">{icon}</div>
            <div>
                <div style="color: #F8FAFC; font-weight: 600; font-size: 15px; letter-spacing: 0.3px;">{merchant}</div>
                <div style="color: #64748B; font-size: 13px; margin-top: 3px; font-weight: 500;">{date} • {category}</div>
            </div>
        </div>
        <div style="color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px; text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);">
            {amount}
        </div>
    </div>
    """

# --- CONNEXION ---
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
except Exception as e: st.error(f"Accès refusé: {e}"); st.stop()

# --- NAVIGATION ---
mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
now = datetime.now()
selected_month = st.sidebar.selectbox("Mois consulté", mois_fr, index=now.month - 1)

try:
    ws = sh.worksheet(next((s for s in [s.title for s in sh.worksheets()] if selected_month.lower() in s.lower()), None))
except Exception: st.error("Onglet introuvable"); st.stop()

# --- EXTRACTION DONNÉES ---
all_rows = ws.get_all_values()
prevu_var, reel_var = 0.0, 0.0
expenses_list = []
category_progress = []
debug_info = []

# 1. SCAN INTELLIGENT POUR CHARGES VARIABLES (Ignore le bloc Récapitulatif)
col_var = -1
col_prevu = -1
col_actuel = -1
row_var_start = -1

for i, row in enumerate(all_rows):
    if i >= 65: break
    for j, cell in enumerate(row):
        if "charges variables" in str(cell).strip().lower():
            row_str = " ".join([str(x).lower() for x in row])
            # La ligne de sécurité : On s'assure qu'on est sur l'en-tête du vrai tableau, pas le récap
            if "prévu" in row_str or "prevu" in row_str or "actuel" in row_str or "réel" in row_str or "reel" in row_str:
                col_var = j
                row_var_start = i
                for k in range(j + 1, len(row)):
                    cell_val = str(row[k]).strip().lower()
                    if "prévu" in cell_val or "prevu" in cell_val: col_prevu = k
                    elif "actuel" in cell_val or "réel" in cell_val or "reel" in cell_val: col_actuel = k
                break
    if col_var != -1: break

if col_prevu == -1: col_prevu = col_var + 1
if col_actuel == -1: col_actuel = col_var + 2

if col_var != -1 and row_var_start != -1:
    debug_info.append(f"✅ 'Charges Variables' ligne {row_var_start+1}. Prévu (col {col_prevu}), Actuel (col {col_actuel}).")
    for i in range(row_var_start + 1, min(row_var_start + 20, len(all_rows))):
        row = all_rows[i]
        if len(row) > max(col_prevu, col_actuel):
            cat_name = str(row[col_var]).strip()
            if "total" in cat_name.lower():
                prevu_var = parse_amount(row[col_prevu])
                reel_var = parse_amount(row[col_actuel])
                break
            elif cat_name and cat_name.lower() not in ["", "nan"]:
                c_prevu = parse_amount(row[col_prevu])
                c_reel = parse_amount(row[col_actuel])
                if c_prevu > 0 or c_reel > 0:
                    category_progress.append({"name": cat_name, "prevu": c_prevu, "reel": c_reel})
else:
    debug_info.append("❌ Section 'Charges Variables' (avec Prévu/Actuel) introuvable.")

# 2. SCANNAGE DYNAMIQUE HISTORIQUE
row_history_start = -1
for i in range(min(100, len(all_rows))):
    if len(all_rows[i]) > 0 and str(all_rows[i][0]).strip().lower() == "date":
        row_history_start = i + 1
        debug_info.append(f"✅ 'Date' trouvé ligne {row_history_start}")
        break

if row_history_start == -1: row_history_start = 59 

for i in range(row_history_start, len(all_rows)):
    row = all_rows[i]
    if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
        if "total" in str(row[0]).strip().lower() or "total" in str(row[1]).strip().lower(): continue
        try:
            amt_clean = parse_amount(row[2])
            if amt_clean > 0:
                expenses_list.append({"Date": row[0], "Marchand": row[1], "Montant": f"{amt_clean:.2f} CHF", "Catégorie": row[4]})
        except IndexError: pass

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- UI PRINCIPALE ---
st.title(f"⚡ {selected_month} {now.year}")
st.write("") 

c1, c2 = st.columns(2)
with c1: st.metric("Restant", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color="normal" if restant > 0 else "inverse")
with c2: st.metric("Budget Fixé", f"{prevu_var:.1f} CHF")

st.write("")
st.markdown(f"**Conso actuelle :** <span style='color: #FFFFFF; font-family: \"Space Grotesk\", sans-serif; font-size: 18px; text-shadow: 0 0 10px rgba(59, 130, 246, 0.6);'>{reel_var:.2f} CHF</span>", unsafe_allow_html=True)
st.progress(percent)

# DEBUG
if prevu_var == 0:
    with st.expander("🛠️ Console de Débogage"):
        for info in debug_info: st.write(info)

st.divider()

# --- TRACKER & FORMULAIRE ---
st.markdown("<h3 style='color: #FFFFFF; font-size: 22px; margin-bottom: 20px; text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);'>📊 Traqueur par Catégorie</h3>", unsafe_allow_html=True)

if category_progress:
    col_c1, col_c2 = st.columns(2)
    for idx, cat in enumerate(category_progress):
        target_col = col_c1 if idx % 2 == 0 else col_c2
        with target_col:
            st.markdown(get_progress_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)
else:
    st.info("Aucune catégorie de dépense trouvée.")

st.divider()

# --- AJOUT & TRANSACTIONS ---
col_form, col_hist = st.columns([1.2, 1])

with col_form:
    with st.form("new_exp", clear_on_submit=True):
        st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 15px;'>➕ Nouvelle Dépense</h4>", unsafe_allow_html=True)
        lib = st.text_input("Bénéficiaire / Lieu", placeholder="Ex: Migros, Apple...")
        amt = st.number_input("Montant (CHF)", min_value=0.0, step=0.1, format="%.2f")
        cat = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène"])
        note = st.text_input("Note (optionnel)")
        
        st.write("")
        if st.form_submit_button("ENREGISTRER LE PAIEMENT") and lib and amt > 0:
            ws.append_row([datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat], value_input_option="USER_ENTERED")
            st.success("✅ Transaction confirmée.")
            st.cache_resource.clear()
            st.rerun()

with col_hist:
    st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 15px;'>📡 Activité Récente</h4>", unsafe_allow_html=True)
    if expenses_list:
        for exp in expenses_list[::-1][:5]:
            st.markdown(get_transaction_html(exp["Date"], exp["Marchand"], exp["Montant"], exp["Catégorie"]), unsafe_allow_html=True)
    else:
        st.info("Aucun paiement récent.")

st.write("")
st.sidebar.caption(f"Dernière synchronisation : {datetime.now().strftime('%H:%M')}")
