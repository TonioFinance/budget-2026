import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
import time
import yfinance as yf

st.set_page_config(page_title="Budget 2026 Pro", page_icon="⚡", layout="centered", initial_sidebar_state="collapsed")


# =============================================================================
# 1. DESIGN SYSTEM
#    Pour changer le look de toute l'app : modifie TOKENS (couleurs, rayons, polices).
#    Pour changer un composant précis : modifie sa section dans CSS plus bas.
# =============================================================================
TOKENS = {
    # Fonds
    "bg": "#030712",
    "bg-glow": "#172554",
    # Texte
    "text": "#F8FAFC",
    "text-muted": "#94A3B8",
    "text-dim": "#64748B",
    # Bleus (accent principal)
    "blue-900": "#1E3A8A",
    "blue-600": "#2563EB",
    "blue-500": "#3B82F6",
    "blue-400": "#60A5FA",
    "blue-300": "#93C5FD",
    # États
    "green": "#34D399",
    "green-600": "#10B981",
    "green-800": "#059669",
    "amber": "#FBBF24",
    "amber-600": "#F59E0B",
    "amber-800": "#B45309",
    "red": "#FB7185",
    "red-600": "#E11D48",
    "red-800": "#9F1239",
    # Formes
    "radius-lg": "24px",
    "radius-md": "16px",
    "radius-sm": "12px",
    # Police
    "font": "'Lato', sans-serif",
    # Dégradés (réutilisés partout)
    "grad-blue": "linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%)",
    "grad-blue-hover": "linear-gradient(90deg, #2A4CAE 0%, #3B82F6 100%)",
    "grad-blue-glass": "linear-gradient(90deg, rgba(30, 58, 138, 0.62) 0%, rgba(37, 99, 235, 0.62) 100%)",
    "grad-blue-glass-hover": "linear-gradient(90deg, rgba(42, 76, 174, 0.78) 0%, rgba(59, 130, 246, 0.78) 100%)",
    "glow-blue-hover": "0 10px 30px rgba(59, 130, 246, 0.40), inset 0 1px 1px rgba(255, 255, 255, 0.40)",
    "grad-ok": "linear-gradient(90deg, #059669, #10B981)",
    "grad-warn": "linear-gradient(90deg, #B45309, #F59E0B)",
    "grad-over": "linear-gradient(90deg, #9F1239, #E11D48)",
    # Ombres
    "glow-blue": "0 6px 15px rgba(37, 99, 235, 0.2), inset 0 1px 2px rgba(255,255,255,0.2)",
}

CSS_IMPORTS = """
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');
@import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
"""

