# =============================================================================
# components/dialogs.py — modale aplikacji
# =============================================================================
# Ten plik zawiera wszystkie wyskakujące okienka (modale) aplikacji.
# Modal to okienko które pojawia się na wierzchu strony po kliknięciu przycisku
# i wymaga od użytkownika podjęcia akcji (zapisz/anuluj) zanim wróci do listy.
#
# Modale są zdefiniowane jako funkcje z dekoratorem @st.dialog —
# wywołanie funkcji automatycznie otwiera okienko.
#
# Wszystkie modale działają według tego samego wzorca:
#   1. Wyświetl informacje o produkcie (kontekst dla użytkownika)
#   2. Pokaż pola do wypełnienia
#   3. Po kliknięciu "Zapisz":
#      a. Zapisz do Firestore (trwały zapis)
#      b. Zaktualizuj session_state (natychmiastowe odświeżenie UI)
#      c. st.rerun() — przerysuj stronę żeby zmiany były widoczne
#   4. Po kliknięciu "Anuluj" — zamknij modal bez zapisywania
#
# Modale w tym pliku:
#   - dialog_sprzedazy   — rejestracja sprzedaży produktu
#   - dialog_edycji      — edycja wszystkich danych produktu
#   - dialog_usuwania    — potwierdzenie usunięcia produktu
#   - dialog_wystawienia — rejestracja wystawienia produktu na sprzedaż
# =============================================================================

import streamlit as st
import datetime
from database import aktualizuj_produkt, usun_produkt, aktualizuj_session_state
from config import KATEGORIE, PLATFORMY, DOWODY_ZAKUPU, FORMAT_DATY

# =============================================================================
# DIALOG SPRZEDAŻY
# =============================================================================
@st.dialog("Zapisz sprzedaż")
def dialog_sprzedazy(produkt):
    """Modal rejestracji sprzedaży produktu.

    Otwierany po kliknięciu "✅ Sprzedaj" na karcie wystawionego produktu.
    Zmienia status produktu z "wystawiony" na "sprzedany" i zapisuje
    cenę sprzedaży, datę oraz platformę sprzedaży.

    Args:
        produkt (dict): słownik z danymi produktu przekazany z lista.py
    """

    # Kontekst — pokazujemy użytkownikowi który produkt sprzedaje
    st.write(f"**{produkt['nazwa']}**")
    st.caption(f"Cena zakupu: {produkt['cena_zakupu']} zł")
    
    # -------------------------------------------------------------------------
    # POLA FORMULARZA
    # -------------------------------------------------------------------------
    cena_sprzedazy = st.number_input(
        "Cena sprzedaży (zł)",
        min_value=0.0,
        step=1.0
    )
    data_sprzedazy = st.date_input(
        "Data sprzedaży",
        value=datetime.date.today() # domyślnie dzisiaj
    )
    gdzie_sprzedane = st.selectbox(
        "Gdzie sprzedane",
        PLATFORMY # lista z config.py: ["Vinted", "OLX", "Inne"]
    )
    
    # -------------------------------------------------------------------------
    # PRZYCISKI AKCJI
    # -------------------------------------------------------------------------
    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("💾 Zapisz", use_container_width=True):

            # Walidacja — cena musi być większa od zera
            if cena_sprzedazy <= 0:
                st.error("Podaj cenę sprzedaży!")
            else:
                # Słownik z polami do zaktualizowania w Firestore
                # Nie podajemy tutaj wszystkich pól produktu — tylko te które się zmieniają
                dane = {
                    "status": "sprzedany",
                    "cena_sprzedazy": cena_sprzedazy,
                    "data_sprzedazy": data_sprzedazy.strftime(FORMAT_DATY),
                    "gdzie_sprzedane": gdzie_sprzedane
                }

                # Zapis do Firestore (trwały) + aktualizacja session_state (UI)
                aktualizuj_produkt(produkt["id"], dane)
                aktualizuj_session_state(produkt["id"], dane)
                st.rerun() # zamknij modal i odśwież listę

    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun() # zamknij modal bez zapisywania

# =============================================================================
# DIALOG EDYCJI
# =============================================================================

