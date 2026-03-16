import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Budget 2026", page_icon="💠", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE ULTRA-PRO / GLOW BLEU ---
st.markdown("""
    <style>
    /* Fond principal : Dégradé radial bleu abysse vers noir */
    .stApp { 
        background: radial-gradient(circle at top, #0A192F 0%, #020C1B 100%);
        color: #E2E8F0; 
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Textes et Titres */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 800 !important; text-shadow: 0 0 20px rgba(0, 198, 255, 0.3); }
    p, label { color: #94A3B8 !important; font-weight: 500; }
    
    /* Cartes des Métriques (Reste / Total) - Effet Verre & Néon */
    div[data-testid="stMetricValue"] { 
        font-size: 42px; 
        font-weight: 900; 
        color: #00F0FF !important; /* Bleu Cyan Néon */
        text-shadow: 0 0 15px rgba(0, 240, 255, 0.6), 0 0 30px rgba(0, 240, 255, 0.2); 
        letter-spacing: -1px;
    }
    div[data-testid="stMetricLabel"] {
        color: #60A5FA !important;
        font-size: 15px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .stMetric { 
        background: rgba(13, 25, 48, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 25px; 
        border-radius: 24px; 
        border: 1px solid rgba(0, 240, 255, 0.15); 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(0, 122, 255, 0.1); 
        transition: all 0.3s ease;
    }
    .stMetric:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 15px 40px rgba(0, 122, 255, 0.3), inset 0 0 25px rgba(0, 240, 255, 0.2); 
        border: 1px solid rgba(0, 240, 255, 0.4);
    }

    /* Barre de progression (Luminescence Bleue) */
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #0072FF, #00F0FF); 
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.7);
        border-radius: 10px;
    }

    /* Boîte du Formulaire */
    div[data-testid="stForm"] { 
        background: linear-gradient(145deg, #0B1930, #040D21);
        padding: 35px; 
        border-radius: 24px; 
        border: 1px solid #1E3A5F; 
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6); 
    }

    /* Inputs et Selectbox */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: rgba(2, 12, 27, 0.8) !important;
        color: #00F0FF !important;
        border: 1px solid #1E3A5F !important;
        border-radius: 12px;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #00F0FF !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }

    /* Bouton d'action "Valider" - Glowing Button */
    .stButton>button { 
        background: linear-gradient(90deg, #0072FF 0%, #00C6FF 100%);
        color: #FFFFFF !important; 
        border-radius: 16px; 
        height: 3.8em; 
        font-size: 16px;
        font-weight: 800; 
        text-transform: uppercase;
        letter-spacing: 1.5px; 
        width: 100%; 
        border: none; 
        box-shadow: 0 8px 25px rgba(0, 198, 255, 0.4); 
        transition: all 0.3s ease-in-out; 
    }
    .stButton>button:hover { 
        box-shadow: 0 12px 35px rgba(0, 240, 255, 0.7); 
        transform: scale(1.03); 
    }
    
    /* Séparateur discret */
    hr { border-color: rgba(30, 58, 95, 0.5) !important; margin-top: 2.5rem; margin-bottom: 2.5rem; }
    
    /* Tableaux de données (Dataframe) */
    .stDataFrame { border: 1px solid #1E3A5F; border-radius: 14px; overflow: hidden; background: rgba(13, 25, 48, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DE NETTOYAGE ---
def parse_amount(val):
    if not val: return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try: return float(cleaned)
    except ValueError: return 0.0

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

col_var = -1
col_prevu = -1
col_actuel = -1
row_var_start = -1

for i, row in enumerate(all_rows):
    if i >= 59: break
    for j, cell in enumerate(row):
        if "charges variables" in str(cell).strip().lower():
            col_var = j
            row_var_start = i
            for k in range(j + 1, len(row)):
                cell_val = str(row[k]).strip().lower()
                if "prévu" in cell_val or "prevu" in cell_val: col_prevu = k
                elif "actuel" in cell_val: col_actuel = k
            break
    if col_var != -1: break

if col_prevu == -1: col_prevu = col_var + 1
if col_actuel == -1: col_actuel = col_var + 2

if col_var != -1 and row_var_start != -1:
    for i in range(row_var_start + 1, min(row_var_start + 20, len(all_rows))):
        row = all_rows[i]
        if len(row) > max(col_prevu, col_actuel):
            if "total" in str(row[col_var]).strip().lower():
                prevu_var = parse_amount(row[col_prevu])
                reel_var = parse_amount(row[col_actuel])
                break

for i in range(59, len(all_rows)):
    row = all_rows[i]
    if len(row) > 4 and str(row[0]).strip() != "":
        try:
            amt_clean = parse_amount(row[2])
            expenses_list.append({"Date": row[0], "Marchand": row[1], "Montant": f"{amt_clean:.2f} CHF", "Catégorie": row[4]})
        except IndexError: pass

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- UI PRINCIPALE ---
st.title(f"💠 {selected_month} {now.year}")
st.write("") 

c1, c2 = st.columns(2)
with c1: st.metric("Restant", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color="normal" if restant > 0 else "inverse")
with c2: st.metric("Budget Fixé", f"{prevu_var:.1f} CHF")

st.write("")
st.markdown(f"**Conso actuelle :** <span style='color: #00F0FF; font-weight: 700; text-shadow: 0 0 10px rgba(0,240,255,0.5);'>{reel_var:.2f} CHF</span>", unsafe_allow_html=True)
st.progress(percent)

st.divider()

# --- FORMULAIRE ---
with st.form("new_exp", clear_on_submit=True):
    st.markdown("<h3 style='color: #00F0FF !important; text-shadow: 0 0 15px rgba(0, 240, 255, 0.5);'>⚡ Nouvelle Transaction</h3>", unsafe_allow_html=True)
    st.write("")
    col_a, col_b = st.columns([2, 1])
    with col_a: lib = st.text_input("Bénéficiaire / Lieu", placeholder="Ex: Migros, Apple, Uber...")
    with col_b: amt = st.number_input("Montant (CHF)", min_value=0.0, step=0.1, format="%.2f")
    cat = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène"])
    note = st.text_input("Note (optionnel)")
    
    st.write("")
    if st.form_submit_button("VALIDER LE PAIEMENT") and lib and amt > 0:
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat], value_input_option="USER_ENTERED")
        st.success("✅ Transaction encryptée et ajoutée.")
        st.cache_resource.clear()
        st.rerun()

# --- HISTORIQUE ---
if expenses_list:
    st.write("")
    with st.expander("📡 Flux Récents", expanded=True):
        st.dataframe(pd.DataFrame(expenses_list[::-1]).head(5), use_container_width=True, hide_index=True)

st.sidebar.caption(f"Dernière synchronisation serveur : {datetime.now().strftime('%H:%M')}")