CSS = """
/* ---------- BASE ---------- */
.stApp {
    background-color: var(--bg);
    background-image: radial-gradient(circle at 50% -20%, var(--bg-glow) 0%, var(--bg) 85%);
    color: var(--text);
    font-family: var(--font);
}
* { transition: all 0.05s ease-out; }
h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 700 !important; letter-spacing: -0.5px; }
.text-green { color: var(--green); }
.text-red { color: var(--red); }

/* ---------- COMPOSANT PARTAGÉ : "BLUE GLOW" ----------
   Tout ce qui est listé ici partage EXACTEMENT le même look (dégradé bleu).
   Pour ajouter un élément au style, ajoute simplement son sélecteur à cette liste. */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button,
[data-testid="stExpander"] summary {
    background: var(--grad-blue) !important;
    border: 1px solid rgba(59, 130, 246, 0.5) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--glow-blue) !important;
    color: #FFFFFF !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button { height: 3.8rem !important; width: 100%; }
[data-testid="stButton"] button p,
[data-testid="stFormSubmitButton"] button p { color: #FFFFFF !important; font-weight: 900 !important; }

/* ---------- MONTH PICKER : bouton translucide (verre), dégradé bleu clair -> bleu marine ----------
   Le "bouton" est le conteneur du widget (classe st-key-<key>), donc ça ne dépend pas
   de la structure interne du selectbox : tout l'intérieur est rendu transparent. */
.st-key-header_month_picker,
.st-key-sidebar_month_picker {
    background: var(--grad-blue-glass) !important;
    border: 1px solid rgba(59, 130, 246, 0.5) !important;
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.28), inset 0 1px 1px rgba(255, 255, 255, 0.30) !important;
    padding: 0.35rem 0.5rem !important;
    cursor: pointer;
}
.st-key-header_month_picker:hover,
.st-key-sidebar_month_picker:hover {
    background: var(--grad-blue-glass-hover) !important;
    border-color: rgba(147, 197, 253, 0.60) !important;
    box-shadow: var(--glow-blue-hover) !important;
}
.st-key-header_month_picker *,
.st-key-sidebar_month_picker * {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}
.st-key-header_month_picker svg,
.st-key-sidebar_month_picker svg { fill: #FFFFFF !important; }

/* ---------- SELECTBOX / INPUTS "NORMAUX" (formulaire, filtres) ---------- */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"] {
    background-color: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: var(--radius-sm);
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input { color: #FFFFFF !important; }

/* ---------- LISTE DÉROULANTE (popover, commun à tous les selectbox) ---------- */
[data-baseweb="popover"] ul,
[data-baseweb="popover"] [data-baseweb="menu"],
[role="listbox"] {
    background: rgba(15, 23, 42, 0.92) !important;
    backdrop-filter: blur(16px);
    border: 1px solid rgba(147, 197, 253, 0.30) !important;
    border-radius: 14px !important;
}
[role="option"] { color: #FFFFFF !important; background: transparent !important; }
[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background: var(--grad-blue-glass) !important;
}

/* ---------- ONGLETS (sélecteurs ARIA, indépendants de BaseWeb) ---------- */
[role="tablist"] {
    gap: 24px;
    background-color: rgba(15, 23, 42, 0.7);
    padding: 10px 20px;
    border-radius: 26px;
    border: 1px solid rgba(59, 130, 246, 0.2);
    backdrop-filter: blur(25px);
    margin-bottom: 40px;
    justify-content: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
[role="tablist"] > div[aria-hidden="true"],
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[role="tab"] {
    height: 55px;
    background-color: transparent !important;
    border-radius: var(--radius-md) !important;
    padding: 0 35px !important;
}
[role="tab"] p, [role="tab"] span {
    color: var(--text-dim) !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
[role="tab"][aria-selected="true"] { background-color: rgba(37, 99, 235, 0.15) !important; }
[role="tab"][aria-selected="true"] p, [role="tab"][aria-selected="true"] span {
    color: #FFFFFF !important;
    font-weight: 900 !important;
    text-shadow: 0 0 15px rgba(255,255,255,0.4);
}

/* ---------- HERO CARD ---------- */
.hero-card {
    background: linear-gradient(160deg, rgba(30, 58, 138, 0.25) 0%, rgba(3, 7, 18, 0.8) 100%);
    padding: 35px 30px;
    border-radius: var(--radius-lg);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-top: 2px solid rgba(59, 130, 246, 0.7);
    box-shadow: 0 20px 40px rgba(0,0,0,0.6), inset 0 1px 20px rgba(59,130,246,0.1);
    backdrop-filter: blur(15px);
    margin-bottom: 25px;
    text-align: center;
}
.hero-card--green {
    border-color: rgba(16, 185, 129, 0.4);
    border-top-color: rgba(16, 185, 129, 0.7);
    background: linear-gradient(160deg, rgba(16, 185, 129, 0.1) 0%, rgba(3, 7, 18, 0.8) 100%);
}
.hero-top {
    display: flex; justify-content: space-between;
    margin-bottom: 10px; font-size: 13px; color: var(--blue-300);
    text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700;
}
.hero-top b { color: #FFFFFF; }
.hero-value {
    font-size: 52px; font-weight: 900; color: #FFFFFF;
    text-shadow: 0 0 20px rgba(59,130,246,0.6);
    margin-bottom: 25px; letter-spacing: -1px;
}
.hero-value small { font-size: 24px; color: var(--blue-400); }
.hero-card--green .hero-value small { color: var(--green); }

/* ---------- BARRES DE PROGRESSION & ÉTATS (ok / warn / over) ---------- */
.bar { background: rgba(0,0,0,0.5); border-radius: 10px; width: 100%; height: 10px; border: 1px solid rgba(255,255,255,0.05); overflow: hidden; }
.bar > div { height: 100%; border-radius: 10px; }
.fill--ok   { background: var(--grad-ok); }
.fill--warn { background: var(--grad-warn); }
.fill--over { background: var(--grad-over); }

.banner {
    margin-top: 25px; padding: 12px; border-radius: var(--radius-sm);
    font-size: 14px; font-weight: 600;
    display: flex; align-items: center; justify-content: center; gap: 8px;
}
.banner--ok   { background: rgba(16,185,129,0.1); color: var(--green); border: 1px solid rgba(16,185,129,0.3); }
.banner--warn { background: rgba(245,158,11,0.1); color: var(--amber); border: 1px solid rgba(245,158,11,0.3); }
.banner--over { background: rgba(225,29,72,0.1);  color: var(--red);   border: 1px solid rgba(225,29,72,0.3); }

.badge { padding: 2px 8px; border-radius: 8px; }
.badge--ok   { background: rgba(16,185,129,0.12); color: var(--green); border: 1px solid rgba(16,185,129,0.25); }
.badge--warn { background: rgba(245,158,11,0.12); color: var(--amber); border: 1px solid rgba(245,158,11,0.25); }
.badge--over { background: rgba(225,29,72,0.15);  color: var(--red);   border: 1px solid rgba(225,29,72,0.3); }

/* ---------- CARTES LISTE (catégories, transactions, investissements) ---------- */
.card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 18px;
    margin-bottom: 12px;
}
.card:hover {
    background: rgba(59,130,246,0.08);
    border-color: rgba(59,130,246,0.3);
}
.card--cat { padding: 16px 20px; cursor: pointer; }
.card--cat:hover { transform: scale(1.02); }
.card--tx { padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; border-radius: var(--radius-md); margin-bottom: 10px; }
.card--tx:hover { transform: translateX(8px) scale(1.01); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
.card--inv { padding: 18px 22px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s ease; }
.card--inv:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }

.row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.cat-label { color: #FFFFFF; font-size: 16px; font-weight: 700; }
.cat-amount { color: #FFFFFF; font-size: 15px; font-weight: 700; text-shadow: 0 0 10px rgba(59,130,246,0.3); }
.cat-planned { color: var(--text-dim); font-size: 13px; font-weight: 600; }
.cat-sub { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 12px; font-weight: 700; }

.tx-icon {
    background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.2);
    width: 40px; height: 40px; border-radius: var(--radius-sm);
    display: flex; align-items: center; justify-content: center;
}
.tx-title { color: #FFFFFF; font-weight: 700; font-size: 15px; }
.tx-meta { color: var(--text-dim); font-size: 12px; margin-top: 2px; }
.tx-amount { color: #FFFFFF; font-weight: 800; font-size: 15px; }

.inv-logo {
    width: 48px; height: 48px; border-radius: 50%; object-fit: cover;
    background-color: var(--bg); border: 2px solid rgba(96,165,250,0.4);
    box-shadow: 0 4px 10px rgba(0,0,0,0.3); flex-shrink: 0;
}
.inv-name { color: #FFFFFF; font-weight: 800; font-size: 17px; letter-spacing: -0.2px; }
.inv-ticker { color: var(--text-muted); font-size: 13px; margin-top: 3px; font-weight: 600; }
.inv-value { color: #FFFFFF; font-weight: 800; font-size: 17px; }
.inv-perf { margin-top: 4px; font-size: 14px; font-weight: 800; }

/* ---------- NET WORTH ---------- */
.nw-grid { display: flex; gap: 12px; margin-top: 25px; }
.nw-card {
    flex: 1; background: rgba(15,23,42,0.5);
    border: 1px solid rgba(59,130,246,0.2); border-radius: var(--radius-md);
    padding: 15px; text-align: center;
}
.nw-title { font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 5px; }
.nw-value { font-size: 18px; font-weight: 900; }

/* ---------- HOVER DES BOUTONS (même effet que l'expander et le sélecteur de mois) ---------- */
[data-testid="stButton"] button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: var(--grad-blue-hover) !important;
    border-color: rgba(147, 197, 253, 0.60) !important;
    box-shadow: var(--glow-blue-hover) !important;
}

/* ---------- POP-UP (st.dialog) : verre sombre + glissement depuis le bas ---------- */
@keyframes slide-up {
    from { opacity: 0; transform: translateY(60px) scale(0.98); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
div[role="dialog"] {
    background: rgba(10, 18, 40, 0.92) !important;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(59, 130, 246, 0.35) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 30px 80px rgba(0, 0, 0, 0.7), inset 0 1px 20px rgba(59, 130, 246, 0.10) !important;
    animation: slide-up 0.35s cubic-bezier(0.2, 0.8, 0.2, 1);
}
div[role="dialog"] h2 { color: #FFFFFF !important; font-weight: 900 !important; letter-spacing: 1.5px; text-transform: uppercase; }

/* ---------- PASTILLES DE CATÉGORIE (st.pills) ---------- */
[data-testid="stPills"] button {
    border-radius: 999px !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(59, 130, 246, 0.25) !important;
    color: var(--text-muted) !important;
    font-weight: 700 !important;
}
[data-testid="stPills"] button:hover { border-color: rgba(147, 197, 253, 0.6) !important; color: #FFFFFF !important; }
[data-testid="stPills"] button[aria-checked="true"],
[data-testid="stPills"] button[aria-pressed="true"],
[data-testid="stPills"] [data-testid="stBaseButton-pillsActive"] {
    background: var(--grad-blue) !important;
    border-color: rgba(59, 130, 246, 0.6) !important;
    color: #FFFFFF !important;
    box-shadow: var(--glow-blue) !important;
}

/* ---------- EXPANDER ---------- */
[data-testid="stExpander"] {
    background: rgba(15,23,42,0.2) !important;
    border: 1px solid rgba(59,130,246,0.3) !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 15px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary { padding: 14px 20px !important; cursor: pointer; }
[data-testid="stExpander"] summary:hover {
    background: var(--grad-blue-hover) !important;
    border-color: rgba(147, 197, 253, 0.60) !important;
    box-shadow: var(--glow-blue-hover) !important;
}
[data-testid="stExpander"] summary p { color: #FFFFFF !important; font-weight: 900 !important; letter-spacing: 1.5px; }

/* ---------- CONTENEUR "VERRE" POUR LES GRAPHIQUES (st.container(key="glass_...")) ---------- */
[class*="st-key-glass_"] {
    background: rgba(15,23,42,0.3);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: var(--radius-lg);
    padding: 20px;
    margin-top: 20px;
}

/* ---------- TITRES ---------- */
.page-title { color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -1px; line-height: 1.2; }
.page-sub { color: var(--text-muted); font-size: 18px; margin-top: 5px; }
.page-sub b { color: var(--blue-400); }
.page-cycle { color: var(--text-dim); font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-top: 4px; text-transform: uppercase; }
.section-title { color: #FFFFFF; font-weight: 700; text-align: center; letter-spacing: -0.5px; }

[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid rgba(59,130,246,0.2); }

/* ---------- MOBILE ---------- */
@media (max-width: 768px) {
    .hero-value { font-size: 42px !important; }
    .hero-card { padding: 25px 20px !important; }
    [role="tablist"] { gap: 10px; padding: 5px 10px; }
    [role="tab"] { padding: 0 15px !important; }
    [role="tab"] p, [role="tab"] span { font-size: 13px !important; }
    [class*="st-key-glass_"] { padding: 15px 5px; }
    .nw-grid { flex-wrap: wrap; }
    .nw-card { flex-basis: 40%; }
}
"""


