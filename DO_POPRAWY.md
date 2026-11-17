# Do poprawy przed oddaniem

Lista uwag po przeglądzie projektu. Liczby są sprawdzone: ranking, analiza wrażliwości i symulacja strategii
dają te same wyniki co w raporcie i na slajdach. Poniżej rzeczy niedokończone albo niejasne.

> Plik roboczy — usunąć przed oddaniem.

## Raport i prezentacja

- [ ] **Autorzy** — placeholder `[imiona i nazwiska…]` w raporcie (strona tytułowa) i na slajdzie 1.
- [ ] **Luka po K4** — w tabelach jest K3 → K5, nigdzie nie ma wprost napisane, że K4 to usunięty monitoring wycieków.
  Do decyzji:
  - (a) zostawić numerację i dopisać pod tabelą kryteriów jedno zdanie, np. *„Numeracja z wersji roboczej – K4
    (monitoring wycieków) usunięto po zebraniu danych, bo miały go wszystkie badane produkty.”*
  - (b) przenumerować K5–K16 na K4–K15 (zmiana w CSV, kodzie, Excelu, raporcie i slajdach).
- [ ] **Slajd 5: „Unikaliśmy pułapek ze slajdu 13”** — chodzi o slajd z zajęć, ale w naszej prezentacji slajd 13
  to harmonogram. Zmienić na np. „pułapek omawianych na zajęciach”.
- [ ] **Slajd 8: wariant „tylko 7 menedżerów dedykowanych”** — w obliczeniach usunięte jest też K5 (E2E),
  bo wszystkie dedykowane je mają (min = max). Raport to zaznacza, slajd nie.
- [ ] **K11 (przejrzystość interfejsu)** — raport mówi „do weryfikacji testem zespołu”. Zrobić test albo zmienić zapis.
- [ ] **Słownictwo w strategii** — „Trust Center”, „CISO”, „Head of Mobile”, „CXP/CXF”, „bug bounty”:
  każdy powinien umieć wytłumaczyć te pojęcia bez notatek.

## Dane i dokumentacja

- [ ] **`kryteria.md`** — nagłówek „wersja robocza v1” i „16 kryteriów”; obowiązuje v2 z 15 kryteriami.
- [ ] **`dane_ujednolicone.csv`** — wiersze K4 nadal są w pliku (kod je odfiltrowuje). Usunąć albo zostawić świadomie.
- [ ] **Wartości z pewnością „low” (13 szt.)** — przejrzeć, czy da się je potwierdzić; mogą paść pytania.
- [ ] **Excel vs Python** — raport twierdzi, że dają te same wyniki. Otworzyć Excela i sprawdzić samemu.

## Kod

- [ ] **`benchmark.py`** — opis na górze pliku to nadal „Krok 1: wczytanie danych”.
- [ ] **`dashboard.py`, linie 10–13** — komentarz „Te same funkcje, których używa benchmark.py” stoi nad importem
  plotly zamiast nad importem z `benchmark`.
- [ ] **Komentarze w kodzie** — każdy komentarz powinien umieć wytłumaczyć ktoś z zespołu
  (np. te o osiach wykresu w openpyxl). Jeśli nikt nie umie — uprościć.
- [ ] **`requirements.txt`** — 44 paczki z `pip freeze`; bezpośrednio używamy 6
  (pandas, openpyxl, streamlit, plotly, matplotlib, python-docx).

## Forma oddania

- [ ] **Ustalić, jak oddajemy pracę** — link do repo na GitHubie czy sama paczka plików
  (raport, prezentacja, Excel + ewentualnie ZIP z kodem). Jeśli link do repo:
  - repo publiczne czy prywatne z dostępem dla prowadzącej,
  - przed oddaniem usunąć ten plik i inne pliki robocze,
  - prowadząca zobaczy całą historię commitów.

## Propozycja: rozdzielić `narzedzia/raport.py`

W `raport.py` są obliczenia, których nie ma nigdzie indziej: luki LastPass wobec lidera, analiza wrażliwości
(4 warianty) i symulacja strategii (10. → 8. → 7. → 3. miejsce). To najważniejsze wnioski, a są schowane
w skrypcie generującym Worda. Do tego cała treść raportu jest zapisana w kodzie Pythona.

Propozycja (na osobnej gałęzi, po akceptacji zespołu):

1. **Obliczenia → `benchmark.py`** jako funkcje `luki()`, `analiza_wrazliwosci()`, `symulacja_strategii()`,
   z wynikami wypisywanymi w terminalu obok rankingu.
2. **Wykresy → osobny `wykresy.py`** w głównym folderze.
3. **Tekst raportu** — tylko w Wordzie; `raport.py` do usunięcia (zostaje w historii gita).

## Pytania, na które warto mieć odpowiedź

- Dlaczego normalizacja min-max?
- Dlaczego w symulacji LastPass (66,0 pkt) wyprzedza 1Password, które miało 66,4?
  (zmiana danych LastPass przesuwa min/max w kryteriach, więc 1Password spada do 65,4)
- Dlaczego wariant z samymi dedykowanymi nie ma K5?
- Dlaczego dashboard w Streamlit i co robi `@st.cache_data`?
