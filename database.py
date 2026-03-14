# =============================================================================
# database.py — warstwa dostępu do danych
# =============================================================================
# Ten plik jest jedynym miejscem w aplikacji które komunikuje się z Firebase
# Firestore. Żaden inny plik (views/, components/) nie powinien bezpośrednio
# importować firebase_admin ani wywoływać operacji na bazie.
#
# Taka separacja (wzorzec "Data Access Layer") ma dwie zalety:
#   1. Jeśli kiedyś zmienimy bazę danych (np. z Firestore na Supabase) —
#      zmieniamy tylko ten plik, reszta aplikacji zostaje bez zmian.
#   2. Łatwiej znaleźć błędy związane z bazą — zawsze zaczynamy tu.
#
# Struktura Firestore vs SQL:
#   Firestore kolekcja  ≈  tabela SQL
#   Firestore dokument  ≈  wiersz SQL
#   Firestore pole      ≈  kolumna SQL
# =============================================================================

import streamlit as st
import pandas as pd
from firebase_config import get_db

# =============================================================================
# ODCZYT DANYCH
# =============================================================================

def pobierz_produkty():
    """Pobiera wszystkie produkty z Firestore jako listę słowników.

    Odpowiednik SQL:
        SELECT * FROM products ORDER BY timestamp_unix DESC

    Zwraca:
        list[dict] — lista produktów, każdy jako słownik Python
        []         — pusta lista jeśli błąd połączenia lub brak danych
    """
    try:
        db = get_db()

        # order_by sortuje dokumenty po polu timestamp_unix malejąco —
        # najnowsze dodane produkty pojawiają się na górze listy.
        # timestamp_unix to liczba (Unix timestamp) — poprawnie sortowalny,
        # w przeciwieństwie do timestamp który jest stringiem "DD.MM.YYYY HH:MM:SS"
        docs = db.collection("products").order_by(
            "timestamp_unix", direction="DESCENDING"
        ).stream()
        
        # Iterujemy po dokumentach i konwertujemy każdy na słownik.
        # doc.to_dict() zwraca pola dokumentu, ale bez jego ID —
        # dlatego ręcznie dodajemy "id": doc.id
        produkty = []
        for doc in docs:
            produkt = doc.to_dict()
            produkt["id"] = doc.id  # Firestore ID dokumentu (unikalny string)
            produkty.append(produkt)

        return produkty

    except Exception as e:
        # Zamiast crashować aplikację — pokazujemy czytelny błąd użytkownikowi
        st.error(f"Błąd połączenia z bazą danych: {e}")
        return []


def pobierz_produkty_df():
    """Pobiera wszystkie produkty jako pandas DataFrame.

    DataFrame jest wygodniejszy niż lista słowników gdy chcemy:
    - filtrować (df[df["status"] == "sprzedany"])
    - sortować (df.sort_values("cena_zakupu"))
    - agregować (df.groupby("kategoria").sum())

    Zwraca:
        pd.DataFrame — produkty jako tabela
        pd.DataFrame() — pusty DataFrame jeśli brak danych lub błąd
    """
    produkty = pobierz_produkty()
    if not produkty:
        return pd.DataFrame()
    return pd.DataFrame(produkty)

# =============================================================================
# ZAPIS DANYCH
# =============================================================================

def dodaj_produkt(produkt):
    """Dodaje nowy produkt do Firestore i zwraca jego wygenerowane ID.

    Odpowiednik SQL:
        INSERT INTO products VALUES (...)
        RETURNING id

    Firestore samo generuje unikalne ID dokumentu (długi losowy string) —
    nie musimy go podawać, w odróżnieniu od AUTO_INCREMENT w SQL.

    Args:
        produkt (dict): słownik z danymi produktu

    Zwraca:
        str  — ID nowo utworzonego dokumentu
        None — jeśli błąd zapisu
    """
    try:
        db = get_db()

        # collection.add() dodaje nowy dokument i zwraca krotkę (timestamp, DocumentReference)
        # Nas interesuje tylko DocumentReference (indeks [1]) i jego .id
        doc_ref = db.collection("products").add(produkt)
        return doc_ref[1].id

    except Exception as e:
        st.error(f"Nie udało się dodać produktu: {e}")
        return None

# =============================================================================
# AKTUALIZACJA DANYCH
# =============================================================================

def aktualizuj_produkt(produkt_id, dane):
    """Aktualizuje wybrane pola istniejącego dokumentu w Firestore.

    Odpowiednik SQL:
        UPDATE products SET pole1=val1, pole2=val2 WHERE id = produkt_id

    Ważne: update() nadpisuje tylko podane pola — pozostałe pola dokumentu
    zostają bez zmian. To różni się od set() który zastąpiłby cały dokument.

    Args:
        produkt_id (str): Firestore ID dokumentu do zaktualizowania
        dane (dict): słownik z polami do zaktualizowania i ich nowymi wartościami
    """
    try:
        db = get_db()

        # document() zwraca referencję do konkretnego dokumentu po jego ID
        # update() aktualizuje tylko podane pola, reszta dokumentu zostaje
        db.collection("products").document(produkt_id).update(dane)

    except Exception as e:
        st.error(f"Nie udało się zaktualizować produktu: {e}")

# =============================================================================
# USUWANIE DANYCH
# =============================================================================

def usun_produkt(produkt_id):
    """Trwale usuwa dokument z Firestore.

    Odpowiednik SQL:
        DELETE FROM products WHERE id = produkt_id

    Uwaga: operacja nieodwracalna — Firestore nie ma kosza ani soft delete.
    Dlatego w UI przed usunięciem pokazujemy dialog z potwierdzeniem.

    Args:
        produkt_id (str): Firestore ID dokumentu do usunięcia
    """
    try:
        db = get_db()
        db.collection("products").document(produkt_id).delete()

    except Exception as e:
        st.error(f"Nie udało się usunąć produktu: {e}")

# =============================================================================
# SYNCHRONIZACJA UI
# =============================================================================

def aktualizuj_session_state(produkt_id, dane):
    """Aktualizuje lokalny DataFrame w session_state po zmianie w Firestore.

    Po każdej operacji zapisu do Firestore (aktualizuj_produkt, usun_produkt)
    musimy też zaktualizować lokalną kopię danych w session_state —
    inaczej UI pokazywałoby stare dane do momentu ręcznego odświeżenia.

    Wzorzec "optimistic update":
        1. Zapisz do Firestore (trwały zapis w chmurze)
        2. Zaktualizuj session_state (natychmiastowa aktualizacja UI)
    Dzięki temu UI reaguje natychmiast, bez czekania na odpowiedź z Firebase.

    Zawsze wywołuj tę funkcję zaraz po aktualizuj_produkt():
        aktualizuj_produkt(id, dane)
        aktualizuj_session_state(id, dane)

    Args:
        produkt_id (str): ID produktu do zaktualizowania w session_state
        dane (dict): te same dane które zostały zapisane do Firestore
    """

    # maska to seria True/False — True tylko dla wiersza z pasującym ID
    # Odpowiednik SQL: WHERE id = produkt_id
    maska = st.session_state.products_df["id"] == produkt_id

    # Aktualizujemy każde pole w DataFrame używając .loc[maska, kolumna]
    # To pandas odpowiednik UPDATE SET dla konkretnego wiersza
    for klucz, wartosc in dane.items():
        st.session_state.products_df.loc[maska, klucz] = wartosc