def inject_css():
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in TOKENS.items()) + "}"
    st.markdown(f"<style>{CSS_IMPORTS}{root}{CSS}</style>", unsafe_allow_html=True)


inject_css()


# =============================================================================
# 2. COMPOSANTS UI (chaque fonction retourne du HTML, aucune logique de données)
#    Important : pas d'indentation en début de ligne dans le HTML (sinon Markdown
#    le prend pour un bloc de code), d'où les "".join([...]).
# =============================================================================
CATEGORY_UI = {
    "Courses": ("Groceries", "ph-shopping-cart"),
    "Sorties/Restos": ("Dining", "ph-fork-knife"),
    "Transport": ("Transport", "ph-car"),
    "Loisirs": ("Leisure", "ph-game-controller"),
    "Imprévus": ("Unexpected", "ph-warning-circle"),
    "Shopping": ("Shopping", "ph-tote"),
    "Hygiène": ("Hygiene", "ph-drop"),
    "Hygiène/Entretien": ("Hygiene", "ph-drop"),
}
FORM_CATS = {"Groceries": "Courses", "Dining": "Sorties/Restos", "Transport": "Transport", "Leisure": "Loisirs",
             "Unexpected": "Imprévus", "Shopping": "Shopping", "Hygiene": "Hygiène/Entretien"}


def format_chf(value):
    try:
        return f"{float(value):,.2f}".replace(",", "'")
    except (ValueError, TypeError):
        return "0.00"


def level(percent, warn=0.66, crit=1.0):
    """Retourne 'ok', 'warn' ou 'over' : sert à choisir les classes CSS (fill--, badge--, banner--)."""
    if percent >= crit:
        return "over"
    if percent >= warn:
        return "warn"
    return "ok"


def ui_category(name):
    return CATEGORY_UI.get(str(name).strip(), (name, "ph-wallet"))