@st.dialog("Edytuj produkt")
def dialog_edycji(produkt):
    """Modal edycji wszystkich danych produktu.

    Otwierany po kliknięciu "✏️" na karcie dowolnego produktu.
    Pozwala edytować wszystkie pola — zakup, wystawienie i sprzedaż —
    niezależnie od aktualnego statusu produktu.

    Sekcje wystawienia i sprzedaży są zawsze widoczne. Pola które nie były
    jeszcze wypełnione (np. data wystawienia dla kupionego produktu) mają
    wartości domyślne (0 dla cen, dzisiaj dla dat).

    Args:
        produkt (dict): słownik z danymi produktu przekazany z lista.py
    """

    # Kontekst — pokazujemy nazwę i aktualny status
    st.write(f"**{produkt['nazwa']}**")
    st.caption(f"Status: {produkt['status']}")

    # =========================================================================
    # SEKCJA 1 — INFORMACJE O ZAKUPIE
    # =========================================================================
    st.subheader("Informacje o zakupie")

    nazwa = st.text_input("Nazwa produktu", value=produkt["nazwa"])

    # Dwa pola w jednym wierszu
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
            KATEGORIE,
            # index= określa który element listy jest domyślnie wybrany
            # KATEGORIE.index("Buty") zwraca np. 3 — Streamlit zaznacza 4. element
            index=KATEGORIE.index(produkt["kategoria"])
        )

    opis = st.text_area("Opis", value=produkt.get("opis", ""), height=80)
    miejsce_zakupu = st.text_input("Gdzie kupiony", value=produkt.get("miejsce_zakupu", ""))

    dowod_zakupu = st.radio(
        "Dowód zakupu",
        DOWODY_ZAKUPU,
        index=DOWODY_ZAKUPU.index(produkt.get("dowod_zakupu", "Paragon")),
        horizontal=True
    )

    # strptime konwertuje string "DD.MM.YYYY" na obiekt date —
    # st.date_input wymaga obiektu date, nie stringa
    data_zakupu = st.date_input(
        "Data zakupu",
        value=datetime.datetime.strptime(
            produkt.get("data_zakupu", datetime.date.today().strftime(FORMAT_DATY)),
            FORMAT_DATY
        ).date()
    )

    st.divider()

    # =========================================================================
    # SEKCJA 2 — INFORMACJE O WYSTAWIENIU
    # =========================================================================
    st.subheader("Informacje o wystawieniu")

    cena_wystawienia = st.number_input(
        "Cena wystawienia (zł)",
        min_value=0.0,
        step=1.0,
        value=float(produkt.get("cena_wystawienia", 0.0))
        # Domyślnie 0.0 jeśli produkt nie był jeszcze wystawiony
    )

    # Zabezpieczenie przed NaN — pandas wypełnia brakujące pola jako NaN (float),
    # a strptime wymaga stringa. isinstance() sprawdza czy wartość jest stringiem.
    data_wystawienia_raw = produkt.get("data_wystawienia", None)
    if not isinstance(data_wystawienia_raw, str):
        data_wystawienia_raw = None # zamieniamy NaN/None na None
    
    data_wystawienia = st.date_input(
        "Data wystawienia",
        value=datetime.datetime.strptime(data_wystawienia_raw, FORMAT_DATY).date() 
        if data_wystawienia_raw else datetime.date.today()
        # Jeśli data istnieje — parsujemy, jeśli nie — domyślnie dzisiaj
    )

    st.divider()

    # =========================================================================
    # SEKCJA 3 — INFORMACJE O SPRZEDAŻY
    # =========================================================================
    st.subheader("Informacje o sprzedaży")

    cena_sprzedazy = st.number_input(
        "Cena sprzedaży (zł)",
        min_value=0.0,
        step=1.0,
        value=float(produkt.get("cena_sprzedazy", 0.0))
        # Domyślnie 0.0 jeśli produkt nie był jeszcze sprzedany
    )

    # Zabezpieczenie przed NaN — ten sam wzorzec co przy dacie wystawienia
    gdzie_sprzedane_wartosc = produkt.get("gdzie_sprzedane", "Inne")
    if not isinstance(gdzie_sprzedane_wartosc, str):
        gdzie_sprzedane_wartosc = "Inne" # NaN nie jest w liście PLATFORMY — crashuje .index()

    gdzie_sprzedane = st.selectbox(
        "Gdzie sprzedane",
        PLATFORMY,
        index=PLATFORMY.index(gdzie_sprzedane_wartosc)
    )

    # Ten sam wzorzec zabezpieczenia przed NaN co przy dacie wystawienia
    data_sprzedazy_raw = produkt.get("data_sprzedazy", None)
    if not isinstance(data_sprzedazy_raw, str):
        data_sprzedazy_raw = None

    data_sprzedazy = st.date_input(
        "Data sprzedaży",
        value=datetime.datetime.strptime(data_sprzedazy_raw, FORMAT_DATY).date() if data_sprzedazy_raw else datetime.date.today()
    )

    # =========================================================================
    # PRZYCISKI AKCJI
    # =========================================================================
    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("💾 Zapisz zmiany", use_container_width=True):

            # Walidacja danych przed zapisem
            if not nazwa:
                st.error("Podaj nazwę produktu!")
            elif cena_zakupu <= 0:
                st.error("Podaj cenę zakupu!")
            elif data_zakupu > datetime.date.today():
                st.error("Data zakupu nie może być w przyszłości!")
            else:
                # Budujemy słownik ze wszystkimi polami do zaktualizowania.
                # Zapisujemy zawsze wszystkie sekcje — pola z wartością 0
                # lub domyślną datą zostaną nadpisane w Firestore.
                dane = {
                    "nazwa": nazwa,
                    "cena_zakupu": cena_zakupu,
                    "kategoria": kategoria,
                    "opis": opis,
                    "miejsce_zakupu": miejsce_zakupu,
                    "dowod_zakupu": dowod_zakupu,
                    "data_zakupu": data_zakupu.strftime(FORMAT_DATY),
                    "cena_wystawienia": cena_wystawienia,
                    "data_wystawienia": data_wystawienia.strftime(FORMAT_DATY),
                    "cena_sprzedazy": cena_sprzedazy,
                    "gdzie_sprzedane": gdzie_sprzedane,
                    "data_sprzedazy": data_sprzedazy.strftime(FORMAT_DATY)
                }
                aktualizuj_produkt(produkt["id"], dane)
                aktualizuj_session_state(produkt["id"], dane)
                st.rerun()

    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun()

