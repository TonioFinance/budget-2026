# --- ADD TRANSACTION ---
col_form, col_hist = st.columns([1.2, 1])

# English UI Categories mapping to French GSheet data
form_cat_map = {
    "Groceries": "Courses", 
    "Dining": "Sorties/Restos", 
    "Transport": "Transport", 
    "Leisure": "Loisirs", 
    "Unexpected": "Imprévus", 
    "Shopping": "Shopping", 
    "Hygiene": "Hygiène"
}

with col_form:
    with st.form("new_exp", clear_on_submit=True):
        st.markdown("<h4 style='color: #FFFFFF; margin-bottom: 15px;'>➕ New Expense</h4>", unsafe_allow_html=True)
        lib = st.text_input("Merchant / Location", placeholder="e.g. Migros, Apple...")
        amt = st.number_input("Amount (CHF)", min_value=0.0, step=0.1, format="%.2f")
        cat_en = st.selectbox("Category", list(form_cat_map.keys()))
        note = st.text_input("Note (optional)")
        
        st.write("")
        if st.form_submit_button("ADD EXPENSE") and lib and amt > 0:
            cat_fr = form_cat_map[cat_en]
            
            # --- NOUVELLE LOGIQUE D'INSCRIPTION CIBLÉE ---
            # 1. On récupère toutes les valeurs de la colonne B (Marchand) pour trouver la première ligne vide
            # On commence à regarder à partir de la ligne 58 (index 57)
            col_b_values = ws.col_values(2) # Colonne B
            
            # On cherche la première ligne vide entre 58 et 100
            target_row = 58
            for r in range(58, 100):
                # Si la cellule est vide ou inexistante dans la liste
                if r > len(col_b_values) or not col_b_values[r-1].strip():
                    target_row = r
                    break
            
            # 2. On prépare la ligne
            new_data = [datetime.now().strftime("%Y-%m-%d"), lib, amt, note, cat_fr]
            
            # 3. On utilise 'update' au lieu de 'append_row' pour viser la case précise (A:E)
            range_to_update = f"A{target_row}:E{target_row}"
            ws.update(range_name=range_to_update, values=[new_data], value_input_option="USER_ENTERED")
            
            st.success(f"✅ Transaction added to row {target_row}!")
            st.cache_resource.clear()
            st.rerun()