def title_html(text, icon=None, size=22, margin="0 0 20px 0"):
    icon_html = f"<i class='ph {icon}'></i> " if icon else ""
    return f"<h3 class='section-title' style='font-size:{size}px; margin:{margin};'>{icon_html}{text}</h3>"


def hero_html(top_left, top_right, value_html, extra_html="", variant=""):
    cls = f"hero-card {variant}".strip()
    return "".join([
        f"<div class='{cls}'>",
        f"<div class='hero-top'><div>{top_left}</div><div>{top_right}</div></div>",
        f"<div class='hero-value'>{value_html}</div>",
        extra_html,
        "</div>",
    ])


def progress_bar_html(percent, lvl):
    return f"<div class='bar'><div class='fill--{lvl}' style='width:{min(percent * 100, 100):.1f}%;'></div></div>"


def banner_html(percent):
    lvl = level(percent, warn=0.66, crit=0.80)
    text = {
        "over": ("ph-warning", f"Critical: {percent * 100:.0f}% consumed"),
        "warn": ("ph-info", f"Careful: {percent * 100:.0f}% consumed"),
        "ok": ("ph-check-circle", "On track"),
    }[lvl]
    return f"<div class='banner banner--{lvl}'><i class='ph {text[0]}'></i> {text[1]}</div>"


def category_card_html(name, reel, prevu):
    ui_name, icon = ui_category(name)
    percent = reel / prevu if prevu > 0 else (1.0 if reel > 0 else 0.0)
    lvl = level(percent)
    if prevu > 0:
        diff = prevu - reel
        badge = f"{format_chf(diff)} CHF left" if diff >= 0 else f"+{format_chf(abs(diff))} CHF over"
        pct_label = f"{percent * 100:.0f}% used"
    else:
        badge = "Unplanned" if reel > 0 else "0.00 CHF"
        pct_label = "No limit set"
    return "".join([
        "<div class='card card--cat'>",
        "<div class='row' style='margin-bottom:8px;'>",
        f"<div style='display:flex; align-items:center; gap:10px;'><i class='ph {icon}' style='font-size:22px; color:var(--blue-400);'></i><span class='cat-label'>{ui_name}</span></div>",
        f"<div><span class='cat-amount'>{format_chf(reel)}</span> <span class='cat-planned'>/ {format_chf(prevu)} CHF</span></div>",
        "</div>",
        progress_bar_html(percent, lvl),
        f"<div class='cat-sub'><span style='color:var(--text-dim);'>{pct_label}</span><span class='badge badge--{lvl}'>{badge}</span></div>",
        "</div>",
    ])


def transaction_card_html(date, merchant, amount, category, note=""):
    ui_cat, icon = ui_category(category)
    note_html = f" • <span style='color:var(--text-muted); font-style:italic;'>{note}</span>" if note and str(note).strip() else ""
    return "".join([
        "<div class='card card--tx'>",
        "<div style='display:flex; align-items:center; gap:15px;'>",
        f"<div class='tx-icon'><i class='ph {icon}' style='font-size:20px; color:var(--blue-400);'></i></div>",
        f"<div style='text-align:left;'><div class='tx-title'>{merchant}</div><div class='tx-meta'>{date} • {ui_cat}{note_html}</div></div>",
        "</div>",
        f"<div class='tx-amount'>{amount}</div>",
        "</div>",
    ])


def investment_card_html(item, show_amounts):
    perf_cls = "text-green" if item["unit_perf"] >= 0 else "text-red"
    perf_sign = "+" if item["unit_perf"] >= 0 else ""
    name_url = item["asset_name"].replace("'", "").replace('"', "").replace(" ", "+")
    logo = f"https://ui-avatars.com/api/?name={name_url}&background=0F172A&color=60A5FA&rounded=true&bold=true&font-size=0.4"
    if show_amounts:
        qty = f"{item['qty']:.6f}".rstrip("0").rstrip(".") if item["qty"] < 1 else f"{item['qty']:.4f}".rstrip("0").rstrip(".")
        pnl_sign = "+" if item["pnl_chf"] >= 0 else ""
        price = f"{format_chf(item['value'])} CHF"
        perf = f"{perf_sign}{item['unit_perf']:.2f}%<br>{pnl_sign}{format_chf(item['pnl_chf'])} CHF"
        ticker = f"{item['ticker']} • {qty} Units"
    else:
        price = f"{format_chf(item['current_price'])} {item['currency']}".strip() if item["current_price"] > 0 else "Market Down"
        perf = f"{perf_sign}{item['unit_perf']:.2f}%"
        ticker = item["ticker"]
    return "".join([
        "<div class='card card--inv'>",
        f"<div style='display:flex; align-items:center; gap:16px;'><img src='{logo}' class='inv-logo'>",
        f"<div style='text-align:left;'><div class='inv-name'>{item['asset_name']}</div><div class='inv-ticker'>{ticker}</div></div></div>",
        f"<div style='text-align:right;'><div class='inv-value'>{price}</div><div class='inv-perf'><span class='{perf_cls}'>{perf}</span></div></div>",
        "</div>",
    ])


def net_worth_html(total, cash, emergency, invest, debts):
    def cell(title, value, color):
        return f"<div class='nw-card'><div class='nw-title'>{title}</div><div class='nw-value' style='color:{color};'>{format_chf(value)}</div></div>"
    return hero_html(
        "", "",
        f"{format_chf(total)} <small>CHF</small>",
        extra_html="<div class='nw-grid'>" + "".join([
            cell("Cash (Rem.)", cash, "#38BDF8"),
            cell("Emergency", emergency, "#818CF8"),
            cell("Investments", invest, "#A78BFA"),
            cell("Debts", debts, "var(--red)"),
        ]) + "</div>",
        variant="hero-card--green",
    ).replace("<div class='hero-top'><div></div><div></div></div>",
              "<div class='hero-top' style='justify-content:center; margin-bottom:15px;'><span style='color:var(--green); letter-spacing:2px;'>TOTAL NET WORTH</span></div>")


