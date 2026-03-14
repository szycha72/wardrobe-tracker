# =============================================================================
# views/lista.py — zakładka "Lista produktów"
# =============================================================================
# Najbardziej rozbudowany widok aplikacji. Odpowiada za:
#   1. Wyszukiwanie pełnotekstowe po wielu kolumnach
#   2. Filtrowanie po statusie produktu
#   3. Sortowanie po wybranej kolumnie
#   4. Wyświetlanie kart produktów z przyciskami akcji
#
# Ważne: cała logika filtrowania i sortowania dzieje się po stronie Pythona
# (pandas), nie w Firestore. Przy ~200 produktach to wystarczające podejście —
# pobieramy wszystko raz, a filtrujemy lokalnie w session_state.
# =============================================================================

import streamlit as st
from components.dialogs import dialog_sprzedazy, dialog_edycji, dialog_usuwania, dialog_wystawienia


def pokaz_liste():
    st.subheader("Produkty")

    # Pobieramy DataFrame z session_state — dane są już w pamięci,
    # nie robimy kolejnego zapytania do Firebase
    df = st.session_state.products_df

    if df.empty:
        st.info("Brak produktów. Dodaj pierwszy w zakładce ➕")
        return  # return zatrzymuje wykonanie funkcji — reszta kodu się nie wykona

    # -------------------------------------------------------------------------
    # WYSZUKIWARKA
    # -------------------------------------------------------------------------
    # Pole tekstowe które filtruje listę po opuszczeniu pola przez użytkownika.
    # Wyszukiwanie działa na kilku kolumnach jednocześnie — szczegóły niżej.
    # -------------------------------------------------------------------------
    szukaj = st.text_input(
        "🔍 Szukaj",
        placeholder="np. kurtka, Vinted, H&M..."
    )

    # -------------------------------------------------------------------------
    # KONTROLKI FILTROWANIA I SORTOWANIA
    # -------------------------------------------------------------------------
    # Trzy selectboxy w jednym wierszu — st.columns(3) dzieli
    # wiersz na trzy równe kolumny
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # LOGIKA FILTROWANIA
    # -------------------------------------------------------------------------
    # Pracujemy na kopii DataFrame żeby nie modyfikować oryginału
    # w session_state — gdybyśmy modyfikowali oryginał, filtr byłby
    # trwały między interakcjami użytkownika.
    # -------------------------------------------------------------------------
    wyniki = df.copy()

    # Filtr statusu — odpowiednik SQL: WHERE status = 'kupiony'
    if filtr == "Kupione":
        wyniki = wyniki[wyniki["status"] == "kupiony"]
    elif filtr == "Wystawione":
        wyniki = wyniki[wyniki["status"] == "wystawiony"]
    elif filtr == "Sprzedane":
        wyniki = wyniki[wyniki["status"] == "sprzedany"]

    # -------------------------------------------------------------------------
    # WYSZUKIWANIE PEŁNOTEKSTOWE
    # -------------------------------------------------------------------------
    # Szukamy frazy we wszystkich kolumnach tekstowych jednocześnie.
    # Odpowiednik SQL:
    #   WHERE nazwa LIKE '%fraza%'
    #   OR kategoria LIKE '%fraza%'
    #   OR opis LIKE '%fraza%' ...
    #
    # Jak to działa krok po kroku:
    #   1. wyniki[kolumny_tekstowe] — wybieramy tylko kolumny tekstowe
    #   2. .apply(lambda col: col.astype(str).str.contains(...)) — dla każdej
    #      kolumny sprawdzamy czy zawiera szukaną frazę (True/False)
    #   3. .any(axis=1) — wiersz pasuje jeśli CHOCIAŻ JEDNA kolumna zawiera frazę
    #   4. wyniki[maska] — zostawiamy tylko pasujące wiersze
    # -------------------------------------------------------------------------
    if szukaj:
        kolumny_tekstowe = ["nazwa", "kategoria", "opis", "miejsce_zakupu", "dowod_zakupu", "data_zakupu"]
        maska = wyniki[kolumny_tekstowe].apply(
            lambda col: col.astype(str).str.contains(szukaj, case=False, na=False)
        ).any(axis=1)
        wyniki = wyniki[maska]

    # -------------------------------------------------------------------------
    # LOGIKA SORTOWANIA
    # -------------------------------------------------------------------------
    # Mapujemy czytelną nazwę z selectboxa na nazwę kolumny w DataFrame.
    # Słownik jako "switch statement" — czytelniejszy niż seria if/elif.
    # -------------------------------------------------------------------------
    kolumna_sortowania = {
        "Data zakupu": "data_zakupu",
        "Cena zakupu": "cena_zakupu",
        "Cena sprzedaży": "cena_sprzedazy",
        "Kategoria": "kategoria"
    }[sortuj_po]

    ascending = kolejnosc == "Rosnąco"  # True jeśli rosnąco, False jeśli malejąco

    if kolumna_sortowania in wyniki.columns:
        wyniki = wyniki.sort_values(
            by=kolumna_sortowania,
            ascending=ascending,
            na_position="last"  # produkty bez tej wartości lądują na końcu listy
        )

    # Licznik wyników po zastosowaniu filtrów
    st.caption(f"Znaleziono: {len(wyniki)} produktów")

    if wyniki.empty:
        st.info("Brak produktów spełniających kryteria.")
        return

    # -------------------------------------------------------------------------
    # RENDEROWANIE KART PRODUKTÓW
    # -------------------------------------------------------------------------
    # iterrows() iteruje po DataFrame wiersz po wierszu, zwracając pary
    # (index, wiersz). Podkreślnik _ oznacza "indeks mnie nie interesuje".
    # produkt to pandas Series — dostęp do pól przez produkt["nazwa"]
    # lub produkt.get("nazwa", wartość_domyślna) dla pól opcjonalnych.
    # -------------------------------------------------------------------------
    for _, produkt in wyniki.iterrows():

        # st.container(border=True) rysuje obramowaną kartę dla każdego produktu
        with st.container(border=True):

            # Układ karty: [nazwa+info | status+cena | akcja | usuń | edytuj]
            # Proporcje kolumn: 3:1:1:1:1
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

            # -----------------------------------------------------------------
            # KOLUMNA 1 — informacje o produkcie
            # -----------------------------------------------------------------
            with col1:
                st.write(f"**{produkt['nazwa']}**")
                st.caption(f"{produkt['kategoria']} · {produkt.get('miejsce_zakupu', '')} · {produkt.get('dowod_zakupu', '')} · zakupiono {produkt.get('data_zakupu', '')}")

                # Opis pokazujemy tylko jeśli istnieje — produkt.get() zwraca
                # None jeśli pole nie istnieje, co jest falsy w Pythonie
                if produkt.get("opis"):
                    st.caption(produkt["opis"])

            # -----------------------------------------------------------------
            # KOLUMNA 2 — status i cena
            # Wyświetlamy różne informacje zależnie od statusu produktu
            # ----------------------------------------------------------------- 
            with col2:
                if produkt["status"] == "kupiony":
                    st.markdown("🔵 Kupiony")
                    st.write(f"**{produkt['cena_zakupu']} zł**")

                elif produkt["status"] == "wystawiony":
                    st.markdown("🟡 Wystawiony")
                    
                    # Jeśli cena wystawienia nie istnieje — pokazujemy cenę zakupu
                    st.write(f"**{produkt.get('cena_wystawienia', produkt['cena_zakupu'])} zł**")

                else: # sprzedany
                    st.markdown("🟢 Sprzedany")
                    st.write(f"**{produkt.get('cena_sprzedazy', '?')} zł**")
                    
                    # Zysk = cena sprzedaży - cena zakupu
                    zysk = produkt.get('cena_sprzedazy', 0) - produkt['cena_zakupu']
                    st.caption(f"Zysk: +{zysk:.0f} zł")
                    st.caption(f"📍 {produkt.get('gdzie_sprzedane', '')}")

            # -----------------------------------------------------------------
            # KOLUMNA 3 — główna akcja (zależna od statusu)
            # Każdy produkt ma inną akcję w zależności od etapu cyklu życia:
            #   kupiony   → można wystawić
            #   wystawiony → można sprzedać
            #   sprzedany → brak akcji (produkt zakończył cykl)
            # -----------------------------------------------------------------
            with col3:
                if produkt["status"] == "kupiony":
                    if st.button("📢 Wystaw", key=f"wystaw_{produkt['id']}"):
                        dialog_wystawienia(produkt.to_dict())
                elif produkt["status"] == "wystawiony":
                    if st.button("✅ Sprzedaj", key=f"sprzedaj_{produkt['id']}"):
                        dialog_sprzedazy(produkt.to_dict())

            # -----------------------------------------------------------------
            # KOLUMNA 4 — usuwanie (dostępne zawsze)
            # key musi być unikalny dla każdego przycisku w pętli —
            # używamy ID produktu żeby zagwarantować unikalność
            # -----------------------------------------------------------------
            with col4:
                if st.button("🗑️", key=f"usun_{produkt['id']}"):
                    dialog_usuwania(produkt.to_dict())

            # -----------------------------------------------------------------
            # KOLUMNA 5 — edycja (dostępna zawsze)
            # produkt.to_dict() konwertuje pandas Series na słownik Pythona —
            # dialogi oczekują słownika, nie Series
            # -----------------------------------------------------------------
            with col5:
                if st.button("✏️", key=f"edytuj_{produkt['id']}"):
                    dialog_edycji(produkt.to_dict())