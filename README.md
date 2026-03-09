# 👗 Wardrobe Tracker

Aplikacja webowa do zarządzania sprzedażą ubrań — zbudowana w Pythonie z użyciem Streamlit i Firebase.

## O projekcie

Wardrobe Tracker zastępuje arkusz Excel w prowadzeniu ewidencji zakupionych i sprzedanych ubrań. Umożliwia śledzenie stanów magazynowych, obliczanie zysków i eksport danych — wszystko dostępne z poziomu telefonu lub komputera.

## Funkcjonalności

- **Dodawanie produktów** — formularz z nazwą, ceną zakupu, kategorią, opisem, miejscem zakupu i dowodem zakupu
- **Lista produktów** — przeglądanie wszystkich produktów z filtrami statusu, wyszukiwarką pełnotekstową i sortowaniem
- **Oznaczanie sprzedaży** — rejestrowanie ceny sprzedaży, daty i platformy sprzedaży (Vinted, OLX, Allegro)
- **Edycja i usuwanie** — możliwość edycji wszystkich danych produktu oraz usunięcia go z bazy
- **Dashboard** — statystyki sprzedaży: łączny zysk, średnia marża, zysk per kategoria, zamrożony kapitał, wykres sprzedaży w czasie
- **Eksport do XLSX** — eksport danych do pliku Excel z arkuszem produktów i arkuszem podsumowania

## Stack technologiczny

| Warstwa | Technologia |
|---|---|
| UI | Streamlit |
| Baza danych | Firebase Firestore |
| Hosting | Streamlit Community Cloud |
| Wersjonowanie | GitHub |

## Struktura projektu

```
wardrobe-tracker/
├── app.py                  # główny plik — nawigacja i inicjalizacja
├── database.py             # komunikacja z Firebase Firestore
├── firebase_config.py      # konfiguracja połączenia z Firebase
├── requirements.txt        # zależności projektu
├── .gitignore
├── .streamlit/
│   └── secrets.toml        # klucze API (nie wrzucać na GitHub!)
├── views/
│   ├── lista.py            # zakładka z listą produktów
│   ├── formularz.py        # zakładka z formularzem dodawania
│   ├── dashboard.py        # zakładka z dashboardem i wykresami
│   └── eksport.py          # zakładka z eksportem do XLSX
└── components/
    └── dialogs.py          # modale: sprzedaż, edycja, usuwanie
```

## Uruchomienie lokalne

### Wymagania
- Python 3.10+
- Konto Firebase z projektem Firestore

### Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/TwojaNazwa/wardrobe-tracker.git
cd wardrobe-tracker
```

2. Stwórz i aktywuj wirtualne środowisko:
```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Skonfiguruj sekrety Firebase — stwórz plik `.streamlit/secrets.toml`:
```toml
[firebase]
type = "service_account"
project_id = "twoj-project-id"
private_key_id = "twoj-private-key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "twoj-client-email"
token_uri = "https://oauth2.googleapis.com/token"
```

5. Uruchom aplikację:
```bash
streamlit run app.py
```

## Deploy na Streamlit Community Cloud

1. Wrzuć kod na GitHub (bez pliku `secrets.toml`)
2. Zaloguj się na [share.streamlit.io](https://share.streamlit.io) przez konto GitHub
3. Kliknij **"New app"** → wybierz repozytorium i ustaw `app.py` jako główny plik
4. W **"Advanced settings"** wklej zawartość `secrets.toml`
5. Kliknij **"Deploy"**

## Aktualizacja aplikacji

Po wprowadzeniu zmian lokalnie:
```bash
git add .
git commit -m "Opis zmian"
git push
```
Streamlit Community Cloud automatycznie wykryje zmiany i wdroży nową wersję.

## Bezpieczeństwo

Plik `secrets.toml` zawiera klucze do Firebase i **nigdy nie powinien trafić na GitHub**. Jest dodany do `.gitignore`. Na Streamlit Cloud sekrety konfiguruje się przez panel "Advanced settings" — nie są przechowywane w repozytorium.
