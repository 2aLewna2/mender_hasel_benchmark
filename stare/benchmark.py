"""Analiza benchmarkingowa menedżerów haseł.

Krok 1: wczytanie danych.
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Folder, w którym leży ten skrypt — dzięki temu ścieżki działają
# niezależnie od tego, z jakiego miejsca uruchomisz program.
FOLDER = Path(__file__).parent


def wczytaj_kryteria() -> pd.DataFrame:
    """Wczytuje opis kryteriów (nazwa, typ S/D, waga) z kryteria.csv."""
    kryteria = pd.read_csv(FOLDER / "kryteria.csv", sep=";")
    # Wagi w pliku są w punktach (suma 100) — zamieniamy na ułamki (suma 1),
    # tak jak we wzorze ze slajdu: W = Σ wᵢ·sᵢ, Σ wᵢ = 1
    kryteria["waga"] = kryteria["waga"] / kryteria["waga"].sum()
    return kryteria.set_index("id")


def wczytaj_dane() -> pd.DataFrame:
    """Wczytuje dane i zamienia je na tabelę: wiersze = firmy, kolumny = kryteria."""
    dane = pd.read_csv(FOLDER / "dane_ujednolicone.csv", sep=";", encoding="utf-8-sig")
    tabela = dane.pivot(index="firma", columns="kryterium", values="wartosc")
    return tabela


def normalizuj(dane: pd.DataFrame, kryteria: pd.DataFrame) -> pd.DataFrame:
    """Sprowadza każde kryterium do przedziału 0–1 metodą min-max (slajd 10).

    Stymulanta (S):   s = (x − min) / (max − min)   → więcej = lepiej
    Destymulanta (D): s = (max − x) / (max − min)   → mniej = lepiej
    """
    minimum = dane.min()  # najmniejsza wartość w każdej kolumnie
    maksimum = dane.max()  # największa wartość w każdej kolumnie
    rozstep = maksimum - minimum

    # Kryterium, w którym wszyscy mają to samo, dzieliłoby przez zero
    # i niczego nie różnicuje (pułapka ze slajdu 13) — zatrzymujemy program.
    bez_roznic = rozstep[rozstep == 0].index.tolist()
    if bez_roznic:
        raise ValueError(f"Kryteria bez zróżnicowania (min = max): {bez_roznic}")

    stymulanty = (dane - minimum) / rozstep
    destymulanty = (maksimum - dane) / rozstep

    # Dla każdej kolumny wybieramy właściwy wzór w zależności od typu S/D
    czy_destymulanta = kryteria["typ"] == "D"
    wynik = stymulanty.copy()
    wynik.loc[:, czy_destymulanta] = destymulanty.loc[:, czy_destymulanta]
    return wynik


def ranking(znormalizowane: pd.DataFrame, kryteria: pd.DataFrame) -> pd.DataFrame:
    """Liczy wynik końcowy W = Σ wᵢ·sᵢ (w skali 0–100) i układa ranking."""
    punkty_wazone = znormalizowane * kryteria["waga"]  # każda kolumna × jej waga
    wynik = punkty_wazone.sum(axis=1) * 100  # suma w wierszu = wynik firmy

    tabela = pd.DataFrame({"wynik": wynik.round(1)})
    tabela = tabela.sort_values("wynik", ascending=False)
    tabela.insert(0, "miejsce", range(1, len(tabela) + 1))
    return tabela


def wyniki_grup(znormalizowane: pd.DataFrame, kryteria: pd.DataFrame) -> pd.DataFrame:
    """Ile punktów (z 100) każda firma zdobyła w każdej grupie kryteriów."""
    punkty_wazone = znormalizowane * kryteria["waga"] * 100
    # .T zamienia wiersze z kolumnami, groupby sumuje kryteria tej samej grupy
    return punkty_wazone.T.groupby(kryteria["grupa"]).sum().T.round(1)


# ---------- Zapis do Excela ----------

PLIK_WYNIKOWY = FOLDER / "menedżer haseł - analiza.xlsx"
NAGLOWEK_TLO = PatternFill("solid", start_color="0B3B60")  # granat jak na slajdach
NAGLOWEK_FONT = Font(bold=True, color="FFFFFF")


def formatuj_naglowek(arkusz, szerokosci: list[int]) -> None:
    """Pogrubiony, kolorowy pierwszy wiersz + szerokości kolumn + zamrożony nagłówek."""
    for komorka in arkusz[1]:  # arkusz[1] = pierwszy wiersz
        komorka.fill = NAGLOWEK_TLO
        komorka.font = NAGLOWEK_FONT
        komorka.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for numer, szerokosc in enumerate(szerokosci, start=1):
        arkusz.column_dimensions[get_column_letter(numer)].width = szerokosc
    arkusz.freeze_panes = "B2"  # nagłówek i pierwsza kolumna zostają przy przewijaniu


def arkusz_kryteria(skoroszyt: Workbook, kryteria_pkt: pd.DataFrame) -> None:
    """Arkusz 'Kryteria': opis kryteriów, wagi w punktach i (formułą) jako ułamek."""
    ws = skoroszyt.create_sheet("Kryteria")
    ws.append(["ID", "Kryterium", "Grupa", "Skala", "Typ (S/D)", "Waga [pkt]", "Waga [ułamek]"])
    for wiersz, (id_, k) in enumerate(kryteria_pkt.iterrows(), start=2):
        # Waga jako ułamek liczona przez Excela: zmienisz punkty → wszystko się przeliczy
        ws.append([id_, k["nazwa"], k["grupa"], k["skala"], k["typ"], k["waga"],
                   f"=F{wiersz}/SUM($F$2:$F${len(kryteria_pkt) + 1})"])
    suma = len(kryteria_pkt) + 2
    ws.append(["", "SUMA", "", "", "", f"=SUM(F2:F{suma - 1})", f"=SUM(G2:G{suma - 1})"])
    ws[f"B{suma}"].font = Font(bold=True)
    formatuj_naglowek(ws, [6, 38, 26, 11, 10, 11, 13])


def arkusz_dane(skoroszyt: Workbook, dane: pd.DataFrame, kryteria: pd.DataFrame) -> None:
    """Arkusz 'Dane': surowe wartości, firmy × kryteria (w kolejności z kryteria.csv)."""
    ws = skoroszyt.create_sheet("Dane")
    ws.append(["Firma"] + [f"{id_} {kryteria.loc[id_, 'nazwa']}" for id_ in dane.columns])
    for firma, wartosci in dane.iterrows():
        ws.append([firma] + wartosci.tolist())
    ws.row_dimensions[1].height = 60
    formatuj_naglowek(ws, [18] + [13] * len(dane.columns))


def arkusz_zrodla(skoroszyt: Workbook, kryteria: pd.DataFrame) -> None:
    """Arkusz 'Źródła': każda wartość z uzasadnieniem, linkiem i oceną pewności."""
    zrodla = pd.read_csv(FOLDER / "dane_ujednolicone.csv", sep=";", encoding="utf-8-sig")
    zrodla = zrodla[zrodla["kryterium"].isin(kryteria.index)]  # bez usuniętego K4
    ws = skoroszyt.create_sheet("Źródła")
    ws.append(["Firma", "ID", "Kryterium", "Wartość", "Uzasadnienie", "Źródło", "Pewność"])
    for _, r in zrodla.iterrows():
        ws.append([r["firma"], r["kryterium"], kryteria.loc[r["kryterium"], "nazwa"],
                   r["wartosc"], r["uzasadnienie"], r["zrodlo"], r["pewnosc"]])
        ws.cell(ws.max_row, 6).hyperlink = r["zrodlo"]  # klikalny link
    formatuj_naglowek(ws, [18, 6, 30, 9, 80, 45, 10])


def arkusz_normalizacja(skoroszyt: Workbook, dane: pd.DataFrame, kryteria: pd.DataFrame) -> None:
    """Arkusz 'Normalizacja': wzory min-max jako ŻYWE formuły Excela odwołujące się do 'Dane'."""
    ws = skoroszyt.create_sheet("Normalizacja")
    ws.append(["Firma"] + [f"{id_} {kryteria.loc[id_, 'nazwa']}" for id_ in dane.columns])
    ostatni = len(dane) + 1  # numer ostatniego wiersza z firmą (wiersz 1 to nagłówek)

    for wiersz, firma in enumerate(dane.index, start=2):
        formuly = [firma]
        for nr, id_ in enumerate(dane.columns):
            kol = get_column_letter(nr + 2)  # kryteria zaczynają się od kolumny B
            x = f"Dane!{kol}{wiersz}"
            mn = f"MIN(Dane!{kol}$2:{kol}${ostatni})"
            mx = f"MAX(Dane!{kol}$2:{kol}${ostatni})"
            typ = f"Kryteria!$E${nr + 2}"  # typ S/D tego kryterium
            formuly.append(f'=IF({typ}="D",({mx}-{x})/({mx}-{mn}),({x}-{mn})/({mx}-{mn}))')
        ws.append(formuly)

    # Wiersz z wagami (z arkusza 'Kryteria') — potrzebny do SUMPRODUCT w rankingu
    ws.append([])
    ws.append(["Waga"] + [f"=Kryteria!$G${nr + 2}" for nr in range(len(dane.columns))])
    ws.cell(ws.max_row, 1).font = Font(bold=True)

    for wiersz in ws.iter_rows(min_row=2, min_col=2):
        for komorka in wiersz:
            komorka.number_format = "0.00"
    ws.row_dimensions[1].height = 60
    formatuj_naglowek(ws, [18] + [13] * len(dane.columns))


def arkusz_ranking(skoroszyt: Workbook, dane: pd.DataFrame) -> None:
    """Arkusz 'Ranking': W = Σ wᵢ·sᵢ formułą SUMPRODUCT + miejsce + wykres słupkowy."""
    ws = skoroszyt.create_sheet("Ranking", 0)  # 0 = wstaw jako pierwszy arkusz
    ws.append(["Firma", "Wynik W (0–100)", "Miejsce"])
    ostatni = len(dane) + 1
    ostatnia_kol = get_column_letter(len(dane.columns) + 1)
    wiersz_wag = ostatni + 2  # tam, gdzie w 'Normalizacja' są wagi

    for wiersz, firma in enumerate(dane.index, start=2):
        ws.append([
            firma,
            f"=ROUND(SUMPRODUCT(Normalizacja!B{wiersz}:{ostatnia_kol}{wiersz},"
            f"Normalizacja!$B${wiersz_wag}:${ostatnia_kol}${wiersz_wag})*100,1)",
            f"=RANK(B{wiersz},$B$2:$B${ostatni})",
        ])
    formatuj_naglowek(ws, [20, 16, 10])

    # Wykres słupkowy (poziomy) — Excel narysuje go z wartości policzonych formułami
    wykres = BarChart()
    wykres.type = "bar"  # "bar" = słupki poziome, "col" = pionowe
    wykres.title = "Ranking menedżerów haseł – wynik W (0–100)"
    wykres.title.overlay = False  # tytuł nad wykresem, a nie na słupkach
    wykres.y_axis.scaling.min = 0
    wykres.y_axis.scaling.max = 100
    wykres.x_axis.scaling.orientation = "maxMin"  # lider na górze
    # Po odwróceniu kolejności oś wartości „ucieka” na górę i nachodzi na tytuł —
    # każemy jej przecinać się z drugą osią na końcu, czyli na dole wykresu.
    wykres.y_axis.crosses = "max"
    # Nowsze wersje openpyxl domyślnie ukrywają osie — włączamy je jawnie.
    wykres.x_axis.delete = False
    wykres.y_axis.delete = False
    wykres.y_axis.majorGridlines = None  # bez siatki — czytelniej
    wykres.legend = None
    wykres.varyColors = False  # wszystkie słupki w jednym kolorze
    wykres.gapWidth = 60  # grubsze słupki (mniejszy odstęp między nimi)
    wartosci = Reference(ws, min_col=2, min_row=1, max_row=ostatni)
    nazwy = Reference(ws, min_col=1, min_row=2, max_row=ostatni)
    wykres.add_data(wartosci, titles_from_data=True)
    wykres.set_categories(nazwy)

    seria = wykres.series[0]
    seria.graphicalProperties.solidFill = "0B3B60"  # granat
    seria.graphicalProperties.line.noFill = True
    # Ostatnie miejsce („my”) na różowo — jak „Nasz sklep” na slajdzie 12
    najslabszy = DataPoint(idx=len(dane) - 1)
    najslabszy.graphicalProperties.solidFill = "E0336E"
    seria.dPt.append(najslabszy)

    # Same liczby na końcu słupków (bez nazwy serii, firmy i znaczka legendy)
    seria.dLbls = DataLabelList()
    seria.dLbls.showVal = True
    seria.dLbls.showSerName = False
    seria.dLbls.showCatName = False
    seria.dLbls.showLegendKey = False
    seria.dLbls.position = "outEnd"
    wykres.height, wykres.width = 9, 16  # w centymetrach
    ws.add_chart(wykres, "E2")


def zapisz_excel(dane: pd.DataFrame, kryteria: pd.DataFrame) -> None:
    """Tworzy nowy plik Excel z analizą (oryginalny arkusz zespołu nie jest ruszany)."""
    skoroszyt = Workbook()
    skoroszyt.remove(skoroszyt.active)  # usuwamy domyślny pusty arkusz

    kryteria_pkt = pd.read_csv(FOLDER / "kryteria.csv", sep=";").set_index("id")
    arkusz_kryteria(skoroszyt, kryteria_pkt)
    arkusz_dane(skoroszyt, dane, kryteria)
    arkusz_zrodla(skoroszyt, kryteria)
    arkusz_normalizacja(skoroszyt, dane, kryteria)
    arkusz_ranking(skoroszyt, dane)

    skoroszyt.save(PLIK_WYNIKOWY)
    print(f"\nZapisano: {PLIK_WYNIKOWY.name}")


if __name__ == "__main__":
    kryteria = wczytaj_kryteria()
    dane = wczytaj_dane()

    # Zostawiamy tylko kryteria, które są w kryteria.csv (K4 usunęliśmy)
    dane = dane[kryteria.index]

    print("KRYTERIA:")
    print(kryteria)
    print("\nDANE (firmy × kryteria):")
    print(dane)

    znormalizowane = normalizuj(dane, kryteria)
    print("\nPO NORMALIZACJI (0 = najgorszy, 1 = najlepszy):")
    print(znormalizowane.round(2).to_string())

    wyniki = ranking(znormalizowane, kryteria)
    print("\nRANKING:")
    print(wyniki.to_string())

    grupy = wyniki_grup(znormalizowane, kryteria).loc[wyniki.index]
    print("\nPUNKTY W GRUPACH (maks.: Bezpieczeństwo 45, Funkcjonalność 24, Koszt 17, UX 14):")
    print(grupy.to_string())

    lider = wyniki.index[0]
    najslabszy = wyniki.index[-1]
    print(f"\nLider: {lider} ({wyniki.loc[lider, 'wynik']} pkt)")
    print(f"Najsłabszy („my”): {najslabszy} ({wyniki.loc[najslabszy, 'wynik']} pkt)")

    zapisz_excel(dane.loc[wyniki.index], kryteria)  # firmy w kolejności rankingu
