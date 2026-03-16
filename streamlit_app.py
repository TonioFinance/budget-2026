import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Budget 2026",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STYLE PRO & GLOW (DARK BLUE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F8FAFC; }
    h1, h2, h3, p, label { color: #E2E8F0 !important; }
    div[data-testid="stMetricValue"] { 
        font-size: 32px; font-weight: 800; color: #38BDF8 !important; text-shadow: 0 0 15px rgba(56, 189, 248, 0.4); 
    }
    .stMetric { 
        background-color: #1E293B; padding: 20px; border-radius: 16px; border: 1px solid #334155;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05); 
    }
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #0EA5E9, #3B82F6); box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
    }
    div[data-testid="stForm"] { 
        background-color: #162032; padding: 25px; border-radius: 20px; border: 1px solid #1E293B; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); 
    }
    .stButton>button { 
        background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white !important; border-radius: 12px; height: 3.5em; 
        font-weight: 700; letter-spacing: 1px; width: 100%; border: none; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4); transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.7); transform: translateY(-2px); background: linear-gradient(135deg, #3B82F6, #2563EB); 
    }
    hr { border-color: #334155 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION DE NETTOYAGE DES MONTANTS ---
def parse_amount(val):
    if not val: return 0.0
    # Enlève "CHF", les espaces, les apostrophes et remplace la virgule par un point
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace(" ", "").replace("'", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

# --- CONNEXION ---
@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets:
        st.error("❌ Erreur : La clé 'gcp_service_account' est absente des Secrets Streamlit.")
        return None
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erreur d'authentification : {e}")
        return None

SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"
client = get_gsheet_client()

if not client: 
    st.stop()

try:
    sh = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"❌ Accès au Google Sheet refusé : {e}")
    st.stop()

# --- NAVIGATION ---
mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
now = datetime.now()
selected_month = st.sidebar.selectbox("Mois consulté", mois_fr, index=now.month - 1)

try:
    available_sheets = [s.title for s in sh.worksheets()]
    target_sheet = next((s for s in available_sheets if selected_month.lower() in s.lower()), None)
    if not target_sheet:
        st.error(f"L'onglet {selected_month} n'existe pas dans ce fichier.")
        st.stop()
    ws = sh.worksheet(target_sheet)
except Exception as e:
    st.error("Erreur de lecture de l'onglet.")
    st.stop()

# --- EXTRACTION DONNÉES ---
all_rows = ws.get_all_values()
prevu_var, reel_var = 0.0, 0.0
expenses_list = []
in_var_section = False

for i, row in enumerate(all_rows):
    # 1. RÉCUPÉRATION DES TOTAUX (Haut du tableau, avant la ligne 60)
    if i < 59 and len(row) > 7:
        col_f_lower = str(row[5]).strip().lower()
        
        # On repère le début du bloc "Charges Variables"
        if "charges variables" in col_f_lower:
            in_var_section = True
        
        # On repère la fin du bloc (début des factures)
        elif "factures" in col_f_lower:
            in_var_section = False
            
        # Si on est dans le bon bloc et qu'on trouve la ligne "Total"
        elif in_var_section and "total" in col_f_lower:
            prevu_var = parse_amount(row[6])
            reel_var = parse_amount(row[7])
            in_var_section = False # On arrête de chercher

    # 2. HISTORIQUE DES DÉPENSES (À partir de la ligne 60)
    if i >= 59:
        if len(row) > 4 and str(row[0]).strip() != "":
            try:
                amt_clean = parse_amount(row[2])
                expenses_list.append({
                    "Date": row[0], 
                    "Marchand": row[1], 
                    "Montant": f"{amt_clean:.2f} CHF", 
                    "Catégorie": row[4]
                })
            except IndexError: 
                pass

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- UI PRINCIPALE ---
st.title(f"📍 {selected_month} {now.year}")

c1, c2 = st.columns(2)
with c1:
    color = "normal" if restant > 0 else "inverse"
    st.metric("Reste", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color=color)
with c2:
    st.metric("Total Prévu", f"{prevu_var:.1f} CHF")

st.markdown(f"**Budget consommé :** `{reel_var:.2f} CHF`")
st.progress(percent)

st.divider()

# --- FORMULAIRE ---
with st.form("new_exp", clear_on_submit=True):
    st.subheader("➕ Ajouter un achat")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        lib = st.text_input("Où ?", placeholder="Migros, Coop, Bar...")
    with col_b:
        amt = st.number_input("Combien ?", min_value=0.0, step=0.1, format="%.2f")
    
    cat = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène"])
    note = st.text_input("Note (optionnel)")
    
    if st.form_submit_button("VALIDER L'ACHAT"):
        if lib and amt > 0:
            new_line = [datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat]
            ws.append_row(new_line, value_input_option="USER_ENTERED")
            st.success("✨ Achat enregistré avec succès !")
            st.cache_resource.clear()
            st.rerun()

# --- HISTORIQUE ---
if expenses_list:
    with st.expander("🕒 Dernières dépenses", expanded=True):
        recent = pd.DataFrame(expenses_list[::-1]).head(5)
        st.dataframe(recent, use_container_width=True, hide_index=True)

st.sidebar.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M')}")
