import streamlit as st
import pandas as pd
import plotly.express as px


def pokaz_dashboard():
    st.subheader("Podsumowanie")

    df = st.session_state.products_df

    if df.empty:
        st.info("Brak produktów.")
        return

    sprzedane = df[df["status"] == "sprzedany"].copy()
    wystawione = df[df["status"] == "wystawiony"].copy()
    kupione = df[df["status"] == "kupiony"].copy()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Wszystkich", len(df))
    with col2:
        st.metric("Kupionych", len(kupione))
    with col3:
        st.metric("Wystawionych", len(wystawione))
    with col4:
        st.metric("Sprzedanych", len(sprzedane))

    if sprzedane.empty:
        st.info("Sprzedaj pierwszy produkt żeby zobaczyć statystyki.")
        return

    st.divider()
    sprzedane["zysk"] = sprzedane["cena_sprzedazy"] - sprzedane["cena_zakupu"]
    laczny_zysk = sprzedane["zysk"].sum()
    laczny_przychod = sprzedane["cena_sprzedazy"].sum()
    laczny_koszt = sprzedane["cena_zakupu"].sum()
    srednia_marza = (laczny_zysk / laczny_przychod * 100) if laczny_przychod > 0 else 0
    sredni_zysk = sprzedane["zysk"].mean()

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
    st.subheader("Zysk per kategoria")
    zysk_per_kat = (
        sprzedane.groupby("kategoria")["zysk"]
        .agg(["sum", "count", "mean"])
        .rename(columns={"sum": "Łączny zysk", "count": "Sprzedanych", "mean": "Średni zysk"})
        .sort_values("Łączny zysk", ascending=False)
        .reset_index()
    )
    zysk_per_kat["Łączny zysk"] = zysk_per_kat["Łączny zysk"].round(0).astype(int)
    zysk_per_kat["Średni zysk"] = zysk_per_kat["Średni zysk"].round(0).astype(int)
    zysk_per_kat.columns = ["Kategoria", "Łączny zysk (zł)", "Sprzedanych szt.", "Średni zysk (zł)"]
    st.dataframe(zysk_per_kat, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Sprzedaż w czasie")
    sprzedane_wykres = sprzedane.copy()
    sprzedane_wykres["data_sprzedazy"] = pd.to_datetime(
        sprzedane_wykres["data_sprzedazy"],
        format="%d.%m.%Y"
    )
    sprzedane_wykres["miesiac"] = sprzedane_wykres["data_sprzedazy"].dt.to_period("M").astype(str)

    wykres_df = (
        sprzedane_wykres.groupby("miesiac")
        .agg(zysk=("zysk", "sum"), liczba=("nazwa", "count"))
        .reset_index()
        .sort_values("miesiac")
        .rename(columns={
            "miesiac": "Miesiąc",
            "zysk": "Zysk (zł)",
            "liczba": "Sprzedanych szt."
        })
    )

    metryka = st.radio(
        "Pokaż na wykresie",
        ["Zysk (zł)", "Sprzedanych szt."],
        horizontal=True
    )
    
    fig = px.bar(
        wykres_df,
        x="Miesiąc",
        y=metryka,
        text=metryka
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title=metryka, xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(wykres_df, use_container_width=True, hide_index=True)

    if not wystawione.empty or not kupione.empty:
        st.divider()
        st.subheader("Niesprzedane produkty")
        niesprzedane = df[df["status"] != "sprzedany"]
        zamrozony_kapital = niesprzedane["cena_zakupu"].sum()
        col9, col10 = st.columns(2)
        with col9:
            st.metric("Kupionych + wystawionych", len(niesprzedane))
        with col10:
            st.metric("Zamrożony kapitał", f"{zamrozony_kapital:.0f} zł",
                help="Łączna kwota wydana na produkty które jeszcze nie zostały sprzedane")