def style_fig(fig, height, **layout):
    muted = TOKENS["text-muted"]
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=height,
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(showgrid=False, color=muted),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color=muted),
        **layout,
    )
    return fig


# =============================================================================
# 3. DONNÉES (Google Sheets + yfinance)
# =============================================================================
def parse_amount(val):
    if not val or str(val).lower() in ["nan", "none", ""]:
        return 0.0
    cleaned = str(val).upper().replace("CHF", "").replace(" ", "").replace("\u202f", "").replace("\xa0", "").replace("'", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def cell_at(row, idx, default=""):
    return row[idx] if 0 <= idx < len(row) else default


def parse_trend_date(d_str, year, start_month=None):
    d_str = str(d_str).strip().replace(".", "/")
    if not d_str:
        return pd.NaT
    if "-" in d_str or d_str.count("/") == 2:
        return pd.to_datetime(d_str, dayfirst=True, errors="coerce")
    parts = d_str.split("/")
    if len(parts) == 2:
        inferred_year = year
        try:
            if start_month == 12 and int(parts[1]) == 1:
                inferred_year = year + 1
        except ValueError:
            pass
        return pd.to_datetime(f"{parts[0]}/{parts[1]}/{inferred_year}", format="%d/%m/%Y", errors="coerce")
    return pd.to_datetime(d_str, errors="coerce")


@st.cache_resource
def get_gsheet_client():
    if "gcp_service_account" not in st.secrets:
        return None
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
        )
        return gspread.authorize(creds)
    except Exception:
        return None


SHEET_ID = "1RIue5DT0RyOWlXTdMXYqRrffHogMOH8lkRyX_z-We_c"
client = get_gsheet_client()
if not client:
    st.stop()
try:
    sh = client.open_by_key(SHEET_ID)
except Exception:
    st.error("Access Denied")
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_sheet_titles(sheet_id):
    return [s.title for s in get_gsheet_client().open_by_key(sheet_id).worksheets()]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_worksheet_data(sheet_id, worksheet_title):
    return get_gsheet_client().open_by_key(sheet_id).worksheet(worksheet_title).get_all_values()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_portfolio_data(sheet_id):
    total_val = total_cost = total_fees = 0.0
    enriched = []
    try:
        rows = get_gsheet_client().open_by_key(sheet_id).worksheet("Portfolio").get_all_values()
        header_idx = next((i for i, r in enumerate(rows) if any(k in " ".join(str(c).lower() for c in r) for k in ("ticker", "isin"))), -1)
        if header_idx == -1:
            return total_val, total_cost, total_fees, enriched

        headers = [str(h).strip() for h in rows[header_idx]]
        df = pd.DataFrame(rows[header_idx + 1:], columns=headers)
        for _, row in df.iterrows():
            ticker = str(row.get("Ticker / ISIN", "")).strip()
            if not ticker or ticker.lower() in ["nan", "none"]:
                continue
            qty = parse_amount(row.get("Units", "0"))
            if qty <= 0:
                continue
            invested = parse_amount(row.get("Total Invested", "0"))
            fees = parse_amount(row.get("Fees", "0"))
            entry_price = parse_amount(row.get("Entry Price", row.get("Amount", "0")))
            try:
                stock = yf.Ticker(ticker)
                price = 0.0
                try:
                    fast = stock.fast_info.get("last_price", 0.0)
                    if pd.notna(fast):
                        price = float(fast)
                except Exception:
                    pass
                if price <= 0.0 or pd.isna(price):
                    hist = stock.history(period="5d")
                    if not hist.empty and pd.notna(hist["Close"].iloc[-1]):
                        price = float(hist["Close"].iloc[-1])
                if pd.isna(price):
                    price = 0.0

                value = price * qty
                cost_basis = invested + fees
                total_val += value
                total_cost += cost_basis
                total_fees += fees
                enriched.append({
                    "asset_name": str(row.get("Nom", ticker)), "ticker": ticker,
                    "currency": str(row.get("Currency", "")).strip(),
                    "qty": qty, "current_price": price, "value": value, "entry_price": entry_price,
                    "pnl_chf": value - cost_basis,
                    "unit_perf": ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0.0,
                })
            except Exception:
                pass
    except Exception:
        pass
    return total_val, total_cost, total_fees, enriched


def extract_categories(all_rows):
    col_var = col_prevu = col_actuel = row_start = -1
    for i, row in enumerate(all_rows):
        if i >= 65:
            break
        for j, cell in enumerate(row):
            if "charges variables" in str(cell).strip().lower():
                row_str = " ".join(str(x).lower() for x in row)
                if any(x in row_str for x in ["prévu", "actuel", "réel"]):
                    col_var, row_start = j, i
                    for k in range(j + 1, len(row)):
                        v = str(row[k]).strip().lower()
                        if "prévu" in v or "prevu" in v:
                            col_prevu = k
                        elif any(x in v for x in ["actuel", "réel", "reel"]):
                            col_actuel = k
                    break
        if col_var != -1:
            break

    categories = []
    if col_var != -1:
        for i in range(row_start + 1, min(row_start + 20, len(all_rows))):
            row = all_rows[i]
            cat = str(cell_at(row, col_var)).strip()
            if "total" in cat.lower() or not cat:
                break
            if cat.lower() == "nan" or "vacance" in cat.lower():
                continue
            categories.append({"name": cat, "prevu": parse_amount(cell_at(row, col_prevu)), "reel": parse_amount(cell_at(row, col_actuel))})
    return categories


def extract_expenses(all_rows):
    history_start = -1
    for i, row in enumerate(all_rows):
        if len(row) > 1 and str(row[0]).strip().lower() == "date":
            row_str = " ".join(str(c).lower() for c in row)
            if "lieu" in row_str or "merchant" in row_str:
                history_start = i + 1
                break

    expenses = []
    if history_start != -1:
        for i in range(history_start, min(history_start + 90, len(all_rows))):
            row = all_rows[i]
            if len(row) > 0 and str(row[0]).strip().lower() == "date":
                break
            if len(row) > 4 and str(row[0]).strip() not in ["", "nan"]:
                if "total" in str(row[0]).lower():
                    continue
                expenses.append({
                    "Date": row[0], "Merchant": row[1], "Amount": parse_amount(row[2]),
                    "Note": row[3], "Category": row[4], "sheet_row": i + 1,
                })
    return history_start, expenses


