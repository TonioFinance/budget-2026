import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Budget 2026", page_icon="🏦", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE FINTECH PREMIUM (NOIR / BLEU / BLANC) ---
st.markdown("""
    <style>
    /* Fond principal OLED Black */
    .stApp { 
        background-color: #050505; 
        color: #F9FAFB; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Textes et Titres */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    p, label { color: #A1A1AA !important; font-weight: 500; }
    
    /* Cartes des Métriques (Reste / Total) */
    div[data-testid="stMetricValue"] { 
        font-size: 38px; 
        font-weight: 800; 
        color: #FFFFFF !important; 
        letter-spacing: -1px;
    }
    div[data-testid="stMetricLabel"] {
        color: #A1A1AA !important;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stMetric { 
        background-color: #121212; 
        padding: 24px; 
        border-radius: 20px; 
        border: 1px solid #27272A; 
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5); 
        transition: transform 0.2s ease;
    }
    .stMetric:hover { transform: translateY(-2px); }

    /* Barre de progression (Bleu Électrique) */
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #0052D4, #4364F7, #6FB1FC); 
        border-radius: 10px;
    }

    /* Boîte du Formulaire */
    div[data-testid="stForm"] { 
        background-color: #0A0A0A; 
        padding: 30px; 
        border-radius: 24px; 
        border: 1px solid #27272A; 
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8); 
    }

    /* Inputs et Selectbox */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #18181B !important;
        color: #FFFFFF !important;
        border: 1px solid #3F3F46 !important;
        border-radius: 10px;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #007AFF !important;
        box-shadow: 0 0 0 1px #007AFF !important;
    }

    /* Bouton d'action "Valider" */
    .stButton>button { 
        background-color: #007AFF; 
        color: #FFFFFF !important; 
        border-radius: 14px; 
        height: 3.5em; 
        font-size: 16px;
        font-weight: 600; 
        letter-spacing: 0.5px; 
        width: 100%; 
        border: none; 
        box-shadow: 0 4px 14px rgba(0, 122, 255, 0.3); 
        transition: all 0.2s ease-in-out; 
    }
    .stButton>button:hover { 
        background-color: #006CE0;
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.5); 
        transform: scale(1.02); 
    }
    
    /* Séparateur discret */
    hr { border-color: #27272A !important; margin-top: 2rem; margin-bottom: 2rem; }
    
    /* Tableaux de données (Dataframe) */
    .stDataFrame { border: 1px solid #27272A; border-radius: 12px; overflow: hidden; }
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
debug_info = [] 

# 1. RECHERCHE DYNAMIQUE DU HAUT DU TABLEAU
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

# 2. HISTORIQUE DES DÉPENSES (À partir de la ligne 60)
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
st.title(f"📍 {selected_month} {now.year}")
st.write("") # Petit espace

c1, c2 = st.columns(2)
with c1: st.metric("Reste", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color="normal" if restant > 0 else "inverse")
with c2: st.metric("Total Prévu", f"{prevu_var:.1f} CHF")

st.write("")
st.markdown(f"**Budget consommé :** <span style='color: #FFFFFF; font-weight: 600;'>{reel_var:.2f} CHF</span>", unsafe_allow_html=True)
st.progress(percent)

st.divider()

# --- FORMULAIRE ---
with st.form("new_exp", clear_on_submit=True):
    st.markdown("### ➕ Nouvel Achat")
    col_a, col_b = st.columns([2, 1])
    with col_a: lib = st.text_input("Marchand / Lieu", placeholder="Migros, Apple, Uber...")
    with col_b: amt = st.number_input("Montant (CHF)", min_value=0.0, step=0.1, format="%.2f")
    cat = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène"])
    note = st.text_input("Note (optionnel)", placeholder="Ex: Déjeuner collègues...")
    
    st.write("") # Espacement
    if st.form_submit_button("VALIDER LA DÉPENSE") and lib and amt > 0:
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat], value_input_option="USER_ENTERED")
        st.success("✅ Transaction enregistrée avec succès.")
        st.cache_resource.clear()
        st.rerun()

# --- HISTORIQUE ---
if expenses_list:
    st.write("")
    with st.expander("🕒 Activité Récente", expanded=True):
        st.dataframe(pd.DataFrame(expenses_list[::-1]).head(5), use_container_width=True, hide_index=True)

st.sidebar.caption(f"Dernière synchronisation : {datetime.now().strftime('%H:%M')}")
