# =============================================================================
# views/eksport.py — zakładka "Eksport"
# =============================================================================
# Ten plik odpowiada za generowanie i pobieranie pliku XLSX z danymi.
#
# Kluczowa techniczna decyzja: plik jest generowany w pamięci (io.BytesIO)
# zamiast zapisywany na dysk. Jest to konieczne bo Streamlit Cloud
# nie gwarantuje trwałości systemu plików między sesjami.
#
# Plik XLSX ma dwa arkusze:
#   1. "Produkty" — lista produktów z czytelnie nazwanymi kolumnami
#   2. "Podsumowanie" — zysk per kategoria (tylko dla sprzedanych)
# =============================================================================

import streamlit as st
import pandas as pd
import datetime
import io


def pokaz_eksport():

    st.subheader("Eksport danych")

    df = st.session_state.products_df

    if df.empty:
        st.info("Brak danych do eksportu.")
        return

    # -------------------------------------------------------------------------
    # WYBÓR ZAKRESU EKSPORTU
    # -------------------------------------------------------------------------
    # Użytkownik wybiera czy eksportuje wszystkie produkty czy tylko
    # te z konkretnym statusem
    # -------------------------------------------------------------------------
    zakres = st.radio(
        "Co eksportować?",
        ["Wszystkie produkty", "Tylko kupione", "Tylko wystawione", "Tylko sprzedane"],
        horizontal=True
    )

    if zakres == "Tylko kupione":
        df_eksport = df[df["status"] == "kupiony"].copy()
    elif zakres == "Tylko wystawione":
        df_eksport = df[df["status"] == "wystawiony"].copy()
    elif zakres == "Tylko sprzedane":
        df_eksport = df[df["status"] == "sprzedany"].copy()
    else:
        df_eksport = df.copy()
    
    # -------------------------------------------------------------------------
    # PRZYGOTOWANIE DANYCH DO EKSPORTU
    # -------------------------------------------------------------------------

    # Usuwamy kolumny techniczne które nie są potrzebne użytkownikowi —
    # id to wewnętrzny klucz Firestore, timestamp i timestamp_unix to
    # pola używane tylko przez aplikację do sortowania
    kolumny_do_usuniecia = ["id", "timestamp", "timestamp_unix"]
    df_eksport = df_eksport.drop(
        columns=[k for k in kolumny_do_usuniecia if k in df_eksport.columns]
    )

    # Dodajemy kolumnę "zysk" tylko dla sprzedanych produktów —
    # .where() ustawia wartość tylko tam gdzie warunek jest True,
    # dla pozostałych wierszy wstawia NaN (puste pole w Excelu)
    if "cena_sprzedazy" in df_eksport.columns:
        df_eksport["zysk"] = (
            df_eksport["cena_sprzedazy"] - df_eksport["cena_zakupu"]
        ).where(df_eksport["status"] == "sprzedany")

    # Zmieniamy nazwy kolumn z technicznych (snake_case) na czytelne po polsku
    nazwy_kolumn = {
        "nazwa": "Nazwa",
        "kategoria": "Kategoria",
        "opis": "Opis",
        "miejsce_zakupu": "Miejsce zakupu",
        "dowod_zakupu": "Dowód zakupu",
        "data_zakupu": "Data zakupu",
        "cena_zakupu": "Cena zakupu (zł)",
        "status": "Status",
        "cena_sprzedazy": "Cena sprzedaży (zł)",
        "data_sprzedazy": "Data sprzedaży",
        "gdzie_sprzedane": "Gdzie sprzedane",
        "zysk": "Zysk (zł)"
    }

    # Zmieniamy tylko te kolumny które faktycznie istnieją w DataFrame
    df_eksport = df_eksport.rename(
        columns={k: v for k, v in nazwy_kolumn.items() if k in df_eksport.columns}
    )

    st.caption(f"Liczba wierszy do eksportu: {len(df_eksport)}")

    # -------------------------------------------------------------------------
    # GENEROWANIE PLIKU XLSX W PAMIĘCI
    # -------------------------------------------------------------------------
    # io.BytesIO() tworzy "wirtualny plik" w pamięci RAM —
    # zamiast zapisywać na dysk, trzymamy bajty pliku w zmiennej.
    # pd.ExcelWriter zapisuje dane do tego wirtualnego pliku.
    # buffer.getvalue() zwraca bajty gotowe do pobrania przez przeglądarkę.
    # -------------------------------------------------------------------------
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

        # Arkusz 1 — lista produktów
        df_eksport.to_excel(writer, index=False, sheet_name="Produkty")

        # Arkusz 2 — podsumowanie per kategoria (zawsze ze wszystkich sprzedanych,
        # niezależnie od wybranego zakresu eksportu)
        sprzedane = df[df["status"] == "sprzedany"].copy()
        if not sprzedane.empty:
            sprzedane["zysk"] = sprzedane["cena_sprzedazy"] - sprzedane["cena_zakupu"]
            podsumowanie = (
                sprzedane.groupby("kategoria")["zysk"]
                .agg(["sum", "count", "mean"])
                .rename(columns={
                    "sum": "Łączny zysk (zł)",
                    "count": "Sprzedanych szt.",
                    "mean": "Średni zysk (zł)"
                })
                .reset_index()
                .rename(columns={"kategoria": "Kategoria"})
            )
            podsumowanie.to_excel(writer, index=False, sheet_name="Podsumowanie")

    # -------------------------------------------------------------------------
    # PRZYCISK POBIERANIA
    # -------------------------------------------------------------------------
    # st.download_button wysyła bajty pliku do przeglądarki jako pobieranie.
    # Nazwa pliku zawiera dzisiejszą datę — łatwo znaleźć w folderze Pobrane.
    # mime= określa typ pliku — przeglądarka wie że to Excel, nie PDF czy ZIP.
    # -------------------------------------------------------------------------
    nazwa_pliku = f"wardrobe_tracker_{datetime.date.today().strftime('%d%m%Y')}.xlsx"
    st.download_button(
        label="📥 Pobierz plik XLSX",
        data=buffer.getvalue(),
        file_name=nazwa_pliku,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )