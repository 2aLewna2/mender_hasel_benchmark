"""Generator raportu Word i wykresów PNG.

Uruchomienie (z folderu projektu, z aktywnym .venv):  python narzedzia/raport.py
Tworzy: 'Raport - benchmarking menedżerów haseł.docx' i folder wykresy/.
UWAGA: nadpisuje raport — ręczne poprawki w Wordzie trzeba wtedy nanieść ponownie.
"""
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent  # folder projektu
sys.path.insert(0, str(PROJ))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from benchmark import normalizuj, ranking, wczytaj_dane, wczytaj_kryteria, wyniki_grup

GRANAT, ROZ, MORSKI, SZARY = "#0B3B60", "#E0336E", "#2A9D8F", "#6B7785"
OUT = PROJ / "Raport - benchmarking menedżerów haseł.docx"
WYK = PROJ / "wykresy"
WYK.mkdir(exist_ok=True)

# ---------------- dane i obliczenia ----------------
kryt = wczytaj_kryteria()
dane = wczytaj_dane()[kryt.index]
norm = normalizuj(dane, kryt)
rank = ranking(norm, kryt)
grupy = wyniki_grup(norm, kryt).loc[rank.index]
kpkt = pd.read_csv(PROJ / "kryteria.csv", sep=";").set_index("id")
zrodla = pd.read_csv(PROJ / "dane_ujednolicone.csv", sep=";", encoding="utf-8-sig")
zrodla = zrodla[zrodla["kryterium"].isin(kryt.index)]
LIDER, MY = rank.index[0], rank.index[-1]
luki = ((norm.loc[LIDER] - norm.loc[MY]) * kryt["waga"] * 100).round(1).sort_values(ascending=False)

def scen(k_mod=None, d_mod=None):
    k = kryt if k_mod is None else k_mod
    d = dane if d_mod is None else d_mod
    return ranking(normalizuj(d, k), k)

k_rowne = kryt.copy(); k_rowne["waga"] = 1 / len(k_rowne)
k_bez6 = kryt.copy(); k_bez6.loc["K6", "waga"] = 0; k_bez6["waga"] /= k_bez6["waga"].sum()
k_ded = kryt.drop("K5"); k_ded["waga"] /= k_ded["waga"].sum()
d_ded = dane.drop(["Apple Hasła", "Google", "Microsoft (Edge)"])[k_ded.index]
scenariusze = {
    "Wagi bazowe": rank,
    "Wagi równe (każde kryterium 1/15)": scen(k_rowne),
    "Bez kryterium K6 (incydenty)": scen(k_bez6),
    "Tylko menedżery dedykowane (7 firm, bez K5)": scen(k_ded, d_ded),
}

# Symulacja efektu strategii (wartości LastPass po wdrożeniu działań)
etapy = [("Stan obecny", {}),
         ("Po szybkich wygranych\n(TOTP, oceny 4,5, CXP)", {"K14": 1, "K12": 4.5, "K9": 5}),
         ("+ Trust Center, audyty,\njęzyk polski", {"K8": 5, "K16": 1}),
         ("+ open source\naplikacji klienckich", {"K7": 1})]
sym, d_sym = [], dane.copy()
for nazwa, zm in etapy:
    for c, v in zm.items():
        d_sym.loc[MY, c] = v
    r = ranking(normalizuj(d_sym, kryt), kryt)
    sym.append((nazwa, int(r.loc[MY, "miejsce"]), float(r.loc[MY, "wynik"])))

# ---------------- wykresy ----------------
plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#B0B7C0",
                     "xtick.color": "#4A5560", "ytick.color": "#222"})

def wykres_rankingu():
    fig, ax = plt.subplots(figsize=(7, 3.8), dpi=200)
    firmy = rank.index[::-1]
    kol = [ROZ if f == MY else MORSKI if f == LIDER else GRANAT for f in firmy]
    ax.barh(firmy, rank.loc[firmy, "wynik"], color=kol, height=0.62)
    for i, f in enumerate(firmy):
        ax.text(rank.loc[f, "wynik"] + 1, i, f"{rank.loc[f, 'wynik']:.1f}".replace(".", ","), va="center", fontsize=9, color="#222")
    ax.set_xlim(0, 100); ax.set_xlabel("Wynik W (0–100)", color="#4A5560")
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    fig.tight_layout(); p = WYK / "1_ranking.png"; fig.savefig(p); plt.close(fig); return p

