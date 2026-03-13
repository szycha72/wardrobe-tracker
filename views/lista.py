import streamlit as st
from components.dialogs import dialog_sprzedazy, dialog_edycji, dialog_usuwania, dialog_wystawienia


def pokaz_liste():
    st.subheader("Produkty")

    df = st.session_state.products_df

    if df.empty:
        st.info("Brak produktów. Dodaj pierwszy w zakładce ➕")
        return

    szukaj = st.text_input(
        "🔍 Szukaj",
        placeholder="np. kurtka, Vinted, H&M..."
    )

    col_filtr, col_sort, col_kolejnosc = st.columns(3)
    with col_filtr:
        filtr = st.selectbox("Status", ["Wszystkie","Kupione", "Wystawione", "Sprzedane"])
    with col_sort:
        sortuj_po = st.selectbox(
            "Sortuj po",
            ["Data zakupu", "Cena zakupu", "Cena sprzedaży", "Kategoria"]
        )
    with col_kolejnosc:
        kolejnosc = st.selectbox("Kolejność", ["Malejąco", "Rosnąco"])

    wyniki = df.copy()

    if filtr == "Kupione":
        wyniki = wyniki[wyniki["status"] == "kupiony"]
    elif filtr == "Wystawione":
        wyniki = wyniki[wyniki["status"] == "wystawiony"]
    elif filtr == "Sprzedane":
        wyniki = wyniki[wyniki["status"] == "sprzedany"]

    if szukaj:
        kolumny_tekstowe = ["nazwa", "kategoria", "opis", "miejsce_zakupu", "dowod_zakupu", "data_zakupu"]
        maska = wyniki[kolumny_tekstowe].apply(
            lambda col: col.astype(str).str.contains(szukaj, case=False, na=False)
        ).any(axis=1)
        wyniki = wyniki[maska]

    kolumna_sortowania = {
        "Data zakupu": "data_zakupu",
        "Cena zakupu": "cena_zakupu",
        "Cena sprzedaży": "cena_sprzedazy",
        "Kategoria": "kategoria"
    }[sortuj_po]

    ascending = kolejnosc == "Rosnąco"

    if kolumna_sortowania in wyniki.columns:
        wyniki = wyniki.sort_values(
            by=kolumna_sortowania,
            ascending=ascending,
            na_position="last"
        )

    st.caption(f"Znaleziono: {len(wyniki)} produktów")

    if wyniki.empty:
        st.info("Brak produktów spełniających kryteria.")
        return

    for _, produkt in wyniki.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            with col1:
                st.write(f"**{produkt['nazwa']}**")
                st.caption(f"{produkt['kategoria']} · {produkt.get('miejsce_zakupu', '')} · {produkt.get('dowod_zakupu', '')} · zakupiono {produkt.get('data_zakupu', '')}")
                if produkt.get("opis"):
                    st.caption(produkt["opis"])

            with col2:
                if produkt["status"] == "kupiony":
                    st.markdown("🔵 Kupiony")
                    st.write(f"**{produkt['cena_zakupu']} zł**")
                elif produkt["status"] == "wystawiony":
                    st.markdown("🟡 Wystawiony")
                    st.write(f"**{produkt.get('cena_wystawienia', produkt['cena_zakupu'])} zł**")
                else:
                    st.markdown("🟢 Sprzedany")
                    st.write(f"**{produkt.get('cena_sprzedazy', '?')} zł**")
                    zysk = produkt.get('cena_sprzedazy', 0) - produkt['cena_zakupu']
                    st.caption(f"Zysk: +{zysk:.0f} zł")
                    st.caption(f"📍 {produkt.get('gdzie_sprzedane', '')}")

            with col3:
                if produkt["status"] == "kupiony":
                    if st.button("📢 Wystaw", key=f"wystaw_{produkt['id']}"):
                        dialog_wystawienia(produkt.to_dict())
                elif produkt["status"] == "wystawiony":
                    if st.button("✅ Sprzedaj", key=f"sprzedaj_{produkt['id']}"):
                        dialog_sprzedazy(produkt.to_dict())

            with col4:
                if st.button("🗑️", key=f"usun_{produkt['id']}"):
                    dialog_usuwania(produkt.to_dict())

            with col5:
                if st.button("✏️", key=f"edytuj_{produkt['id']}"):
                    dialog_edycji(produkt.to_dict())