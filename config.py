# =============================================================================
# config.py — stałe konfiguracyjne aplikacji
# =============================================================================
# Ten plik przechowuje wszystkie "magiczne stringi" i listy wartości
# używane w wielu miejscach aplikacji.
#
# Zasada: jeśli jakaś wartość pojawia się w więcej niż jednym pliku —
# powinna mieszkać tutaj. Dzięki temu zmiana (np. dodanie nowej kategorii)
# wymaga edycji tylko tego jednego pliku, a nie szukania po całym projekcie.
#
# Importuj stałe w innych plikach przez:
#   from config import KATEGORIE, PLATFORMY, FORMAT_DATY
# =============================================================================

# Kategorie produktów — używane w formularzu dodawania i w edycji
KATEGORIE = ["Kurtki", "Sukienki", "Spodnie", "Buty", "Torebki", "Inne"]

# Platformy sprzedaży — używane w dialogu sprzedaży i edycji
PLATFORMY = ["Vinted", "OLX", "Inne"]

# Dowody zakupu — używane w formularzu dodawania i w edycji
DOWODY_ZAKUPU = ["Paragon", "Faktura"]

# Możliwe statusy produktu — odzwierciedlają cykl życia produktu:
# kupiony → wystawiony → sprzedany
STATUSY = ["kupiony", "wystawiony", "sprzedany"]

# Format daty używany wszędzie w aplikacji — przy zapisie do Firebase
# i przy odczycie. Zmiana tutaj automatycznie zmienia format w całej aplikacji.
# DD.MM.YYYY — format czytelny dla użytkownika (np. 14.03.2026)
FORMAT_DATY = "%d.%m.%Y"