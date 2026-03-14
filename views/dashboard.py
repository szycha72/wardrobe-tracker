# =============================================================================
# views/dashboard.py — zakładka "Dashboard"
# =============================================================================
# Ten plik odpowiada za wyświetlanie statystyk i wykresów.
# Wszystkie obliczenia są wykonywane przez pandas na lokalnym DataFrame —
# żadnych dodatkowych zapytań do Firebase.
#
# Struktura dashboardu:
#   1. Metryki główne (liczba produktów per status)
#   2. Metryki finansowe (zysk, marża, przychód) — tylko jeśli są sprzedane
#   3. Tabela zysku per kategoria
#   4. Wykres sprzedaży w czasie (plotly)
#   5. Zamrożony kapitał (kupione + wystawione)
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px


def pokaz_dashboard():
    st.subheader("Podsumowanie")

    df = st.session_state.products_df

    if df.empty:
        st.info("Brak produktów.")
        return
    
    # -------------------------------------------------------------------------
    # PODZIAŁ NA GRUPY STATUSÓW
    # -------------------------------------------------------------------------
    # Tworzymy trzy osobne DataFrame dla każdego statusu.
    # .copy() jest ważne — bez niego pandas może wyrzucić ostrzeżenie
    # SettingWithCopyWarning gdy próbujemy modyfikować przefiltrowany DataFrame
    # -------------------------------------------------------------------------
    sprzedane = df[df["status"] == "sprzedany"].copy()
    wystawione = df[df["status"] == "wystawiony"].copy()
    kupione = df[df["status"] == "kupiony"].copy()

    # -------------------------------------------------------------------------
    # METRYKI GŁÓWNE — liczba produktów per status
    # -------------------------------------------------------------------------
    # st.metric wyświetla dużą liczbę z etykietą — idealny do KPI
    # -------------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wszystkich", len(df))
    with col2:
        st.metric("Kupionych", len(kupione))
    with col3:
        st.metric("Wystawionych", len(wystawione))
    with col4:
        st.metric("Sprzedanych", len(sprzedane))

    # Jeśli nic nie sprzedano — nie ma sensu pokazywać dalszych statystyk
    if sprzedane.empty:
        st.info("Sprzedaj pierwszy produkt żeby zobaczyć statystyki.")
        return

    st.divider()

    # -------------------------------------------------------------------------
    # OBLICZENIA FINANSOWE
    # -------------------------------------------------------------------------
    # Tworzymy nową kolumnę "zysk" przez odejmowanie dwóch kolumn —
    # pandas wykonuje operację element po elemencie (vectorized operation),
    # bez potrzeby pisania pętli. Odpowiednik SQL:
    #   SELECT cena_sprzedazy - cena_zakupu AS zysk FROM products
    # -------------------------------------------------------------------------
    sprzedane["zysk"] = sprzedane["cena_sprzedazy"] - sprzedane["cena_zakupu"]

    laczny_zysk = sprzedane["zysk"].sum()
    laczny_przychod = sprzedane["cena_sprzedazy"].sum()
    laczny_koszt = sprzedane["cena_zakupu"].sum()

    # Marża = zysk / przychód * 100 — zabezpieczenie przed dzieleniem przez zero
    srednia_marza = (laczny_zysk / laczny_przychod * 100) if laczny_przychod > 0 else 0
    sredni_zysk = sprzedane["zysk"].mean()

    # -------------------------------------------------------------------------
    # METRYKI FINANSOWE
    # -------------------------------------------------------------------------
    col_zysk, col_marza, col_sredni = st.columns(3)
    with col_zysk:
        st.metric("Łączny zysk", f"{laczny_zysk:.0f} zł")
    with col_marza:
        st.metric("Średnia marża", f"{srednia_marza:.0f}%")
    with col_sredni:
        st.metric("Średni zysk / produkt", f"{sredni_zysk:.0f} zł")

    col_przychod, col_koszt = st.columns(2)
    with col_przychod:
        st.metric("Łączny przychód", f"{laczny_przychod:.0f} zł")
    with col_koszt:
        st.metric("Łączny koszt zakupu", f"{laczny_koszt:.0f} zł")

    st.divider()

    # -------------------------------------------------------------------------
    # TABELA ZYSKU PER KATEGORIA
    # -------------------------------------------------------------------------
    # groupby("kategoria") grupuje wiersze po kategorii — odpowiednik SQL:
    #   SELECT kategoria,
    #          SUM(zysk) as laczny_zysk,
    #          COUNT(*) as sprzedanych,
    #          AVG(zysk) as sredni_zysk
    #   FROM sprzedane
    #   GROUP BY kategoria
    #   ORDER BY laczny_zysk DESC
    # -------------------------------------------------------------------------
    st.subheader("Zysk per kategoria")
    zysk_per_kat = (
        sprzedane.groupby("kategoria")["zysk"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "Łączny zysk", "count": "Sprzedanych", "mean": "Średni zysk"})
        .sort_values("Łączny zysk", ascending=False)
        .reset_index()
    )
    # Zaokrąglamy do pełnych złotych i konwertujemy na int (bez ".0")
    zysk_per_kat["Łączny zysk"] = zysk_per_kat["Łączny zysk"].round(0).astype(int)
    zysk_per_kat["Średni zysk"] = zysk_per_kat["Średni zysk"].round(0).astype(int)
    zysk_per_kat.columns = ["Kategoria", "Łączny zysk (zł)", "Sprzedanych szt.", "Średni zysk (zł)"]
    st.dataframe(zysk_per_kat, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------------------------------------------------------
    # WYKRES SPRZEDAŻY W CZASIE
    # -------------------------------------------------------------------------
    # Kroki przygotowania danych do wykresu:
    #   1. Konwertujemy string "DD.MM.YYYY" na obiekt datetime
    #   2. Wyciągamy miesiąc w formacie "YYYY-MM" (do_period + astype(str))
    #   3. Grupujemy po miesiącu i liczymy zysk i liczbę sprzedaży
    #   4. Sortujemy chronologicznie
    # -------------------------------------------------------------------------
    st.subheader("Sprzedaż w czasie")
    sprzedane_wykres = sprzedane.copy()

    # pd.to_datetime konwertuje string na datetime — musimy podać format
    # bo domyślnie pandas nie wie że "14.03.2026" to DD.MM.YYYY
    sprzedane_wykres["data_sprzedazy"] = pd.to_datetime(
        sprzedane_wykres["data_sprzedazy"],
        format="%d.%m.%Y"
    )

    # to_period("M") wyciąga miesiąc jako Period (np. 2026-03)
    # astype(str) konwertuje na string żeby plotly mógł go użyć jako oś X
    sprzedane_wykres["miesiac"] = sprzedane_wykres["data_sprzedazy"].dt.to_period("M").astype(str)

    wykres_df = (
        sprzedane_wykres.groupby("miesiac")
        .agg(zysk=("zysk", "sum"), liczba=("nazwa", "count"))
        .reset_index()
        .sort_values("miesiac") # sortowanie chronologiczne po stringu "YYYY-MM"
        .rename(columns={
            "miesiac": "Miesiąc",
            "zysk": "Zysk (zł)",
            "liczba": "Sprzedanych szt."
        })
    )

    # Przełącznik między dwiema metrykami na wykresie
    metryka = st.radio(
        "Pokaż na wykresie",
        ["Zysk (zł)", "Sprzedanych szt."],
        horizontal=True
    )
    
    # Plotly zamiast st.bar_chart — daje pełną kontrolę nad skalą osi Y
    # co rozwiązuje problem z niewidocznymi słupkami przy małych wartościach
    fig = px.bar(
        wykres_df,
        x="Miesiąc",
        y=metryka,
        text=metryka # wartości wyświetlane nad słupkami
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title=metryka, xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    # Tabela z dokładnymi liczbami pod wykresem
    st.dataframe(wykres_df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # ZAMROŻONY KAPITAŁ
    # -------------------------------------------------------------------------
    # Pokazujemy sekcję tylko jeśli są produkty niesprzedane.
    # Zamrożony kapitał = suma cen zakupu produktów kupionych i wystawionych —
    # czyli pieniądze które zostały wydane ale jeszcze nie wróciły ze sprzedaży.
    # -------------------------------------------------------------------------
    if not wystawione.empty or not kupione.empty:
        st.divider()
        st.subheader("Niesprzedane produkty")

        # Filtrujemy wszystkie produkty które NIE są sprzedane
        niesprzedane = df[df["status"] != "sprzedany"]
        zamrozony_kapital = niesprzedane["cena_zakupu"].sum()
        col9, col10 = st.columns(2)
        with col9:
            st.metric("Kupionych + wystawionych", len(niesprzedane))
        with col10:
            # help= dodaje ikonkę "?" z podpowiedzią po najechaniu myszką
            st.metric("Zamrożony kapitał", f"{zamrozony_kapital:.0f} zł",
                help="Łączna kwota wydana na produkty które jeszcze nie zostały sprzedane")