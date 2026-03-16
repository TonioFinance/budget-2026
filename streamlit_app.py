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
    /* Fond principal de l'application (Bleu nuit profond) */
    .stApp {
        background-color: #0B1120;
        color: #F8FAFC;
    }
    
    /* Typographie globale */
    h1, h2, h3, p, label {
        color: #E2E8F0 !important;
    }

    /* Style des métriques (Cartes de Reste et Total) */
    div[data-testid="stMetricValue"] { 
        font-size: 32px; 
        font-weight: 800; 
        color: #38BDF8 !important; /* Bleu clair néon */
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4); /* Effet Glow */
    }
    .stMetric { 
        background-color: #1E293B; /* Bleu-gris ardoise */
        padding: 20px; 
        border-radius: 16px; 
        border: 1px solid #334155;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05); 
    }

    /* Barre de progression avec dégradé et lueur */
    .stProgress > div > div > div > div { 
        background: linear-gradient(90deg, #0EA5E9, #3B82F6);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
    }

    /* Boîte du Formulaire */
    div[data-testid="stForm"] { 
        background-color: #162032; 
        padding: 25px; 
        border-radius: 20px; 
        border: 1px solid #1E293B; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); 
    }

    /* Bouton d'action "Valider" */
    .stButton>button { 
        background: linear-gradient(135deg, #2563EB, #1D4ED8); 
        color: white !important; 
        border-radius: 12px; 
        height: 3.5em; 
        font-weight: 700; 
        letter-spacing: 1px;
        width: 100%; 
        border: none; 
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.7);
        transform: translateY(-2px);
        background: linear-gradient(135deg, #3B82F6, #2563EB); 
    }
    
    /* Ligne de séparation */
    hr {
        border-color: #334155 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION ---
@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets:
        st.error("❌ Erreur : La clé 'gcp_service_account' est absente des Secrets Streamlit.")
        return None
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_dict = dict(creds_info)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erreur lors de l'authentification : {e}")
        return None

SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"
client = get_gsheet_client()

if not client: 
    st.warning("L'application attend la configuration correcte des Secrets pour démarrer.")
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
    st.error(f"Erreur de lecture de l'onglet : {e}")
    st.stop()

# --- EXTRACTION DONNÉES ---
all_rows = ws.get_all_values()
prevu_var, reel_var = 0.0, 0.0

expenses_list = [] # <-- Correction de la variable ici

# On utilise enumerate pour connaître le numéro de la ligne
for i, row in enumerate(all_rows):
    
    # 1. Recherche "Charges Variables" pour le résumé (en haut du tableau)
    if len(row) > 7 and "Charges Variables" in row[5]:
        try:
            prevu_var = float(row[6].replace("'", "").replace(",", "").strip() or 0)
            reel_var = float(row[7].replace("'", "").replace(",", "").strip() or 0)
        except ValueError: 
            pass
    
    # 2. Historique des dépenses (UNIQUEMENT à partir de la ligne 60 -> index 59)
    if i >= 59:
        # On vérifie qu'il y a bien une date ou un marchand pour éviter les lignes vides
        if len(row) > 4 and row[0].strip() != "":
            try:
                expenses_list.append({
                    "Date": row[0], 
                    "Marchand": row[1], 
                    "Montant": f"{row[2]} CHF", 
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
    with st.expander("🕒 Dernières dépenses (Lignes 60+)", expanded=True):
        # On affiche les 5 dernières dépenses ajoutées (ordre inverse)
        recent = pd.DataFrame(expenses_list[::-1]).head(5)
        st.dataframe(recent, use_container_width=True, hide_index=True)

st.sidebar.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M')}")
