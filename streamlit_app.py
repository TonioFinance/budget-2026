import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Budget 2026", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")

# --- STYLE OBSIDIAN & EMERALD WITH DYNAMIC GLOW (LATO FONT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');

    .stApp { 
        background-color: #030712;
        background-image: radial-gradient(circle at 50% -20%, #064e3b 0%, #030712 85%);
        color: #F8FAFC; 
        font-family: 'Lato', sans-serif;
    }

    /* --- ULTRA-FAST HOVER ANIMATION (0.15s) --- */
    * { transition: all 0.15s ease-out; }

    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    
    /* Metrics Top (Green Glow effect) */
    div[data-testid="stMetricValue"] { 
        font-family: 'Lato', sans-serif;
        font-size: 40px !important; 
        font-weight: 900 !important;
        color: #FFFFFF !important; 
        text-shadow: 0 0 10px rgba(255,255,255,0.2), 0 0 30px rgba(16, 185, 129, 0.3); 
    }
    
    div[data-testid="stMetricLabel"] { 
        font-weight: 700;
