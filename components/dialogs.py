import streamlit as st
import datetime
from database import aktualizuj_produkt, usun_produkt


@st.dialog("Zapisz sprzedaż")
def dialog_sprzedazy(produkt):
    st.write(f"**{produkt['nazwa']}**")
    st.caption(f"Cena zakupu: {produkt['cena_zakupu']} zł")
    
    cena_sprzedazy = st.number_input(
        "Cena sprzedaży (zł)",
        min_value=0.0,
        step=1.0
    )
    data_sprzedazy = st.date_input(
        "Data sprzedaży",
        value=datetime.date.today()
    )
    gdzie_sprzedane = st.selectbox(
        "Gdzie sprzedane",
        ["Vinted", "OLX", "Allegro", "Inne"]
    )
    
    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("💾 Zapisz", use_container_width=True):
            if cena_sprzedazy <= 0:
                st.error("Podaj cenę sprzedaży!")
            else:
                dane = {
                    "status": "sprzedany",
                    "cena_sprzedazy": cena_sprzedazy,
                    "data_sprzedazy": data_sprzedazy.strftime("%d.%m.%Y"),
                    "gdzie_sprzedane": gdzie_sprzedane
                }
                aktualizuj_produkt(produkt["id"], dane)
                maska = st.session_state.products_df["id"] == produkt["id"]
                for klucz, wartosc in dane.items():
                    st.session_state.products_df.loc[maska, klucz] = wartosc
                st.rerun()
    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun()


@st.dialog("Edytuj produkt")
def dialog_edycji(produkt):
    nazwa = st.text_input("Nazwa produktu", value=produkt["nazwa"])
    
    col1, col2 = st.columns(2)
    with col1:
        cena_zakupu = st.number_input(
            "Cena zakupu (zł)",
            min_value=0.0,
            step=1.0,
            value=float(produkt["cena_zakupu"])
        )
    with col2:
        kategoria = st.selectbox(
            "Kategoria",
            ["Kurtki", "Sukienki", "Spodnie", "Buty", "Torebki", "Inne"],
            index=["Kurtki", "Sukienki", "Spodnie", "Buty", "Torebki", "Inne"].index(produkt["kategoria"])
        )

    opis = st.text_area(
        "Opis",
        value=produkt.get("opis", ""),
        height=80
    )
    miejsce_zakupu = st.text_input(
        "Gdzie kupiony",
        value=produkt.get("miejsce_zakupu", "")
    )
    dowod_zakupu = st.radio(
        "Dowód zakupu",
        ["Paragon", "Faktura"],
        index=["Paragon", "Faktura"].index(produkt.get("dowod_zakupu", "Paragon")),
        horizontal=True
    )
    data_zakupu = st.date_input(
        "Data zakupu",
        value=datetime.datetime.strptime(
            produkt.get("data_zakupu", datetime.date.today().strftime("%d.%m.%Y")),
            "%d.%m.%Y"
        ).date()
    )

    if produkt.get("status") == "sprzedany":
        st.divider()
        st.caption("Informacje o sprzedaży")
        cena_sprzedazy = st.number_input(
            "Cena sprzedaży (zł)",
            min_value=0.0,
            step=1.0,
            value=float(produkt.get("cena_sprzedazy", 0.0))
        )
        gdzie_sprzedane = st.selectbox(
            "Gdzie sprzedane",
            ["Vinted", "OLX", "Allegro", "Inne"],
            index=["Vinted", "OLX", "Allegro", "Inne"].index(produkt.get("gdzie_sprzedane", "Inne"))
        )
        data_sprzedazy = st.date_input(
            "Data sprzedaży",
            value=datetime.datetime.strptime(
                produkt.get("data_sprzedazy", datetime.date.today().strftime("%d.%m.%Y")),
                "%d.%m.%Y"
            ).date()
        )

    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("💾 Zapisz zmiany", use_container_width=True):
            if not nazwa:
                st.error("Podaj nazwę produktu!")
            elif cena_zakupu <= 0:
                st.error("Podaj cenę zakupu!")
            elif data_zakupu > datetime.date.today():
                st.error("Data zakupu nie może być w przyszłości!")
            else:
                dane = {
                    "nazwa": nazwa,
                    "cena_zakupu": cena_zakupu,
                    "kategoria": kategoria,
                    "opis": opis,
                    "miejsce_zakupu": miejsce_zakupu,
                    "dowod_zakupu": dowod_zakupu,
                    "data_zakupu": data_zakupu.strftime("%d.%m.%Y")
                }
                if produkt.get("status") == "sprzedany":
                    dane["cena_sprzedazy"] = cena_sprzedazy
                    dane["gdzie_sprzedane"] = gdzie_sprzedane
                    dane["data_sprzedazy"] = data_sprzedazy.strftime("%d.%m.%Y")

                aktualizuj_produkt(produkt["id"], dane)
                maska = st.session_state.products_df["id"] == produkt["id"]
                for klucz, wartosc in dane.items():
                    st.session_state.products_df.loc[maska, klucz] = wartosc
                st.rerun()
    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun()


@st.dialog("Usuń produkt")
def dialog_usuwania(produkt):
    st.warning(f"Czy na pewno chcesz usunąć **{produkt['nazwa']}**? Tej operacji nie można cofnąć.")
    
    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("🗑️ Usuń", use_container_width=True, type="primary"):
            usun_produkt(produkt["id"])
            maska = st.session_state.products_df["id"] != produkt["id"]
            st.session_state.products_df = st.session_state.products_df[maska]
            st.rerun()
    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun()