# Benchmarking menedżerów haseł (wersja 2, uproszczona)

Porównujemy 10 menedżerów haseł na 15 kryteriach, wybieramy lidera i najsłabszego.

## Pliki

| Plik | Co to jest |
|------|------------|
| `menedżer haseł-2.xlsx` | surowe dane: menedżerowie, kryteria, S/D, wagi |
| `Analiza benchmarkingowa menedżerów haseł.docx` | opis kryteriów, wag i wniosków |
| `normalizacja_v2.ipynb` | notatnik: normalizacja, suma ważona, ranking i zapis Excela z wynikami i wykresem |

## Jak uruchomić notatnik (bez instalowania czegokolwiek)

1. Otwórz notatnik w Google Colab:
   https://colab.research.google.com/github/2aLewna2/mender_hasel_benchmark/blob/main/normalizacja_v2.ipynb
   (link działa, gdy repo jest publiczne, a notatnik jest już na gałęzi `main`)
2. *Środowisko wykonawcze → Uruchom wszystko*.
3. Wgraj `menedżer haseł-2.xlsx`, kiedy notatnik o to poprosi.
4. Pobierze się `menedzer_hasel_wyniki.xlsx` z tabelą po normalizacji, rankingiem i wykresem.

Lokalnie (Jupyter / VS Code): Excel musi leżeć w tym samym folderze co notatnik. Wtedy notatnik nie pyta o upload.

## Metoda w skrócie

- TAK/NIE → 1/0 (dla destymulanty odwrotnie)
- liczby i skala 1–5 → min-max: stymulanta `(x − min)/(max − min)`, destymulanta `(max − x)/(max − min)`
- „Brak planu płatnego” w cenie → 1
- wynik: `W = Σ waga · wynik × 100` (wagi sumują się do 1)

## Dashboard (opcja plotly)

Na końcu notatnika jest sekcja **7. Dashboard** z interaktywnymi wykresami (plotly):
ranking z wyróżnionym liderem i najsłabszym, mapa wyników 0–1 oraz porównanie dwóch menedżerów
(wkład punktowy każdego kryterium) z wyborem z listy. Działa w Colabie od razu.
Podgląd notatnika na GitHubie nie pokazuje wykresów plotly, bo do tego trzeba go uruchomić w Colabie.
