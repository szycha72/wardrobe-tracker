# =============================================================================
# firebase_config.py — konfiguracja połączenia z Firebase
# =============================================================================
# Ten plik odpowiada wyłącznie za jedno zadanie: zainicjalizowanie połączenia
# z Firebase i zwrócenie klienta bazy danych Firestore.
#
# Jest importowany tylko przez database.py — żaden inny plik nie powinien
# bezpośrednio używać tego modułu.
# =============================================================================

import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def get_db():
    """Zwraca klienta Firestore — inicjalizuje połączenie jeśli jeszcze nie istnieje.

    Firebase Admin SDK wymaga jednorazowej inicjalizacji przy starcie aplikacji.
    Streamlit uruchamia cały skrypt przy każdej interakcji użytkownika, więc
    bez zabezpieczenia "if not firebase_admin._apps" próbowałby inicjalizować
    połączenie setki razy — co skończyłoby się błędem "app already exists".

    Klucze do Firebase są przechowywane w .streamlit/secrets.toml (lokalnie)
    lub w panelu Streamlit Cloud (produkcja) — nigdy w kodzie źródłowym.
    """

    # -----------------------------------------------------------------------------
    # INICJALIZACJA POŁĄCZENIA (tylko przy pierwszym wywołaniu)
    # -----------------------------------------------------------------------------
    # firebase_admin._apps to słownik aktywnych połączeń — jeśli jest pusty,
    # oznacza że połączenie jeszcze nie zostało nawiązane i trzeba je zainicjować.
    # -----------------------------------------------------------------------------

    if not firebase_admin._apps:

        # Pobieramy credentials z secrets.toml jako słownik Pythona
        cert = dict(st.secrets["firebase"])

        # private_key w pliku secrets.toml ma znaki \n jako dosłowny tekst
        # (backslash + n). Firebase potrzebuje prawdziwych znaków nowej linii.
        # Ta linijka zamienia "\n" (2 znaki) na rzeczywisty znak nowej linii.
        cert["private_key"] = cert["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(cert)
        firebase_admin.initialize_app(cred)

    # -----------------------------------------------------------------------------
    # ZWRACANIE KLIENTA FIRESTORE
    # -----------------------------------------------------------------------------
    # firestore.client() zwraca obiekt przez który wykonujemy wszystkie operacje
    # na bazie danych — odczyt, zapis, aktualizację, usuwanie.
    # Ten obiekt jest importowany i używany wyłącznie w database.py
    # -----------------------------------------------------------------------------

    return firestore.client()