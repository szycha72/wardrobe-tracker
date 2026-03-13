import streamlit as st
import datetime
import pandas as pd
from database import dodaj_produkt
from config import KATEGORIE, DOWODY_ZAKUPU, FORMAT_DATY


def pokaz_formularz():
    st.subheader("Dodaj nowy produkt")

    with st.form("formularz_produktu", clear_on_submit=True):
        nazwa = st.text_input(
            "Nazwa produktu",
            placeholder="np. Kurtka zimowa H&M"
        )

        col1, col2 = st.columns(2)
        with col1:
            cena_zakupu = st.number_input(
                "Cena zakupu (zł)",
                min_value=0.0,
                step=1.0
            )
        with col2:
            kategoria = st.selectbox(
                "Kategoria",
                KATEGORIE
            )

        data_zakupu = st.date_input(
            "Data zakupu",
            value=datetime.date.today()
        )

        opis = st.text_area(
            "Opis (opcjonalnie)",
            placeholder="np. rozmiar M, stan bardzo dobry",
            height=80
        )

        miejsce_zakupu = st.text_input(
            "Gdzie kupiony",
            placeholder="np. Vinted, OLX"
        )

        dowod_zakupu = st.radio(
            "Dowód zakupu",
            DOWODY_ZAKUPU,
            horizontal=True
        )

        submitted = st.form_submit_button(
            "➕ Dodaj produkt",
            use_container_width=True
        )

    if submitted:
        if not nazwa:
            st.error("Podaj nazwę produktu!")
        elif cena_zakupu <= 0:
            st.error("Podaj cenę zakupu!")
        elif data_zakupu > datetime.date.today():
            st.error("Data zakupu nie może być w przyszłości!")
        else:
            nowy_produkt = {
                "nazwa": nazwa,
                "cena_zakupu": cena_zakupu,
                "kategoria": kategoria,
                "opis": opis,
                "miejsce_zakupu": miejsce_zakupu,
                "dowod_zakupu": dowod_zakupu,
                "status": "kupiony",
                "data_zakupu": data_zakupu.strftime(FORMAT_DATY),
                "timestamp": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "timestamp_unix": datetime.datetime.now().timestamp()
            }
            nowe_id = dodaj_produkt(nowy_produkt)
            nowy_produkt["id"] = nowe_id
            nowy_df = pd.DataFrame([nowy_produkt])
            st.session_state.products_df = pd.concat(
                [nowy_df, st.session_state.products_df],
                ignore_index=True
            )
            st.success(f"Dodano produkt: {nazwa} ✅")