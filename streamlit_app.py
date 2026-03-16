import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Budget 2026", page_icon="💰", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE PRO & GLOW (DARK BLUE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B1120; color: #F8FAFC; }
    h1, h2, h3, p, label { color: #E2E8F0 !important; }
    div[data-testid="stMetricValue"] { font-size: 32px; font-weight: 800; color: #38BDF8 !important; text-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }
    .stMetric { background-color: #1E293B; padding: 20px; border-radius: 16px; border: 1px solid #334155; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05); }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #0EA5E9, #3B82F6); box-shadow: 0 0 12px rgba(59, 130, 246, 0.6); }
    div[data-testid="stForm"] { background-color: #162032; padding: 25px; border-radius: 20px; border: 1px solid #1E293B; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); }
    .stButton>button { background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white !important; border-radius: 12px; height: 3.5em; font-weight: 700; letter-spacing: 1px; width: 100%; border: none; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4); transition: all 0.3s ease; }
    .stButton>button:hover { box-shadow: 0 6px 20px rgba(37, 99, 235, 0.7); transform: translateY(-2px); background: linear-gradient(135deg, #3B82F6, #2563EB); }
    hr { border-color: #334155 !important; }
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

# On balaie tout le fichier (avant la ligne 60) pour trouver "Charges Variables", "Prévu" et "Actuel"
for i, row in enumerate(all_rows):
    if i >= 59: break
    for j, cell in enumerate(row):
        if "charges variables" in str(cell).strip().lower():
            col_var = j
            row_var_start = i
            # On cherche les colonnes Prévu et Actuel sur la même ligne
            for k in range(j + 1, len(row)):
                cell_val = str(row[k]).strip().lower()
                if "prévu" in cell_val or "prevu" in cell_val: col_prevu = k
                elif "actuel" in cell_val: col_actuel = k
            break
    if col_var != -1: break

# Sécurité si les mots n'ont pas été trouvés exactement sur la ligne
if col_prevu == -1: col_prevu = col_var + 1
if col_actuel == -1: col_actuel = col_var + 2

if col_var != -1 and row_var_start != -1:
    debug_info.append(f"✅ 'Charges Variables' trouvé (Ligne {row_var_start+1}, Colonne {col_var+1}). Colonne Actuel = {col_actuel+1}")
    # On descend dans la MÊME colonne pour chercher le Total
    for i in range(row_var_start + 1, min(row_var_start + 20, len(all_rows))):
        row = all_rows[i]
        if len(row) > max(col_prevu, col_actuel):
            if "total" in str(row[col_var]).strip().lower():
                prevu_var = parse_amount(row[col_prevu])
                reel_var = parse_amount(row[col_actuel])
                debug_info.append(f"✅ 'Total' trouvé (Ligne {i+1}). Prévu: {prevu_var}, Actuel: {reel_var}")
                break
else:
    debug_info.append("❌ Le code n'a pas trouvé la cellule contenant exactement 'Charges Variables'.")

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

c1, c2 = st.columns(2)
with c1: st.metric("Reste", f"{restant:.2f} CHF", delta=f"{restant:.2f}", delta_color="normal" if restant > 0 else "inverse")
with c2: st.metric("Total Prévu", f"{prevu_var:.1f} CHF")
st.markdown(f"**Budget Actuel consommé :** `{reel_var:.2f} CHF`")
st.progress(percent)

# -- OUTIL DE DÉBOGAGE (Aide visuelle qui s'affiche seulement si ça plante) --
if prevu_var == 0:
    with st.expander("🛠️ Console de Débogage (Ouvrir si les chiffres sont à 0)"):
        for info in debug_info: st.write(info)

st.divider()

# --- FORMULAIRE ---
with st.form("new_exp", clear_on_submit=True):
    st.subheader("➕ Ajouter un achat")
    col_a, col_b = st.columns([2, 1])
    with col_a: lib = st.text_input("Où ?", placeholder="Migros, Coop, Bar...")
    with col_b: amt = st.number_input("Combien ?", min_value=0.0, step=0.1, format="%.2f")
    cat = st.selectbox("Catégorie", ["Courses", "Sorties/Restos", "Transport", "Loisirs", "Imprévus", "Shopping", "Hygiène"])
    note = st.text_input("Note (optionnel)")
    if st.form_submit_button("VALIDER L'ACHAT") and lib and amt > 0:
        ws.append_row([datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat], value_input_option="USER_ENTERED")
        st.success("✨ Achat enregistré !")
        st.cache_resource.clear()
        st.rerun()

# --- HISTORIQUE ---
if expenses_list:
    with st.expander("🕒 Dernières dépenses", expanded=True):
        st.dataframe(pd.DataFrame(expenses_list[::-1]).head(5), use_container_width=True, hide_index=True)

st.sidebar.caption(f"Dernière synchro : {datetime.now().strftime('%H:%M')}")