def wykres_luk():
    l = luki[luki > 0][::-1]
    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=200)
    ax.barh([f"{i} {kryt.loc[i, 'nazwa']}" for i in l.index], l.values, color=ROZ, height=0.62)
    for i, v in enumerate(l.values):
        ax.text(v + 0.15, i, f"{v:.1f}".replace(".", ","), va="center", fontsize=9)
    ax.set_xlabel(f"Punkty tracone do lidera ({LIDER})", color="#4A5560")
    ax.spines["left"].set_visible(False); ax.tick_params(axis="y", length=0)
    fig.tight_layout(); p = WYK / "2_luki.png"; fig.savefig(p); plt.close(fig); return p

DZIALANIA = [  # id, krótka nazwa, wpływ, nakład, ćwiartka
    ("D1", "TOTP w planach Premium/Families", 3.3, 1.0, "Szybka wygrana"),
    ("D2", "Program poprawy ocen w sklepach", 4.0, 2.0, "Szybka wygrana"),
    ("D3", "Trust Center + publikowane audyty", 5.0, 4.0, "Projekt strategiczny"),
    ("D4", "Otwarcie kodu aplikacji klienckich", 4.0, 4.4, "Projekt strategiczny"),
    ("D5", "Eksport szyfrowany + standard CXP", 3.0, 2.3, "Szybka wygrana"),
    ("D6", "Przywrócenie języka polskiego", 2.0, 1.6, "Drobne usprawnienie"),
    ("D7", "Obniżka ceny do poziomu lidera", 2.0, 4.6, "Odrzucamy"),
]

def wykres_macierzy():
    fig, ax = plt.subplots(figsize=(7, 5), dpi=200)
    G = 2.75  # granica ćwiartek: ocena >= 3 = wysoki wpływ / wysoki nakład
    tla = [((0.5, G), 5.5 - G, "#D9F0EC", "Szybkie wygrane\nwdrażaj od razu"), ((G, G), 5.5 - G, "#DCE5EE", "Projekty strategiczne\nzaplanuj i zabezpiecz zasoby"),
           ((0.5, 0.5), G - 0.5, "#EEF7F5", "Drobne usprawnienia\nprzy okazji"), ((G, 0.5), G - 0.5, "#FADDE6", "Odrzuć\nmały wpływ, duży koszt")]
    for (x, y), h, c, t in tla:
        w_ = (G - 0.5) if x == 0.5 else (5.5 - G)
        ax.add_patch(plt.Rectangle((x, y), w_, h, color=c, zorder=0, lw=0))
        ax.text(x + 0.12, y + h - 0.12, t, va="top", fontsize=8.5, color="#33404D", fontweight="bold")
    for i, n, w, k, _ in DZIALANIA:
        ax.scatter(k, w, s=140, color=ROZ if i == "D7" else GRANAT, zorder=3, edgecolor="white", linewidth=1.5)
        prawa = k > 3.5  # podpis po lewej stronie punktów przy prawej krawędzi
        if prawa:  # podpis pod punktem, wyrównany do prawej — nie wychodzi poza wykres i nie nachodzi na inne
            ax.text(k + 0.12, w - 0.3, f"{i} {n}", fontsize=8, va="center", zorder=4, color="#222", ha="right")
        else:
            ax.text(k + 0.14, w - 0.04, f"{i} {n}", fontsize=8, va="center", zorder=4, color="#222")
    ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
    ax.set_xlabel("Nakład / trudność wdrożenia (1–5) →", color="#4A5560")
    ax.set_ylabel("Wpływ na pozycję konkurencyjną (1–5) →", color="#4A5560")
    ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
    fig.tight_layout(); p = WYK / "3_macierz.png"; fig.savefig(p); plt.close(fig); return p

def wykres_sciezki():
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=200)
    x = range(len(sym)); w = [s[2] for s in sym]
    ax.bar(x, w, color=[ROZ] + [GRANAT] * (len(sym) - 1), width=0.55)
    for i, (_, m, v) in enumerate(sym):
        ax.text(i, v + 2, f"{v:.1f} pkt · {m}. miejsce".replace(".", ",", 1), ha="center", fontsize=9)
    ax.set_xticks(list(x)); ax.set_xticklabels([s[0] for s in sym], fontsize=8.5)
    ax.set_ylim(0, 85); ax.set_ylabel("Wynik W LastPass", color="#4A5560")
    fig.tight_layout(); p = WYK / "4_sciezka.png"; fig.savefig(p); plt.close(fig); return p

p_rank, p_luki, p_macierz, p_sciezka = wykres_rankingu(), wykres_luk(), wykres_macierzy(), wykres_sciezki()

# ---------------- dokument ----------------
doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
for s in ("left_margin", "right_margin"): setattr(sec, s, Cm(2.0))
sec.top_margin = sec.bottom_margin = Cm(2.0)

