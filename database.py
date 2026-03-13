import streamlit as st
import pandas as pd
from firebase_config import get_db


def pobierz_produkty():
    """Odpowiednik: SELECT * FROM products ORDER BY timestamp_unix DESC"""
    try:
        db = get_db()
        docs = db.collection("products").order_by(
            "timestamp_unix", direction="DESCENDING"
        ).stream()

        produkty = []
        for doc in docs:
            produkt = doc.to_dict()
            produkt["id"] = doc.id
            produkty.append(produkt)

        return produkty

    except Exception as e:
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return []


def pobierz_produkty_df():
    """Zwraca produkty jako pandas DataFrame — wygodniejsze do filtrowania i sortowania"""
    produkty = pobierz_produkty()
    if not produkty:
        return pd.DataFrame()
    return pd.DataFrame(produkty)


def dodaj_produkt(produkt):
    """Odpowiednik: INSERT INTO products VALUES (...)"""
    try:
        db = get_db()
        doc_ref = db.collection("products").add(produkt)
        return doc_ref[1].id

    except Exception as e:
        st.error(f"Nie udało się dodać produktu: {e}")
        return None


def aktualizuj_produkt(produkt_id, dane):
    """Odpowiednik: UPDATE products SET ... WHERE id = produkt_id"""
    try:
        db = get_db()
        db.collection("products").document(produkt_id).update(dane)

    except Exception as e:
        st.error(f"Nie udało się zaktualizować produktu: {e}")


def usun_produkt(produkt_id):
    """Odpowiednik: DELETE FROM products WHERE id = produkt_id"""
    try:
        db = get_db()
        db.collection("products").document(produkt_id).delete()

    except Exception as e:
        st.error(f"Nie udało się usunąć produktu: {e}")


def aktualizuj_session_state(produkt_id, dane):
    """Aktualizuje lokalny DataFrame w session_state po zmianie w Firestore.
    Wywołuj zawsze po aktualizuj_produkt() żeby UI było zsynchronizowane z bazą.
    """
    maska = st.session_state.products_df["id"] == produkt_id
    for klucz, wartosc in dane.items():
        st.session_state.products_df.loc[maska, klucz] = wartosc