# =============================================================================
# DIALOG USUWANIA
# =============================================================================

@st.dialog("Usuń produkt")
def dialog_usuwania(produkt):
    """Modal potwierdzenia usunięcia produktu.

    Otwierany po kliknięciu "🗑️" na karcie dowolnego produktu.
    Wymaga potwierdzenia przed usunięciem — operacja jest nieodwracalna.

    Po usunięciu z Firestore, produkt jest też usuwany z lokalnego DataFrame
    przez filtrowanie wszystkich wierszy z innym ID.

    Args:
        produkt (dict): słownik z danymi produktu przekazany z lista.py
    """

    # Ostrzeżenie z nazwą produktu — użytkownik wie co usuwa
    st.warning(f"Czy na pewno chcesz usunąć **{produkt['nazwa']}**? Tej operacji nie można cofnąć.")
    
    col_ok, col_anuluj = st.columns(2)
    with col_ok:

        # type="primary" nadaje przyciskowi czerwony kolor — wizualne ostrzeżenie
        if st.button("🗑️ Usuń", use_container_width=True, type="primary"):

            # Usuń z Firestore
            usun_produkt(produkt["id"])

            # Usuń z lokalnego DataFrame — zostawiamy wszystkie wiersze OPRÓCZ usuwanego.
            # To odwrotność filtrowania: != zamiast ==
            # Odpowiednik SQL: DELETE FROM products WHERE id = produkt_id
            maska = st.session_state.products_df["id"] != produkt["id"]
            st.session_state.products_df = st.session_state.products_df[maska]

            st.rerun()

    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun()

# =============================================================================
# DIALOG WYSTAWIENIA
# =============================================================================

@st.dialog("Wystaw produkt")
def dialog_wystawienia(produkt):
    """Modal rejestracji wystawienia produktu na sprzedaż.

    Otwierany po kliknięciu "📢 Wystaw" na karcie kupionego produktu.
    Zmienia status produktu z "kupiony" na "wystawiony" i zapisuje
    cenę wystawienia oraz datę wystawienia.

    Args:
        produkt (dict): słownik z danymi produktu przekazany z lista.py
    """

    # Kontekst — pokazujemy użytkownikowi który produkt wystawia
    st.write(f"**{produkt['nazwa']}**")
    st.caption(f"Cena zakupu: {produkt['cena_zakupu']} zł")

    # -------------------------------------------------------------------------
    # POLA FORMULARZA
    # -------------------------------------------------------------------------
    cena_wystawienia = st.number_input(
        "Cena wystawienia (zł)",
        min_value=0.0,
        step=1.0
    )
    data_wystawienia = st.date_input(
        "Data wystawienia",
        value=datetime.date.today() # domyślnie dzisiaj
    )
    
    # -------------------------------------------------------------------------
    # PRZYCISKI AKCJI
    # -------------------------------------------------------------------------
    col_ok, col_anuluj = st.columns(2)
    with col_ok:
        if st.button("📢 Wystaw", use_container_width=True):

            # Walidacja — cena musi być większa od zera
            if cena_wystawienia <= 0:
                st.error("Podaj cenę wystawienia!")
            else:
                dane = {
                    "status": "wystawiony",
                    "cena_wystawienia": cena_wystawienia,
                    "data_wystawienia": data_wystawienia.strftime(FORMAT_DATY)
                }

                # Zapis do Firestore (trwały) + aktualizacja session_state (UI)
                aktualizuj_produkt(produkt["id"], dane)
                aktualizuj_session_state(produkt["id"], dane)
                st.rerun() # zamknij modal i odśwież listę
    with col_anuluj:
        if st.button("✖ Anuluj", use_container_width=True):
            st.rerun() # zamknij modal bez zapisywania