def extract_daily_summary(all_rows, expenses):
    daily = []
    if len(all_rows) > 149:
        for row in all_rows[149:250]:
            if len(row) >= 2:
                date_val = str(row[0]).strip()
                low = date_val.lower()
                if date_val and low != "date" and "total" not in low and "dépense" not in low and "depense" not in low:
                    daily.append({"Date": date_val, "Amount": parse_amount(row[1])})
    elif expenses:
        daily = [{"Date": e["Date"], "Amount": e["Amount"]} for e in expenses]
    return daily


def extract_net_worth_parts(all_rows, prevu_var, reel_var):
    cash = parse_amount(all_rows[41][9]) if len(all_rows) > 41 and len(all_rows[41]) > 9 else 0.0
    if cash == 0.0:
        cash = prevu_var - reel_var

    emergency = parse_amount(all_rows[9][2]) if len(all_rows) > 9 and len(all_rows[9]) > 2 else 0.0
    for r in all_rows[:15]:
        if len(r) > 3 and "emergency fund" in str(r[0]).lower():
            reel_ef, prevu_ef, debut_ef = parse_amount(r[3]), parse_amount(r[2]), parse_amount(r[1])
            emergency = reel_ef if reel_ef > 0 else (prevu_ef if prevu_ef > 0 else debut_ef)
            break

    debts = parse_amount(all_rows[58][9]) if len(all_rows) > 58 and len(all_rows[58]) > 9 else 0.0
    if debts == 0.0:
        try:
            for r in fetch_worksheet_data(SHEET_ID, "Data")[3:7]:
                if len(r) > 1:
                    debts += parse_amount(r[1])
        except Exception:
            pass
    return cash, emergency, debts


# =============================================================================
# 4. NAVIGATION : mois actif (cycle comptable du 15 au 15) + synchro auto
# =============================================================================
months_map = {"January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril", "May": "Mai", "June": "Juin",
              "July": "Juillet", "August": "Août", "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre"}
months_list_en = list(months_map.keys())
now = datetime.now()
CYCLE_START_DAY = 15

default_idx = (now.month - 2) if now.day < CYCLE_START_DAY else (now.month - 1)
if default_idx < 0:
    default_idx = 11

st.session_state.setdefault("active_month_en", months_list_en[default_idx])
st.session_state.setdefault("sidebar_month_picker", st.session_state.active_month_en)
st.session_state.setdefault("header_month_picker", st.session_state.active_month_en)


def sync_month(source_key):
    """Appelé quand un sélecteur de mois change : met à jour l'autre sélecteur ET recharge les données."""
    chosen = st.session_state[source_key]
    st.session_state.active_month_en = chosen
    st.session_state.sidebar_month_picker = chosen
    st.session_state.header_month_picker = chosen
    st.cache_data.clear()


st.sidebar.selectbox("Select Month", months_list_en, key="sidebar_month_picker",
                     on_change=sync_month, args=("sidebar_month_picker",))
active_month_en = st.session_state.active_month_en
selected_month = months_map[active_month_en]

curr_m_num = months_list_en.index(active_month_en) + 1
curr_y_num = now.year - 1 if (now.month == 1 and now.day < CYCLE_START_DAY and curr_m_num == 12) else now.year
period_start_dt = datetime(curr_y_num, curr_m_num, CYCLE_START_DAY)
next_m_num = curr_m_num + 1 if curr_m_num < 12 else 1
next_y_num = curr_y_num if curr_m_num < 12 else curr_y_num + 1
period_end_dt = datetime(next_y_num, next_m_num, CYCLE_START_DAY)

available_titles = fetch_sheet_titles(SHEET_ID)
matched_title = next((s for s in available_titles if selected_month.lower() in s.lower()), None)
if not matched_title:
    matched_title = next((s for s in available_titles if s.lower() not in ["data", "portfolio", "investment", "old factures"]), available_titles[0])
    st.sidebar.warning(f"Onglet '{selected_month}' introuvable. Affichage de '{matched_title}'.")
ws = sh.worksheet(matched_title)

# =============================================================================
# 5. CALCULS
# =============================================================================
all_rows = fetch_worksheet_data(SHEET_ID, matched_title)
category_progress = extract_categories(all_rows)
prevu_var = sum(c["prevu"] for c in category_progress)
reel_var = sum(c["reel"] for c in category_progress)
row_history_start, raw_expenses = extract_expenses(all_rows)
daily_summary_data = extract_daily_summary(all_rows, raw_expenses)

total_portfolio_value, total_cost_basis, total_fees, enriched_portfolio_data = fetch_portfolio_data(SHEET_ID)
cash_remaining, emergency_fund, total_debts = extract_net_worth_parts(all_rows, prevu_var, reel_var)
total_net_worth = cash_remaining + emergency_fund + total_portfolio_value - total_debts

# =============================================================================
# 6. PAGES
# =============================================================================
@st.dialog("New expense")
def add_expense_dialog():
    """Pop-up de saisie rapide : montant -> commerçant -> catégorie (pastilles) -> confirmer."""
    with st.form("add_expense_form", clear_on_submit=True, border=False):
        amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f", value=None, placeholder="0.00")
        lib = st.text_input("Merchant", placeholder="Apple, Migros...")
        cat_en = st.pills("Category", list(FORM_CATS.keys()), selection_mode="single", default="Groceries")
        d_col, n_col = st.columns([1, 1.4])
        with d_col:
            expense_date = st.date_input("Date", value=datetime.now())
        with n_col:
            note = st.text_input("Note", placeholder="Optional")
        submitted = st.form_submit_button("CONFIRM TRANSACTION", width="stretch")

    if submitted:
        if not lib or amt is None or amt <= 0:
            st.warning("Add an amount and a merchant.")
            return
        col_b = ws.col_values(2)
        start_row = (row_history_start + 1) if row_history_start != -1 else 60
        target = start_row
        for r in range(start_row, 149):
            if r > len(col_b) or not str(col_b[r - 1]).strip():
                target = r
                break
        ws.update(values=[[expense_date.strftime("%d/%m/%Y"), lib, amt, note, FORM_CATS[cat_en or "Groceries"]]],
                  range_name=f"A{target}:E{target}", value_input_option="USER_ENTERED")
        st.toast("Expense added! ✅")
        st.cache_data.clear()
        time.sleep(1.0)
        st.rerun()


