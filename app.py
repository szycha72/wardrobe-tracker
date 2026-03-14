# =============================================================================
# app.py — główny plik aplikacji
# =============================================================================
# To jest punkt wejścia całej aplikacji — jedyne miejsce które Streamlit
# uruchamia bezpośrednio komendą: streamlit run app.py
#
# Odpowiedzialność tego pliku jest celowo ograniczona do trzech rzeczy:
#   1. Konfiguracja strony
#   2. Inicjalizacja danych przy starcie
#   3. Definicja nawigacji (zakładki) i wywołanie widoków
#
# Cała logika biznesowa i UI jest w folderach views/ i components/
# =============================================================================

import streamlit as st
import datetime
from database import pobierz_produkty_df
from views.lista import pokaz_liste
from views.formularz import pokaz_formularz
from views.dashboard import pokaz_dashboard
from views.eksport import pokaz_eksport

# -----------------------------------------------------------------------------
# KONFIGURACJA STRONY
# -----------------------------------------------------------------------------
# set_page_config musi być pierwszym wywołaniem Streamlit w skrypcie —
# ustawia tytuł zakładki przeglądarki, ikonę i szerokość layoutu.
# "centered" oznacza że treść ma maksymalną szerokość ~700px — lepsze na telefonie
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Apka Kingusi",
    page_icon="👗",
    layout="centered"
)

# -----------------------------------------------------------------------------
# INICJALIZACJA DANYCH
# -----------------------------------------------------------------------------
# session_state to słownik który persystuje między "rundami" Streamlita.
# Streamlit uruchamia cały skrypt od nowa przy każdej interakcji użytkownika,
# więc bez session_state dane znikałyby przy każdym kliknięciu.
#
# Wzorzec "if X not in session_state" gwarantuje że dane pobieramy z Firebase
# tylko raz — przy pierwszym załadowaniu aplikacji, nie przy każdej interakcji.
# -----------------------------------------------------------------------------

if "products_df" not in st.session_state:
    st.session_state.products_df = pobierz_produkty_df()

# -----------------------------------------------------------------------------
# NAGŁÓWEK I ODŚWIEŻANIE
# -----------------------------------------------------------------------------
# Przycisk odświeżania jest potrzebny gdy aplikacja jest używana na dwóch
# urządzeniach jednocześnie (telefon + komputer) — każde urządzenie ma
# własny session_state i nie widzi zmian wprowadzonych na drugim urządzeniu.
# Kliknięcie przycisku wymusza ponowne pobranie danych z Firebase.
# -----------------------------------------------------------------------------

st.title("👗 Apka Kingusi")

if st.button("🔄 Odśwież dane"):
    st.session_state.products_df = pobierz_produkty_df()
    st.rerun()

# -----------------------------------------------------------------------------
# NAWIGACJA — ZAKŁADKI
# -----------------------------------------------------------------------------
# st.tabs tworzy poziomą nawigację zakładkową.
# Każda zakładka wywołuje funkcję z odpowiedniego pliku w views/ —
# dzięki temu ten plik pozostaje krótki i czytelny.
# -----------------------------------------------------------------------------
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