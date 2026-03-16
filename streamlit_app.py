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

# Style personnalisé pour un look "App iPhone"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .stProgress > div > div > div > div { background-color: #007AFF; }
    div[data-testid="stForm"] { background-color: white; padding: 20px; border-radius: 15px; border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION À GOOGLE SHEETS ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erreur de configuration des Secrets : {e}")
        return None

# ID du tableur
SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"

client = get_gsheet_client()
if client:
    try:
        sh = client.open_by_key(SHEET_ID)
    except Exception as e:
        st.error("❌ Impossible d'accéder au fichier. Vérifie l'ID et le partage avec l'email du compte de service.")
        st.stop()
else:
    st.stop()

# --- GESTION DU MOIS ---
mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
now = datetime.now()
default_month = mois_fr[now.month - 1]

# Sidebar pour sélection manuelle si besoin
with st.sidebar:
    st.header("Paramètres")
    selected_month = st.selectbox("Choisir le mois", mois_fr, index=now.month - 1)
    if st.button("Rafraîchir les données"):
        st.cache_resource.clear()
        st.rerun()

try:
    # On essaie de trouver la feuille (insensible à la casse et aux espaces)
    available_sheets = [s.title for s in sh.worksheets()]
    target_sheet = None
    
    for s_name in available_sheets:
        if selected_month.lower() in s_name.lower():
            target_sheet = s_name
            break
            
    if target_sheet:
        ws = sh.worksheet(target_sheet)
    else:
        st.error(f"⚠️ Onglet '{selected_month}' introuvable.")
        st.info(f"Onglets disponibles : {', '.join(available_sheets)}")
        st.stop()
except Exception as e:
    st.error(f"Erreur lors de l'accès à l'onglet : {e}")
    st.stop()

# --- LECTURE DU BUDGET ---
data = ws.get_all_values()
prevu_var = 0.0
reel_var = 0.0

# Recherche flexible de "Charges Variables"
for row in data:
    # On cherche dans toute la ligne au cas où les colonnes ont bougé
    row_str = " ".join([str(cell) for cell in row])
    if "Charges Variables" in row_str:
        try:
            # On cherche les colonnes G (index 6) et H (index 7)
            if len(row) > 7:
                p_raw = row[6].replace("'", "").replace(",", "").replace("CHF", "").strip()
                r_raw = row[7].replace("'", "").replace(",", "").replace("CHF", "").strip()
                prevu_var = float(p_raw) if p_raw else 0.0
                reel_var = float(r_raw) if r_raw else 0.0
                break
        except (ValueError, IndexError):
            continue

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- INTERFACE ---
st.title(f"📊 Budget {selected_month}")

c1, c2 = st.columns(2)
with c1:
    delta_color = "normal" if restant > 0 else "inverse"
    st.metric("Reste", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color=delta_color)
with c2:
    st.metric("Total Prévu", f"{prevu_var:.2f} CHF")

st.write(f"**Consommation :** {reel_var:.2f} / {prevu_var:.2f} CHF")
st.progress(percent)

st.divider()

# --- FORMULAIRE D'AJOUT ---
st.subheader("➕ Ajouter une dépense")
with st.form("form_depense", clear_on_submit=True):
    date_d = st.date_input("Date", now)
    nom_d = st.text_input("Marchand", placeholder="Ex: Migros, Shell, Bar...")
    montant_d = st.number_input("Montant (CHF)", min_value=0.0, step=0.05, format="%.2f")
    cat_d = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène/Entretien"])
    note_d = st.text_input("Note", placeholder="Optionnel")
    
    submit = st.form_submit_button("Enregistrer la dépense")

if submit:
    if nom_d and montant_d > 0:
        # Format de ligne : Date, Marchand, Montant, Note, Catégorie
        nouvelle_ligne = [date_d.strftime("%Y-%m-%d"), nom_d, montant_d, note_d, cat_d]
        
        with st.spinner("Envoi vers Google Sheets..."):
            try:
                ws.append_row(nouvelle_ligne, value_input_option="USER_ENTERED")
                st.success(f"✅ {montant_d} CHF ajoutés chez {nom_d}")
                st.balloons()
                st.cache_resource.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de l'écriture : {e}")
    else:
        st.warning("Remplis le marchand et le montant !")

st.divider()
st.caption(f"Connecté : {sh.title} | {now.strftime('%H:%M:%S')}")
