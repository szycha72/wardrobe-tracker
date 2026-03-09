from firebase_config import get_db
import pandas as pd

def pobierz_produkty():
    """Odpowiednik: SELECT * FROM products ORDER BY data_dodania DESC"""
    db = get_db()
    docs = db.collection("products").order_by(
    "timestamp_unix", direction="DESCENDING"
    ).stream()
    
    produkty = []
    for doc in docs:
        produkt = doc.to_dict()
        produkt["id"] = doc.id  # Firestore ID dokumentu
        produkty.append(produkt)
    
    return produkty


def dodaj_produkt(produkt):
    """Odpowiednik: INSERT INTO products VALUES (...)"""
    db = get_db()
    # add() samo generuje unikalne ID dokumentu
    doc_ref = db.collection("products").add(produkt)
    return doc_ref[1].id  # zwracamy wygenerowane ID


def aktualizuj_produkt(produkt_id, dane):
    """Odpowiednik: UPDATE products SET ... WHERE id = produkt_id"""
    db = get_db()
    db.collection("products").document(produkt_id).update(dane)

def pobierz_produkty_df():
    """Zwraca produkty jako pandas DataFrame — wygodniejsze do filtrowania i sortowania"""
    produkty = pobierz_produkty()
    if not produkty:
        return pd.DataFrame()
    return pd.DataFrame(produkty)

def usun_produkt(produkt_id):
    """Odpowiednik: DELETE FROM products WHERE id = produkt_id"""
    db = get_db()
    db.collection("products").document(produkt_id).delete()