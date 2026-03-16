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
    # Définit les droits d'accès
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Récupère les credentials depuis les secrets Streamlit
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# ID du tableur extrait de ton lien
SHEET_ID = "1HXd22qMTATg__4U1Os0ktUMnhK1vflKlRU9b5yoxFHU"

try:
    client = get_gsheet_client()
    sh = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error("❌ Erreur de connexion au Google Sheet. Vérifie tes Secrets Streamlit et le partage du fichier.")
    st.stop()

# --- DÉTERMINATION DU MOIS ---
mois_fr = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août", 
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}
now = datetime.now()
current_month = mois_fr[now.month]

try:
    ws = sh.worksheet(current_month)
except Exception:
    st.error(f"La feuille '{current_month}' est introuvable dans ton tableur.")
    st.stop()

# --- LECTURE DU BUDGET ---
# On récupère toutes les valeurs pour analyser la structure
data = ws.get_all_values()

prevu_var = 0.0
reel_var = 0.0

# Recherche de la ligne "Charges Variables" dans le récapitulatif
# Basé sur tes fichiers : Label en Col F (index 5), Prévu en G (index 6), Réel en H (index 7)
for row in data:
    if len(row) > 7 and "Charges Variables" in row[5]:
        try:
            # Nettoyage des nombres (remplace virgules et apostrophes)
            p_raw = row[6].replace("'", "").replace(",", "").strip()
            r_raw = row[7].replace("'", "").replace(",", "").strip()
            prevu_var = float(p_raw) if p_raw else 0.0
            reel_var = float(r_raw) if r_raw else 0.0
        except ValueError:
            pass
        break

restant = prevu_var - reel_var
percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

# --- INTERFACE ---
st.title(f"📊 Budget {current_month}")

# Métriques principales
c1, c2 = st.columns(2)
with c1:
    delta_color = "normal" if restant > 0 else "inverse"
    st.metric("Reste à dépenser", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color=delta_color)
with c2:
    st.metric("Total Prévu", f"{prevu_var:.2f} CHF")

# Barre de progression
st.write(f"**Consommation du budget :** {reel_var:.2f} / {prevu_var:.2f} CHF")
bar_color = "green" if percent < 0.8 else "orange" if percent < 1 else "red"
st.progress(percent)

st.divider()

# --- FORMULAIRE D'AJOUT ---
st.subheader("➕ Ajouter une dépense")
with st.form("form_depense", clear_on_submit=True):
    date_d = st.date_input("Date", now)
    nom_d = st.text_input("Marchand / Libellé", placeholder="Ex: Migros, Shell, Bar...")
    montant_d = st.number_input("Montant (CHF)", min_value=0.0, step=0.05, format="%.2f")
    
    # Liste des catégories basée sur ton tableur
    cat_d = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène/Entretien"])
    note_d = st.text_input("Note (Description)", placeholder="Optionnel")
    
    submit = st.form_submit_button("Enregistrer la dépense")

if submit:
    if nom_d and montant_d > 0:
        # Préparation de la ligne : Date, Marchand, Montant, Description, Catégorie
        # On l'ajoute à la fin de la feuille (append_row)
        nouvelle_ligne = [date_d.strftime("%Y-%m-%d"), nom_d, montant_d, note_d, cat_d]
        
        with st.spinner("Enregistrement dans Google Sheets..."):
            ws.append_row(nouvelle_ligne, value_input_option="USER_ENTERED")
        
        st.success(f"✅ {montant_d} CHF ajoutés avec succès !")
        st.balloons()
        # On force le rafraîchissement pour voir les nouvelles métriques
        st.cache_resource.clear()
        st.rerun()
    else:
        st.warning("Merci de remplir au moins le marchand et le montant.")

st.divider()
st.caption(f"Connecté au tableur : {sh.title} | {now.strftime('%H:%M:%S')}")