st = doc.styles
st["Normal"].font.name = "Calibri"; st["Normal"].font.size = Pt(11)
st["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st["Normal"].paragraph_format.space_after = Pt(6)
st["Normal"].paragraph_format.line_spacing = 1.15
for nazwa, rozm, przed in [("Heading 1", 16, 18), ("Heading 2", 13, 12), ("Title", 26, 0)]:
    s = st[nazwa]; s.font.name = "Calibri"; s.font.size = Pt(rozm); s.font.bold = True
    s.font.color.rgb = RGBColor.from_string(GRANAT[1:])
    s.element.rPr.rFonts.set(qn("w:asciiTheme"), "") if False else None
    rf = s.element.rPr.rFonts; [rf.attrib.pop(qn(a), None) for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")]
    rf.set(qn("w:ascii"), "Calibri"); rf.set(qn("w:hAnsi"), "Calibri")
    s.paragraph_format.space_before = Pt(przed); s.paragraph_format.space_after = Pt(6); s.paragraph_format.keep_with_next = True

def pole(par, kod):
    r = par.add_run()
    for typ, txt in (("begin", None), (None, kod), ("end", None)):
        if typ:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), typ); r._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)

stopka = sec.footer.paragraphs[0]; stopka.alignment = WD_ALIGN_PARAGRAPH.CENTER
stopka.add_run("Benchmarking menedżerów haseł · strona ").font.size = Pt(9); pole(stopka, "PAGE")

def akapit(tekst, bold_prefix=None, styl=None, rozmiar=None, kursywa=False):
    p = doc.add_paragraph(style=styl)
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    r = p.add_run(tekst); r.italic = kursywa
    if rozmiar: r.font.size = Pt(rozmiar)
    return p

def punkt(tekst, bold_prefix=None):
    return akapit(tekst, bold_prefix, styl="List Bullet")

def cieniuj(kom, kolor):
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), kolor)
    kom._tc.get_or_add_tcPr().append(shd)

