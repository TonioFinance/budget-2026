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
        creds_dict = dict(creds_info)
        
        # --- LIGNE DE DÉBOGAGE ---
        st.info(f"🔍 Clés lues par Streamlit : {', '.join(creds_dict.keys())}")
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Erreur lors de l'authentification : {e}")
        return None

SHEET_ID