tab_dashboard, tab_investments = st.tabs(["📊 Dashboard", "📈 Investments"])

# ---------------------------------- DASHBOARD --------------------------------
with tab_dashboard:
    restant = prevu_var - reel_var
    percent = min(reel_var / prevu_var, 1.0) if prevu_var > 0 else 0.0

    period_badge = f"{period_start_dt.strftime('%d/%m/%Y')} → {period_end_dt.strftime('%d/%m/%Y')}"
    st.markdown(
        f"<div style='text-align:center; margin-bottom:15px;'>"
        f"<div class='page-title'>OVERVIEW</div>"
        f"<div class='page-sub'>{active_month_en} {curr_y_num} • <b>{matched_title}</b></div>"
        f"<div class='page-cycle'>Cycle: {period_badge}</div></div>",
        unsafe_allow_html=True,
    )

    # Sélecteur de mois : la synchro des données est automatique (callback sync_month)
    _, picker_col, _ = st.columns([1.2, 2.2, 1.2])
    with picker_col:
        st.selectbox("Accounting Period", months_list_en, key="header_month_picker",
                     on_change=sync_month, args=("header_month_picker",), label_visibility="collapsed")

    hero_lvl = level(percent, warn=0.66, crit=0.80)
    st.markdown(hero_html(
        f"SPENT <b>{format_chf(reel_var)} CHF</b>",
        f"PLANNED <b>{format_chf(prevu_var)} CHF</b>",
        f"{format_chf(restant)} <small>CHF</small>",
        extra_html=progress_bar_html(percent, hero_lvl) + banner_html(percent),
    ), unsafe_allow_html=True)

    if st.button("＋ ADD NEW EXPENSE", key="btn_add_expense"):
        add_expense_dialog()

    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown(title_html("Category Breakdown", size=20), unsafe_allow_html=True)
        for cat in sorted(category_progress, key=lambda x: (x["reel"] > 0, x["prevu"]), reverse=True):
            st.markdown(category_card_html(cat["name"], cat["reel"], cat["prevu"]), unsafe_allow_html=True)

    with col_right:
        st.markdown(title_html("Recent Activity", size=20, margin="0 0 12px 0"), unsafe_allow_html=True)
        f_col1, f_col2 = st.columns([1.4, 1])
        with f_col1:
            search_query = st.text_input("Search", placeholder="🔍 Filter merchant, note...", label_visibility="collapsed", key="act_search")
        with f_col2:
            selected_filter_cat = st.selectbox("Filter Category", ["All"] + list(FORM_CATS.keys()), label_visibility="collapsed", key="act_cat_filter")

        if raw_expenses:
            filtered = raw_expenses[::-1]
            if selected_filter_cat != "All":
                target_fr = FORM_CATS[selected_filter_cat].lower()
                filtered = [e for e in filtered if target_fr in str(e["Category"]).strip().lower() or str(e["Category"]).strip().lower() in target_fr]
            if search_query:
                q = search_query.strip().lower()
                filtered = [e for e in filtered if q in str(e["Merchant"]).lower() or q in str(e.get("Note", "")).lower()
                            or q in str(e["Date"]).lower() or q in str(e["Amount"]).lower()]

            with st.container(height=420, border=False):
                if filtered:
                    for e in filtered:
                        st.markdown(transaction_card_html(e["Date"], e["Merchant"], format_chf(e["Amount"]) + " CHF", e["Category"], e.get("Note", "")),
                                    unsafe_allow_html=True)
                else:
                    st.caption("No matching transactions found.")

            last_exp = raw_expenses[-1]
            with st.expander(f"🗑️ Undo last entry ({last_exp['Merchant']} • {format_chf(last_exp['Amount'])} CHF)", expanded=False):
                st.caption(f"Row #{last_exp['sheet_row']} in '{matched_title}' ({last_exp['Date']})")
                if st.button("CONFIRM DELETE LAST ENTRY", key="btn_undo_last"):
                    row_idx = last_exp["sheet_row"]
                    ws.update(values=[["", "", "", "", ""]], range_name=f"A{row_idx}:E{row_idx}", value_input_option="USER_ENTERED")
                    st.toast("Last transaction removed! 🗑️")
                    st.cache_data.clear()
                    time.sleep(1.0)
                    st.rerun()
        else:
            st.caption("No transactions logged for this period yet.")

    st.divider()

    # ---- Spending trend ----
    with st.container(key="glass_trend"):
        st.markdown(title_html("Spending Trend", "ph-trend-up", margin="0 0 15px 0"), unsafe_allow_html=True)
        fig = go.Figure()
        if daily_summary_data:
            df = pd.DataFrame(daily_summary_data)
            df["DateObj"] = df["Date"].apply(lambda x: parse_trend_date(x, curr_y_num, start_month=curr_m_num))
            df = df.dropna(subset=["DateObj"]).groupby("DateObj", as_index=False)["Amount"].sum().sort_values("DateObj")

            if not df.empty:
                period_days = max((period_end_dt - period_start_dt).days, 1)
                ideal_daily = prevu_var / period_days if prevu_var > 0 else 0
                df["Cumulative"] = df["Amount"].cumsum()
                df["Days_Passed"] = ((df["DateObj"] - period_start_dt).dt.days + 1).clip(lower=0, upper=period_days)
                df["Ideal"] = df["Days_Passed"] * ideal_daily
                df["Safe"] = df[["Cumulative", "Ideal"]].min(axis=1)
                df["Over"] = (df["Cumulative"] - df["Ideal"]).clip(lower=0)

                last_idx = df[df["Amount"] > 0].index.max()
                df_plot = df.loc[:last_idx] if pd.notna(last_idx) else df

                fig.add_trace(go.Scatter(x=[period_start_dt, period_end_dt], y=[0, prevu_var], mode="lines",
                                         name="Ideal Budget Limit (15 → 15)", line=dict(color=TOKENS["text-dim"], width=2, dash="dash")))
                fig.add_trace(go.Scatter(x=df_plot["DateObj"], y=df_plot["Safe"], mode="lines", stackgroup="one", name="On Track",
                                         line=dict(color=TOKENS["green-600"], width=0), fillcolor="rgba(16, 185, 129, 0.3)"))
                fig.add_trace(go.Scatter(x=df_plot["DateObj"], y=df_plot["Over"], mode="lines", stackgroup="one", name="Overbudget",
                                         line=dict(color=TOKENS["red-600"], width=0), fillcolor="rgba(225, 29, 72, 0.4)"))
                fig.add_trace(go.Scatter(x=df_plot["DateObj"], y=df_plot["Cumulative"], mode="lines", name="Actual Spend",
                                         line=dict(color=TOKENS["text"], width=2), showlegend=False))
        style_fig(fig, 300, showlegend=True,
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=TOKENS["text"])))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # ---- Distribution ----
    with st.container(key="glass_distribution"):
        st.markdown(title_html("Distribution", "ph-chart-donut", margin="0 0 5px 0"), unsafe_allow_html=True)
        spent = [c for c in category_progress if c["reel"] > 0]
        if spent:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[c["name"] for c in spent], values=[c["reel"] for c in spent], hole=0.75,
                marker=dict(colors=["#3B82F6", "#60A5FA", "#93C5FD", "#1D4ED8", "#2563EB", "#1E3A8A"]),
                textinfo="label+percent", textfont=dict(color="#FFFFFF", size=12), hoverinfo="label+value",
            )])
            fig_pie.update_layout(
                showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                annotations=[dict(text=f"<b>{format_chf(reel_var)}</b><br>CHF", x=0.5, y=0.5, font_size=24, showarrow=False, font=dict(color="#FFFFFF"))],
            )
            st.plotly_chart(fig_pie, width="stretch", config={"displayModeBar": False})
        else:
            st.caption("No spending yet for this period.")

    # ---- Net worth ----
    st.markdown(title_html("Net Worth Snapshot", "ph-scales", margin="50px 0 20px 0"), unsafe_allow_html=True)
    st.markdown(net_worth_html(total_net_worth, cash_remaining, emergency_fund, total_portfolio_value, total_debts), unsafe_allow_html=True)

    # ---- Evolution tracker (données simulées) ----
    with st.container(key="glass_evolution"):
        st.markdown(title_html("Evolution Tracker", "ph-chart-line-up", size=18, margin="0 0 5px 0"), unsafe_allow_html=True)
        st.caption("Simulated data based on current net worth. Connect to a history tab later.")
        mock_dates = [(now.replace(day=1) - timedelta(days=30 * i)).strftime("%b %Y") for i in range(5, -1, -1)]
        mock_values = [total_net_worth * f for f in (0.75, 0.78, 0.85, 0.82, 0.93, 1.0)]
        fig_nw = go.Figure(go.Scatter(
            x=mock_dates, y=mock_values, mode="lines+markers", name="Net Worth",
            line=dict(color=TOKENS["green"], width=3, shape="spline"),
            marker=dict(size=8, color="#FFFFFF", line=dict(width=2, color=TOKENS["green"])),
            fill="tozeroy", fillcolor="rgba(52, 211, 153, 0.1)",
        ))
        style_fig(fig_nw, 250, showlegend=False)
        fig_nw.update_yaxes(tickprefix="CHF ")
        st.plotly_chart(fig_nw, width="stretch", config={"displayModeBar": False})

