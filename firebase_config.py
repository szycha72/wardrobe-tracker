import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def get_db():
    # Inicjalizujemy połączenie tylko raz — jeśli już istnieje, pomijamy
    # To ważne bo Streamlit uruchamia cały skrypt przy każdej interakcji
    # i bez tego warunku próbowałby łączyć się z Firebase setki razy
    if not firebase_admin._apps:
        cert = dict(st.secrets["firebase"])
        cert["private_key"] = cert["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cert)
        firebase_admin.initialize_app(cred)
    
    return firestore.client()