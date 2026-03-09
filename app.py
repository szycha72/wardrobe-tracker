import streamlit as st
import datetime
from database import pobierz_produkty_df
from views.lista import pokaz_liste
from views.formularz import pokaz_formularz
from views.dashboard import pokaz_dashboard
from views.eksport import pokaz_eksport

st.set_page_config(
    page_title="Apka Kingusi",
    page_icon="👗",
    layout="centered"
)

# Inicjalizacja session_state
if "products_df" not in st.session_state:
    st.session_state.products_df = pobierz_produkty_df()

# Nagłówek
st.title("👗 Apka Kingusi")

if st.button("🔄 Odśwież dane"):
    st.session_state.products_df = pobierz_produkty_df()
    st.rerun()

# Nawigacja
tab_lista, tab_dodaj, tab_dashboard, tab_eksport = st.tabs([
    "📋 Lista produktów",
    "➕ Dodaj produkt",
    "📊 Dashboard",
    "📥 Eksport"
])

with tab_lista:
    pokaz_liste()

with tab_dodaj:
    pokaz_formularz()

with tab_dashboard:
    pokaz_dashboard()

with tab_eksport:
    pokaz_eksport()