# --------------------------------- INVESTMENTS -------------------------------
with tab_investments:
    st.markdown("<div style='text-align:center; margin:20px 0;'><h2 style='font-size:32px;'>📈 PORTFOLIO TRACKING</h2></div>", unsafe_allow_html=True)

    show_amounts = st.checkbox("Show Real Amounts", value=False)

    perf_total = ((total_portfolio_value - total_cost_basis) / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
    perf_color = TOKENS["green"] if perf_total >= 0 else TOKENS["red"]
    perf_sign = "+" if perf_total >= 0 else ""

    if show_amounts:
        main_value = f"{format_chf(total_portfolio_value)} <small>CHF</small>"
        fees_label = f"Total Fees: {format_chf(total_fees)} CHF"
    else:
        main_value = "*** <small>CHF</small>"
        fees_label = "Total Fees: *** CHF"

    perf_html = (f"PERFORMANCE<br><span style='color:{perf_color}; font-weight:700;'>{perf_sign}{perf_total:.2f}%</span><br>"
                 f"<span style='font-size:11px; color:var(--text-muted);'>{fees_label}</span>")
    st.markdown(hero_html("TOTAL PORTFOLIO", f"<div style='text-align:right;'>{perf_html}</div>", main_value), unsafe_allow_html=True)

    if enriched_portfolio_data:
        st.markdown("".join(investment_card_html(item, show_amounts) for item in enriched_portfolio_data), unsafe_allow_html=True)
    else:
        st.info("💡 The 'Portfolio' tab is missing or empty. Make sure columns 'Nom', 'Ticker / ISIN', 'Amount' (or 'Entry Price'), 'Units', 'Fees', and 'Total Invested' are present.")

st.sidebar.caption(f"Network Secure • Last sync: {datetime.now().strftime('%H:%M')}")
