# =============================================================================
# views/formularz.py — zakładka "Dodaj produkt"
# =============================================================================
# Ten plik odpowiada za formularz dodawania nowego produktu.
# Nowy produkt zawsze startuje ze statusem "kupiony" — to pierwszy krok
# w cyklu życia produktu: kupiony → wystawiony → sprzedany.
# =============================================================================

import streamlit as st
import datetime
import pandas as pd
from database import dodaj_produkt
from config import KATEGORIE, DOWODY_ZAKUPU, FORMAT_DATY


def pokaz_formularz():
    st.subheader("Dodaj nowy produkt")
    
    # -------------------------------------------------------------------------
    # FORMULARZ WPROWADZANIA DANYCH
    # -------------------------------------------------------------------------
    # st.form grupuje wszystkie pola razem — dane są wysyłane dopiero po
    # kliknięciu przycisku "Dodaj produkt", nie przy każdej zmianie pola.
    # clear_on_submit=True czyści wszystkie pola po pomyślnym wysłaniu.
    #
    # Bez st.form Streamlit przerysowywałby całą stronę przy każdym wpisanym
    # znaku — st.form znacznie poprawia wydajność formularzy.
    # -------------------------------------------------------------------------
    with st.form("formularz_produktu", clear_on_submit=True):
        nazwa = st.text_input(
            "Nazwa produktu",
            placeholder="np. Kurtka zimowa H&M"
        )

        # Dwa pola obok siebie — st.columns(2) dzieli wiersz na dwie równe kolumny
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
                KATEGORIE  # lista z config.py
            )

        data_zakupu = st.date_input(
            "Data zakupu",
            value=datetime.date.today() # domyślnie dzisiaj
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
            DOWODY_ZAKUPU,  # lista z config.py
            horizontal=True
        )

        submitted = st.form_submit_button(
            "➕ Dodaj produkt",
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # OBSŁUGA WYSŁANIA FORMULARZA
    # -------------------------------------------------------------------------
    # Ten blok wykonuje się tylko gdy użytkownik kliknął przycisk "Dodaj produkt".
    # Uwaga: blok if submitted jest POZA blokiem with st.form — to wymaganie
    # Streamlita, logika po wysłaniu musi być poza formularzem.
    # -------------------------------------------------------------------------
    if submitted:

        # Walidacja — sprawdzamy dane przed zapisem do bazy
        if not nazwa:
            st.error("Podaj nazwę produktu!")
        elif cena_zakupu <= 0:
            st.error("Podaj cenę zakupu!")
        elif data_zakupu > datetime.date.today():
            # Zabezpieczenie przed przypadkowym wpisaniem przyszłej daty
            st.error("Data zakupu nie może być w przyszłości!")
        else:
            # -------------------------------------------------------------
            # BUDOWANIE SŁOWNIKA PRODUKTU
            # -------------------------------------------------------------
            # Nowy produkt zawsze startuje ze statusem "kupiony".
            # timestamp — czytelna data dla podglądu w konsoli Firebase
            # timestamp_unix — liczba używana do sortowania w Firestore
            #   (stringi dat "DD.MM.YYYY" nie sortują się poprawnie jako tekst)
            # -------------------------------------------------------------
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

            # Zapis do Firestore — funkcja zwraca ID nowego dokumentu
            nowe_id = dodaj_produkt(nowy_produkt)
            nowy_produkt["id"] = nowe_id

            # -------------------------------------------------------------
            # AKTUALIZACJA LOKALNEGO DATAFRAME
            # -------------------------------------------------------------
            # Zamiast pobierać wszystko od nowa z Firebase (wolne),
            # dodajemy nowy produkt bezpośrednio do lokalnego DataFrame.
            # pd.concat łączy dwa DataFrame — nowy produkt na górze (insert(0))
            # -------------------------------------------------------------
            nowy_df = pd.DataFrame([nowy_produkt])
            st.session_state.products_df = pd.concat(
                [nowy_df, st.session_state.products_df],
                ignore_index=True
            )
            st.success(f"Dodano produkt: {nazwa} ✅")