def tabela(naglowki, wiersze, szer_cm, rozmiar=9, wyroznij=None, wyrownaj_od=1):
    t = doc.add_table(rows=1, cols=len(naglowki)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(naglowki):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(str(h)); r.bold = True
        r.font.size = Pt(rozmiar); r.font.color.rgb = RGBColor(255, 255, 255); cieniuj(c, GRANAT[1:])
    for nr, w in enumerate(wiersze):
        cells = t.add_row().cells
        for i, v in enumerate(w):
            cells[i].text = ""; p = cells[i].paragraphs[0]; r = p.add_run(str(v)); r.font.size = Pt(rozmiar)
            if i >= wyrownaj_od and isinstance(v, (int, float)): p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if wyroznij and wyroznij(w):
                cieniuj(cells[i], "FBE3EB")
            elif nr % 2:
                cieniuj(cells[i], "F2F5F8")
    for row in t.rows:
        for i, c in enumerate(row.cells):
            c.width = Cm(szer_cm[i])
            for p in c.paragraphs: p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    # powtarzaj nagłówek na kolejnych stronach
    trPr = t.rows[0]._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def obraz(sciezka, podpis, szer=16.5):
    doc.add_picture(str(sciezka), width=Cm(szer)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = akapit(podpis, rozmiar=9, kursywa=True); p.alignment = WD_ALIGN_PARAGRAPH.CENTER

def liczba(x, miejsca=1):
    return f"{x:.{miejsca}f}".replace(".", ",")

def nowa_strona():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ----- strona tytułowa -----
for _ in range(6): doc.add_paragraph()
doc.add_paragraph("Analiza benchmarkingowa menedżerów haseł", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
p = akapit("oraz strategia działania dla najsłabszego podmiotu w rankingu", rozmiar=14); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
for _ in range(4): doc.add_paragraph()
for linia in ["Podstawy zarządzania – ćwiczenia 06: benchmarking", "Prowadząca: dr inż. Marta Pawłowska-Nowak", "",
              "Autorzy: [imiona i nazwiska członków zespołu]", "", "Listopad 2026 · dane według stanu na 16.11.2026"]:
    p = akapit(linia, rozmiar=12); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
nowa_strona()

# ----- 1. Wprowadzenie -----
doc.add_heading("1. Cel i zakres analizy", 1)
akapit("Celem pracy jest porównanie dziesięciu menedżerów haseł dostępnych na rynku konsumenckim, wyłonienie lidera "
       "i zaproponowanie strategii dla organizacji, która w rankingu wypada najsłabiej. Zgodnie z założeniem zespołu "
       f"nie tworzymy fikcyjnej firmy – „naszą organizacją” jest podmiot z ostatniego miejsca rankingu, czyli {MY}. "
       "Z jego perspektywy formułujemy wnioski i strategię (analogicznie do przykładu salonu Grisbi-Tre z zajęć).")
punkt("benchmarking zewnętrzny (konkurencyjny) – porównanie z konkurentami w tej samej branży;", "Rodzaj: ")
punkt("produkty i usługi – cechy oferty widziane oczami klienta indywidualnego;", "Przedmiot: ")
punkt("oficjalne cenniki i dokumentacja producentów, strony bezpieczeństwa i raporty z audytów, repozytoria GitHub, "
      "App Store i Google Play, recenzje branżowe oraz publikacje prasowe o incydentach. Źródło każdej wartości podano "
      "w arkuszu „Źródła” pliku Excel i w załączniku B.", "Źródła danych: ")
punkt("arkusz Excel z formułami (normalizacja, wagi, ranking, wykres), skrypt w Pythonie automatyzujący obliczenia "
      "oraz interaktywny dashboard (Streamlit) z analizą wrażliwości.", "Narzędzia: ")

# ----- 2. Metodyka -----
doc.add_heading("2. Metodyka", 1)
doc.add_heading("2.1. Badane podmioty", 2)
OPISY = {
    "Apple Hasła": ("wbudowany (ekosystem Apple)", "darmowy, część iOS/macOS"),
    "Google": ("wbudowany (Chrome/Android)", "darmowy, część konta Google"),
    "Microsoft (Edge)": ("wbudowany (przeglądarka Edge)", "darmowy; od 2025 r. zastępuje Authenticator"),
    "1Password": ("dedykowany", "subskrypcja, brak planu darmowego"),
    "Bitwarden": ("dedykowany, open source", "freemium"),
    "LastPass": ("dedykowany", "freemium"),
    "Dashlane": ("dedykowany", "subskrypcja (plan darmowy wycofany 09.2025)"),
    "NordPass": ("dedykowany (Nord Security)", "freemium"),
    "Proton Pass": ("dedykowany, open source (Proton)", "freemium"),
    "Keeper": ("dedykowany", "freemium z limitem"),
}
tabela(["Produkt", "Typ", "Model biznesowy"], [[f, *OPISY[f]] for f in OPISY], [4.0, 6.0, 7.0], rozmiar=9.5,
       wyroznij=lambda w: w[0] == MY)

doc.add_heading("2.2. Kryteria porównawcze", 2)
akapit("Przyjęto 15 kryteriów łączących trzy rodzaje skal: binarną 0/1 (5 kryteriów), porządkową 1–5 (5) i ilościową (5). "
       "Każde kryterium oznaczono jako stymulantę (S – więcej znaczy lepiej) albo destymulantę (D – mniej znaczy lepiej).")
OPIS_POM = {
    "K1": "1 = brak planu darmowego … 5 = całkowicie darmowy", "K2": "najtańszy plan indywidualny, cena regularna roczna",
    "K3": "Windows, macOS, Linux, iOS, Android, 4 przeglądarki, sejf webowy (0–10)", "K5": "dostawca nie ma dostępu do haseł, domyślnie",
    "K6": "potwierdzone wycieki danych użytkowników 2015–2026", "K7": "publiczny kod aplikacji klienckich",
    "K8": "1 = brak … 5 = regularne, publikowane audyty + certyfikaty + bug bounty", "K9": "formaty importu/eksportu, eksport szyfrowany, standard CXP",
    "K10": "1 = brak … 5 = grupy, uprawnienia i link dla osób bez konta", "K11": "ocena na podstawie recenzji (do weryfikacji testem zespołu)",
    "K12": "średnia App Store (USA) i Google Play", "K13": "liczba metod zabezpieczenia konta (TOTP, FIDO2, passkey, SMS…)",
    "K14": "przechowywanie i generowanie kodów 2FA w planie indywidualnym", "K15": "zaufana osoba może przejąć dostęp do sejfu",
    "K16": "aplikacja dostępna po polsku",
}
tabela(["ID", "Kryterium", "Skala", "Typ", "Waga", "Sposób pomiaru"],
       [[i, kpkt.loc[i, "nazwa"], kpkt.loc[i, "skala"], kpkt.loc[i, "typ"], f"{kpkt.loc[i, 'waga']}%", OPIS_POM[i]] for i in kpkt.index],
       [1.1, 4.4, 1.8, 1.1, 1.3, 7.3], rozmiar=8.5)

doc.add_heading("2.3. Wagi i ich uzasadnienie", 2)
akapit("Wagi ustalono metodą punktową (100 pkt) przed zebraniem danych, aby nie dopasowywać ich do wyniku. Najpierw "
       "rozdzielono punkty między cztery grupy według znaczenia dla klienta, następnie między kryteria w grupie.")
tabela(["Grupa", "Pkt", "Uzasadnienie"], [
    ["Bezpieczeństwo", 45, "Menedżer haseł to „sejf” – klient kupuje przede wszystkim zaufanie; jeden wyciek potrafi zniszczyć markę."],
    ["Funkcjonalność", 24, "Menedżer musi działać wszędzie, gdzie użytkownik się loguje; pozostałe funkcje są dodatkami."],
    ["Koszt", 17, "Klient indywidualny jest wrażliwy cenowo, a darmowe menedżery wbudowane są silną alternatywą."],
    ["Doświadczenie użytkownika", 14, "Wygoda decyduje o tym, czy użytkownik faktycznie korzysta z menedżera; język polski ważny lokalnie, ale niszowy."],
], [4.2, 1.3, 11.5], rozmiar=9.5)

doc.add_heading("2.4. Normalizacja i wynik końcowy", 2)
akapit("Wartości wszystkich kryteriów sprowadzono do przedziału 0–1 metodą min-max:")
punkt("s = (x − min) / (max − min),", "stymulanta: ")
punkt("s = (max − x) / (max − min),", "destymulanta: ")
punkt("W = Σ wᵢ · sᵢ (Σ wᵢ = 1), przeskalowany do 0–100.", "wynik końcowy: ")
akapit("Obliczenia wykonano równolegle w Pythonie i formułami Excela (SUMPRODUCT) – oba sposoby dają identyczne wyniki.")

doc.add_heading("2.5. Jakość danych – decyzje zespołu", 2)
akapit("Przy doborze kryteriów i porządkowaniu danych uwzględniono typowe pułapki analizy benchmarkingowej:")
punkt("biometria i dwuetapowa weryfikacja (0/1) oraz monitoring wycieków – mają je wszystkie badane produkty, więc nie różnicują "
      "(min = max). Dwuetapową weryfikację zamieniono na liczbę metod (K13).", "Usunięte kryteria bez zróżnicowania: ")
punkt("„wersja darmowa” i „limit w wersji darmowej” mierzyły to samo – połączono je w jedno kryterium 1–5 (K1).", "Zdublowane kryteria: ")
punkt("liczono tylko incydenty z wyciekiem danych użytkowników (bez podatności zgłoszonych przez badaczy); liczono tylko funkcje "
      "dostępne w planach indywidualnych (nie biznesowych); przyjęto cenę regularną zamiast promocyjnej.", "Jednolite reguły: ")

# ----- 3. Wyniki -----
doc.add_heading("3. Wyniki analizy", 1)
doc.add_heading("3.1. Zebrane dane", 2)
wiersze = []
for f in rank.index:
    wiersze.append([f] + [liczba(v, 2) if i in ("K2", "K12") else int(v) for i, v in dane.loc[f].items()])
tabela(["Firma"] + list(kryt.index), wiersze, [2.9] + [0.94] * 15, rozmiar=7.5, wyroznij=lambda w: w[0] == MY)
akapit("Firmy uporządkowano według miejsca w rankingu. Nazwy kryteriów – tabela w punkcie 2.2.", rozmiar=9, kursywa=True)

doc.add_heading("3.2. Ranking i lider", 2)
obraz(p_rank, f"Rys. 1. Ranking menedżerów haseł (lider – kolor morski, {MY} – różowy).")
akapit("Punkty zdobyte w poszczególnych grupach kryteriów:")
gr_kol = ["Bezpieczeństwo", "Funkcjonalność", "Koszt", "Doświadczenie użytkownika"]
tabela(["Miejsce", "Firma", "Bezpieczeństwo /45", "Funkcjonalność /24", "Koszt /17", "UX /14", "Wynik W"],
       [[int(rank.loc[f, "miejsce"]), f] + [liczba(grupy.loc[f, g]) for g in gr_kol] + [liczba(rank.loc[f, "wynik"])] for f in rank.index],
       [1.5, 3.3, 2.7, 2.7, 2.0, 1.8, 2.0], rozmiar=9, wyroznij=lambda w: w[1] == MY)
akapit(f"Liderem jest {LIDER} ({liczba(rank.loc[LIDER, 'wynik'])} pkt) – jako jedyny zdobył maksimum w bezpieczeństwie i funkcjonalności. "
       "Źródła jego przewagi, czyli dobre praktyki, od których warto się uczyć:")
for t in ["otwarty kod źródłowy i regularnie publikowane niezależne audyty – zaufanie budowane przez przejrzystość,",
          "najtańszy plan płatny wśród menedżerów dedykowanych (19,80 USD/rok) i darmowa wersja bez limitu haseł i urządzeń,",
          "pełne pokrycie platform (10/10) oraz 7 metod zabezpieczenia konta,",
          "kompletny pakiet funkcji w planie indywidualnym: kody TOTP, dostęp awaryjny, eksport szyfrowany, język polski."]:
    punkt(t)
akapit(f"Ostatnie miejsce zajmuje {MY} ({liczba(rank.loc[MY, 'wynik'])} pkt) – najsłabszy wynik w bezpieczeństwie "
       f"({liczba(grupy.loc[MY, 'Bezpieczeństwo'])}/45) i doświadczeniu użytkownika ({liczba(grupy.loc[MY, 'Doświadczenie użytkownika'])}/14). "
       "Wbudowane menedżery Apple, Google i Microsoft zdobywają komplet punktów za koszt, ale przegrywają funkcjonalnością.")

doc.add_heading("3.3. Analiza wrażliwości", 2)
akapit("Aby sprawdzić, czy wynik nie zależy od subiektywnie dobranych wag, ranking przeliczono w czterech wariantach "
       "(w dashboardzie można to robić suwakami):")
tabela(["Wariant", "Lider", "Ostatnie miejsce", f"Miejsce {MY}"],
       [[n, r.index[0], r.index[-1], f"{int(r.loc[MY, 'miejsce'])} / {len(r)}"] for n, r in scenariusze.items()],
       [7.0, 3.2, 3.6, 3.2], rozmiar=9.5)
akapit(f"Lider jest stabilny – {LIDER} wygrywa w każdym wariancie. Ostatnie miejsce {MY} wynika przede wszystkim z historii "
       "incydentów: po pominięciu kryterium K6 firma awansuje na 8. miejsce. To kluczowy wniosek dla strategii – problemem "
       "jest przede wszystkim zaufanie, a nie sama funkcjonalność produktu.")

# ----- 4. Strategia -----
nowa_strona()
doc.add_heading(f"4. Strategia dla organizacji: {MY}", 1)
doc.add_heading("4.1. Diagnoza – luki wobec lidera", 2)
akapit(f"Dla każdego kryterium policzono, ile punktów rankingu {MY} traci do lidera: (s_lider − s_my) · waga · 100. "
       f"Łączny dystans wynosi {liczba(rank.loc[LIDER, 'wynik'] - rank.loc[MY, 'wynik'])} pkt.")
obraz(p_luki, f"Rys. 2. Punkty tracone przez {MY} względem lidera na poszczególnych kryteriach.")
akapit(f"Największą luką są incydenty bezpieczeństwa (K6, {liczba(luki['K6'])} pkt). Tej luki nie da się zamknąć szybko – "
       "historii wycieków nie można wymazać, a liczba zmaleje dopiero, gdy minie okres objęty badaniem. Dlatego strategia "
       "nie próbuje „poprawić wskaźnika”, tylko odbudowuje zaufanie innymi drogami (audyty, przejrzystość, otwarty kod) "
       "i dba o to, by nie pojawił się kolejny incydent.")

doc.add_heading("4.2. Kluczowe luki", 2)
for tyt, opis in [
    ("Luka 1 – zaufanie i przejrzystość bezpieczeństwa (K6, K8; 22 pkt). ",
     "Trzy wycieki (2015, 2022, 2026) i brak regularnie publikowanych raportów z audytów. Lider pokazuje, że zaufanie buduje się jawnością."),
    ("Luka 2 – zamknięty kod (K7; 5 pkt). ",
     "Konkurenci z czołówki (Bitwarden, Proton Pass) udostępniają kod aplikacji – po wyciekach to najmocniejszy sygnał „nie mamy nic do ukrycia”."),
    ("Luka 3 – niskie oceny użytkowników (K12; 5,4 pkt). ",
     "Najsłabsza średnia w badaniu (4,1; Google Play tylko 3,8) – efekt utraty zaufania i problemów aplikacji na Androida."),
    ("Luka 4 – funkcje zarezerwowane dla firm (K14, K9, K16; 10 pkt łącznie). ",
     "Kody TOTP tylko w planach biznesowych, słabsze przenoszenie danych, wycofany język polski – braki stosunkowo tanie do usunięcia."),
]:
    akapit(opis, bold_prefix=tyt)

doc.add_heading("4.3. Działania i macierz wpływ–nakład", 2)
obraz(p_macierz, "Rys. 3. Macierz wpływ–nakład działań strategicznych.", szer=15)
OPIS_D = {
    "D1": ("K14", "Udostępnienie kodów TOTP w planach Premium i Families – funkcja już istnieje w planach biznesowych."),
    "D2": ("K12", "Prośba o ocenę po udanym autouzupełnieniu, naprawa 10 najczęstszych problemów zgłaszanych w Google Play, odpowiedzi na opinie."),
    "D3": ("K8, K6", "Publiczne Trust Center: coroczne niezależne audyty z publikowanymi raportami, publiczny bug bounty, raporty o incydentach."),
    "D4": ("K7", "Udostępnienie kodu rozszerzeń przeglądarek i aplikacji mobilnych na licencji open source."),
    "D5": ("K9", "Eksport zaszyfrowany oraz import/eksport w standardzie Credential Exchange (CXP)."),
    "D6": ("K16", "Przywrócenie polskiej wersji językowej we wszystkich aplikacjach."),
    "D7": ("K2", "Obniżka ceny Premium do 19,80 USD – odrzucona: luka to tylko 2,5 pkt, a koszt to utrata ok. 45% przychodu z planu."),
}
tabela(["ID", "Działanie", "Kryteria", "Wpływ", "Nakład", "Kwalifikacja"],
       [[i, OPIS_D[i][1], OPIS_D[i][0], liczba(w), liczba(k), q] for i, _, w, k, q in DZIALANIA],
       [1.0, 8.6, 1.6, 1.3, 1.4, 3.1], rozmiar=8.5, wyroznij=lambda w: w[0] == "D7")
akapit("Wpływ oceniono na podstawie punktów rankingu, które dane działanie odzyskuje (≥ 8 pkt = 5, 5–8 = 4, 3–5 = 3, < 3 = 2), "
       "z premią za budowanie zaufania. Nakład – szacunek zespołu (koszt, czas, ryzyko techniczne).", rozmiar=9, kursywa=True)

doc.add_heading("4.4. Cele SMART", 2)
akapit("Horyzont strategii: 18 miesięcy (styczeń 2027 – czerwiec 2028). Cel nadrzędny: awans z 10. na co najmniej 7. miejsce "
       "w powtórzonym benchmarku (czerwiec 2028), a po otwarciu kodu – do pierwszej trójki.")
tabela(["Cel", "Miernik", "Stan obecny → docelowy", "Termin", "Odpowiedzialny"], [
    ["C1 (D1). Udostępnić kody TOTP w planach Premium i Families.", "odsetek aktywnych użytkowników Premium z min. 1 kodem TOTP",
     "0% → 20%", "wdrożenie 31.03.2027; cel 30.09.2027", "Product Manager (plany indywidualne)"],
    ["C2 (D2). Podnieść średnią ocenę aplikacji w sklepach.", "średnia ocena App Store + Google Play (pomiar miesięczny)",
     "4,1 → 4,5 (Google Play 3,8 → 4,3)", "31.12.2027", "Head of Mobile"],
    ["C3 (D3). Uruchomić Trust Center i publikować niezależne audyty.", "liczba opublikowanych raportów z audytów",
     "0 → 2 (VI 2027) → 4 (VI 2028)", "30.06.2027, potem co 12 mies.", "CISO"],
    ["C4 (D3). Utrzymać zero nowych incydentów z wyciekiem danych.", "liczba incydentów z wyciekiem danych użytkowników",
     "0 nowych", "cały horyzont", "CISO"],
    ["C5 (D4). Otworzyć kod aplikacji klienckich.", "odsetek aplikacji klienckich z kodem na GitHubie",
     "0% → 100%", "31.03.2028", "CTO"],
    ["C6 (D5, D6). Eksport szyfrowany + CXP oraz język polski.", "obsługa funkcji (tak/nie); K9 i K16 w benchmarku",
     "K9: 3 → 5; K16: 0 → 1", "CXP 30.09.2027; PL 31.12.2027", "Engineering Manager (Platform)"],
], [4.4, 3.8, 3.1, 2.9, 2.8], rozmiar=8.5)

doc.add_heading("4.5. Harmonogram", 2)
KW = ["I kw. 27", "II kw. 27", "III kw. 27", "IV kw. 27", "I kw. 28", "II kw. 28"]
PLAN = [("D1 TOTP w Premium", [1, 1, 0, 0, 0, 0]), ("D2 Poprawa ocen", [1, 1, 1, 1, 0, 0]),
        ("D5 Eksport szyfrowany + CXP", [0, 1, 1, 0, 0, 0]), ("D6 Język polski", [0, 0, 1, 1, 0, 0]),
        ("D3 Trust Center i audyty", [1, 1, 0, 0, 1, 1]), ("D4 Otwarcie kodu", [0, 0, 1, 1, 1, 0]),
        ("Powtórzenie benchmarku", [0, 0, 0, 0, 0, 1])]
t = tabela(["Działanie"] + KW, [[n] + [""] * 6 for n, _ in PLAN], [5.0] + [2.0] * 6, rozmiar=8.5)
for r, (_, plan) in enumerate(PLAN, start=1):
    for c, on in enumerate(plan, start=1):
        if on: cieniuj(t.rows[r].cells[c], ROZ[1:] if r == len(PLAN) else GRANAT[1:])

doc.add_heading("4.6. Oczekiwany efekt", 2)
akapit(f"Efekt strategii zasymulowano, zmieniając dane {MY} tak, jakby działania zakończyły się sukcesem, i przeliczając "
       "ranking (dane konkurentów bez zmian, kryterium K6 bez zmian).")
obraz(p_sciezka, f"Rys. 4. Symulowana ścieżka awansu {MY} po kolejnych etapach strategii.")
akapit(f"Same szybkie wygrane dają awans na {sym[1][1]}. miejsce, etap Trust Center – na {sym[2][1]}., a otwarcie kodu – na "
       f"{sym[3][1]}. miejsce ({liczba(sym[3][2])} pkt). Uwaga: przy normalizacji min-max poprawa jednej firmy zmienia też "
       "znormalizowane wartości pozostałych, dlatego wyniki należy traktować jako szacunek kierunku zmian.")

doc.add_heading("4.7. Ryzyka", 2)
punkt("poprawiamy produkt, a nie liczbę – prośby o ocenę nie mogą być nachalne ani kierowane tylko do zadowolonych użytkowników.", "Prawo Goodharta: ")
punkt("otwarcie kodu ujawnia błędy; wymaga wcześniejszego audytu i programu bug bounty (dlatego D3 poprzedza D4).", "Open source: ")
punkt("model biznesowy Bitwardena (open source, niska cena) nie musi pasować do LastPass – dlatego odrzucono obniżkę ceny.", "Best practice ≠ best fit: ")
punkt("kolejny wyciek przekreśla strategię – C4 ma najwyższy priorytet.", "Nowy incydent: ")

# ----- 5. Ograniczenia -----
doc.add_heading("5. Ograniczenia analizy", 1)
for t in ["Menedżery wbudowane (Apple, Google, Microsoft) mają inny model biznesowy niż produkty dedykowane – dlatego dodatkowo policzono ranking bez nich (pkt 3.3).",
          "Przejrzystość interfejsu (K11) oceniono na podstawie recenzji – docelowo zespół powinien zastąpić ją średnią z własnych testów.",
          "Dla produktów bez osobnej aplikacji (Google, Microsoft) oceny w sklepach dotyczą przeglądarek; Apple Hasła nie ma wersji na Androida.",
          "Dane według stanu na 16.11.2026 – ceny i funkcje menedżerów haseł zmieniają się kilka razy w roku.",
          "Wagi są subiektywne; analiza wrażliwości pokazuje jednak, że lider i ostatnie miejsce są stabilne."]:
    punkt(t)

# ----- Załączniki -----
doc.add_heading("Załącznik A. Pliki towarzyszące", 1)
for n, o in [("menedżer haseł - analiza.xlsx", "dane, normalizacja i ranking na żywych formułach, wykres, arkusz źródeł"),
             ("benchmark.py", "skrypt Python (pandas, openpyxl) automatyzujący obliczenia i generujący plik Excel"),
             ("dashboard.py", "dashboard Streamlit: suwaki wag, ranking, porównanie z liderem, źródła (uruchomienie: streamlit run dashboard.py)"),
             ("kryteria.csv, dane_ujednolicone.csv", "dane wejściowe: definicje kryteriów i wag oraz wartości ze źródłami")]:
    punkt(o, bold_prefix=f"{n} – ")

doc.add_heading("Załącznik B. Źródła danych", 1)
akapit("Pełna lista (wartość, uzasadnienie i źródło dla każdego kryterium i firmy) znajduje się w arkuszu „Źródła”. Poniżej unikalne źródła według firm.", rozmiar=9.5)
for f in rank.index:
    p = akapit("", bold_prefix=f); p.paragraph_format.space_after = Pt(2)
    for u in zrodla.loc[zrodla["firma"] == f, "zrodlo"].dropna().unique():
        q = doc.add_paragraph(style="List Bullet"); r = q.add_run(u); r.font.size = Pt(8)
        q.paragraph_format.space_after = Pt(0)

doc.save(OUT)
print("OK", OUT, "| symulacja:", sym)
