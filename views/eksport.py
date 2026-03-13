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

    kolumny_do_usuniecia = ["id", "timestamp", "timestamp_unix"]
    df_eksport = df_eksport.drop(
        columns=[k for k in kolumny_do_usuniecia if k in df_eksport.columns]
    )

    if "cena_sprzedazy" in df_eksport.columns:
        df_eksport["zysk"] = (
            df_eksport["cena_sprzedazy"] - df_eksport["cena_zakupu"]
        ).where(df_eksport["status"] == "sprzedany")

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
    df_eksport = df_eksport.rename(
        columns={k: v for k, v in nazwy_kolumn.items() if k in df_eksport.columns}
    )

    st.caption(f"Liczba wierszy do eksportu: {len(df_eksport)}")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_eksport.to_excel(writer, index=False, sheet_name="Produkty")

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
    nazwa_pliku = f"wardrobe_tracker_{datetime.date.today().strftime('%d%m%Y')}.xlsx"
    st.download_button(
        label="📥 Pobierz plik XLSX",
        data=buffer.getvalue(),
        file_name=nazwa_pliku,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )