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

# Style iOS Premium
st.markdown("""
    <style>
    .main { background-color: #f2f2f7; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; }
    .stMetric { background-color: white; padding: 20px; border-radius: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stProgress > div > div > div > div { background-color: #34c759; }
    div[data-testid="stForm"] { background-color: white; padding: 25px; border-radius: 20px; border: none; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stButton>button { background-color: #007AFF; color: white; border-radius: 12px; height: 3.5em; font-weight: 600; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION ---
@st.cache_resource
def get_gsheet_client():
    # Vérification des secrets
    if "gcp_service_account" not in st.secrets:
        st.error("❌ Erreur : La clé 'gcp_service_account' est absente des Secrets Streamlit.")
        st.info("Assurez-vous d'avoir bien collé le bloc [gcp_service_account] dans les paramètres de l'app.")
        return None
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        # On s'assure que c'est bien un dictionnaire
        creds_dict = dict(creds_info)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erreur lors de l'authentification : {e}")
        return None

SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"
client = get_gsheet_client()

if not client: 
    st.warning("L'application attend la configuration des Secrets pour démarrer.")
    st.stop()

try:
    sh = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"❌ Accès au Google Sheet refusé : {e}")
    st.info("Vérifiez que vous avez partagé le fichier avec l'email du compte de service.")
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
except:
    st.error("Erreur de lecture de l'onglet.")
    st.stop()

# --- EXTRACTION DONNÉES ---
all_rows = ws.get_all_values()
prevu_var, reel_var = 0.0, 0.0
expenses_list = []

for row in all_rows:
    # Recherche "Charges Variables" (Colonnes F, G, H -> index 5, 6, 7)
    if len(row) > 7 and "Charges Variables" in row[5]:
        try:
            prevu_var = float(row[6].replace("'", "").replace(",", "").strip() or 0)
            reel_var = float(row[7].replace("'", "").replace(",", "").strip() or 0)
        except: pass
    
    # Historique : Colonnes A, B, C (Date, Marchand, Montant)
    if len(row) > 2 and "-" in row[0] and len(row[0]) >= 8:
        try:
            expenses_list.append({"Date": row[0], "Marchand": row[1], "Montant": f"{row[2]} CHF", "Cat": row[4]})
        except: pass

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- UI PRINCIPALE ---
st.title(f"📍 {selected_month} 2026")

c1, c2 = st.columns(2)
with c1:
    color = "normal" if restant > 0 else "inverse"
    st.metric("Reste", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color=color)
with c2:
    st.metric("Total Prévu", f"{prevu_var:.1f} CHF")

st.write(f"**Budget consommé :** {reel_var:.2f} CHF")
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
            st.success("Enregistré !")
            st.cache_resource.clear()
            st.rerun()

# --- HISTORIQUE ---
if expenses_list:
    with st.expander("🕒 Dernières dépenses"):
        recent = pd.DataFrame(expenses_list[::-1]).head(5)
        st.table(recent)

st.sidebar.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M')}")
