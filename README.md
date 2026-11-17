# Benchmarking menedżerów haseł

Projekt na Podstawy zarządzania (ćwiczenia 06). Porównujemy 10 menedżerów haseł na 15 kryteriach,
wyłaniamy lidera i piszemy strategię dla najsłabszego (LastPass).

## Co jest w folderze

| Plik | Co to jest |
|------|------------|
| `Raport - benchmarking menedżerów haseł.docx` | raport do oddania (analiza + strategia) |
| `Benchmarking menedżerów haseł.pptx` | prezentacja na zajęcia (z notatkami mówcy) |
| `menedżer haseł - analiza.xlsx` | Excel: dane, normalizacja i ranking na formułach, wykres, źródła |
| `kryteria.csv` | kryteria: nazwa, grupa, skala, typ S/D, **waga w punktach** |
| `dane_ujednolicone.csv` | wartości dla każdej firmy i kryterium + uzasadnienie + link do źródła |
| `kryteria.md` | opis kryteriów, uzasadnienie wag, reguły ujednolicenia danych |
| `benchmark.py` | liczy normalizację, wagi i ranking, zapisuje Excela |
| `dashboard.py` | interaktywny dashboard (Streamlit) |
| `narzedzia/raport.py` | generuje raport Word i wykresy w `wykresy/` |
| `wykresy/` | wykresy PNG użyte w raporcie |

## Pierwsze uruchomienie (raz na komputer)

Potrzebny Python 3.11+. W terminalu, w tym folderze:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Codzienne użycie

Za każdym razem w nowym terminalu najpierw: `source .venv/bin/activate`

| Chcę… | Komenda |
|-------|---------|
| przeliczyć ranking i wygenerować Excela | `python benchmark.py` |
| otworzyć dashboard | `streamlit run dashboard.py` → przeglądarka, http://localhost:8501 (zatrzymanie: `Ctrl+C`) |
| wygenerować raport Word od nowa | `python narzedzia/raport.py` ⚠️ nadpisuje raport — ręczne poprawki w Wordzie przepadną |

## Jak zmienić dane albo wagi

1. Zmień wagę w `kryteria.csv` albo wartość w `dane_ujednolicone.csv` (Excel: separator średnik).
2. Uruchom `python benchmark.py` — nowy Excel i ranking w terminalu.
3. Dashboard odśwież przyciskiem **Rerun**.

W pliku Excel można też zmieniać wartości bezpośrednio (arkusze *Dane* i *Kryteria*) — ranking przeliczy się sam,
ale przy następnym `python benchmark.py` plik zostanie wygenerowany od nowa z CSV.

## Metoda w skrócie

- normalizacja min-max: stymulanta `s = (x − min)/(max − min)`, destymulanta `s = (max − x)/(max − min)`
- wynik: `W = Σ wᵢ · sᵢ × 100`, suma wag = 1
- kryterium, w którym wszyscy mają to samo (min = max), zatrzymuje program z komunikatem — nic nie różnicuje
