"""Dashboard benchmarkingu menedżerów haseł.

Uruchomienie:  streamlit run dashboard.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# Te same funkcje, których używa benchmark.py — nic nie liczymy drugi raz
import plotly.graph_objects as go

from benchmark import FOLDER, normalizuj, ranking, wczytaj_dane, wczytaj_kryteria, wyniki_grup

GRANAT, ROZ, MORSKI = "#0B3B60", "#E0336E", "#2A9D8F"  # kolory jak na slajdach

st.set_page_config(page_title="Benchmark menedżerów haseł", page_icon="🔐", layout="wide")


@st.cache_data  # wczytaj pliki raz, a nie przy każdym ruchu suwakiem
def przygotuj_dane():
    kryteria = wczytaj_kryteria()
    dane = wczytaj_dane()[kryteria.index]
    return dane, kryteria


dane, kryteria = przygotuj_dane()
wagi_bazowe = (kryteria["waga"] * 100).round().astype(int)  # z powrotem na punkty

# ---------- Panel boczny: suwaki wag ----------
st.sidebar.header("⚖️ Wagi kryteriów")
st.sidebar.caption("Przesuń suwak i zobacz, czy zmienia się lider. To analiza wrażliwości.")

if st.sidebar.button("↺ Przywróć wagi z kryteria.csv"):
    for id_ in kryteria.index:
        st.session_state[id_] = int(wagi_bazowe[id_])

punkty = {}
for grupa, kryteria_grupy in kryteria.groupby("grupa"):
    with st.sidebar.expander(grupa, expanded=False):
        for id_, k in kryteria_grupy.iterrows():
            punkty[id_] = st.slider(f"{id_} {k['nazwa']}", 0, 30, int(wagi_bazowe[id_]), key=id_)

punkty = pd.Series(punkty)
if punkty.sum() == 0:
    st.error("Wszystkie wagi są równe 0 — ustaw przynajmniej jedną.")
    st.stop()

# Kopia kryteriów z wagami z suwaków (przeliczonymi na ułamki, Σ = 1)
kryteria_teraz = kryteria.copy()
kryteria_teraz["waga"] = punkty / punkty.sum()

# ---------- Obliczenia ----------
znormalizowane = normalizuj(dane, kryteria)  # normalizacja nie zależy od wag
wyniki_bazowe = ranking(znormalizowane, kryteria)
wyniki = ranking(znormalizowane, kryteria_teraz)

lider, najslabszy = wyniki.index[0], wyniki.index[-1]

# ---------- Strona główna ----------
st.title("🔐 Benchmarking menedżerów haseł")
st.caption(f"{len(dane)} produktów · {len(kryteria)} kryteriów · normalizacja min-max · W = Σ wᵢ·sᵢ")

k1, k2, k3 = st.columns(3)
k1.metric("🏆 Lider", lider, f"{wyniki.loc[lider, 'wynik']} pkt", delta_color="off")
k2.metric("📍 Najsłabszy („my”)", najslabszy, f"{wyniki.loc[najslabszy, 'wynik']} pkt", delta_color="off")
k3.metric("Dystans do lidera", f"{wyniki.loc[lider, 'wynik'] - wyniki.loc[najslabszy, 'wynik']:.1f} pkt")

tab_ranking, tab_luki, tab_dane = st.tabs(["📊 Ranking", "🎯 Lider vs my", "📋 Dane i źródła"])

# ---------- Zakładka 1: ranking ----------
with tab_ranking:
    # Wykres rankingu: lider morski, ostatni różowy, reszta granatowa
    do_wykresu = wyniki.reset_index()
    do_wykresu["rola"] = "pozostali"
    do_wykresu.loc[0, "rola"] = "lider"
    do_wykresu.loc[len(do_wykresu) - 1, "rola"] = "najsłabszy"

    wykres = px.bar(
        do_wykresu, x="wynik", y="firma", orientation="h", text="wynik", color="rola",
        color_discrete_map={"lider": MORSKI, "pozostali": GRANAT, "najsłabszy": ROZ},
        range_x=[0, 105], labels={"wynik": "Wynik W (0–100)", "firma": ""},
    )
    wykres.update_yaxes(categoryorder="total ascending")  # najlepszy na górze
    wykres.update_traces(textposition="outside")
    wykres.update_layout(showlegend=False, height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(wykres, width="stretch")

    # Jak zmieniły się miejsca względem wag bazowych
    zmiany = wyniki.join(wyniki_bazowe.add_suffix("_bazowe"))
    zmiany["zmiana miejsca"] = zmiany["miejsce_bazowe"] - zmiany["miejsce"]  # + = awans
    if (zmiany["zmiana miejsca"] != 0).any():
        st.info("Zmiana wag przesunęła ranking. Kolumna „zmiana miejsca”: + oznacza awans.")
    with st.expander("Tabela rankingu (aktualne vs bazowe wagi)"):
        st.dataframe(zmiany[["miejsce", "wynik", "miejsce_bazowe", "wynik_bazowe", "zmiana miejsca"]])

    # Punkty w grupach — w której grupie kto zyskuje / traci
    st.subheader("Punkty w grupach kryteriów")
    grupy = wyniki_grup(znormalizowane, kryteria_teraz).loc[wyniki.index]
    wykres_grup = px.bar(
        grupy.reset_index().melt(id_vars="firma", var_name="grupa", value_name="punkty"),
        x="punkty", y="firma", color="grupa", orientation="h",
        color_discrete_sequence=[GRANAT, MORSKI, "#E9B44C", ROZ], labels={"firma": ""},
    )
    wykres_grup.update_yaxes(categoryorder="array", categoryarray=list(wyniki.index[::-1]))
    wykres_grup.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(wykres_grup, width="stretch")

# ---------- Zakładka 2: lider vs najsłabszy ----------
with tab_luki:
    porownaj = st.selectbox("Porównaj z liderem:", list(wyniki.index[::-1]), index=0)
    st.caption(f"**{lider}** (lider) vs **{porownaj}** — wartości po normalizacji, 1 = najlepszy w badanej grupie.")

    # Wykres radarowy: każde kryterium to jedna „szprycha”
    etykiety = [f"{id_} {kryteria.loc[id_, 'nazwa']}" for id_ in kryteria.index]
    radar = go.Figure()
    for firma, kolor in [(lider, MORSKI), (porownaj, ROZ)]:
        wartosci = znormalizowane.loc[firma].tolist()
        radar.add_trace(go.Scatterpolar(
            r=wartosci + wartosci[:1], theta=etykiety + etykiety[:1],  # domknięcie wielokąta
            fill="toself", name=firma, line_color=kolor, opacity=0.6,
        ))
    radar.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), height=520,
                        margin=dict(l=60, r=60, t=30, b=30))
    st.plotly_chart(radar, width="stretch")

    # Luka = ile punktów rankingu tracimy do lidera na danym kryterium
    luki = pd.DataFrame({
        "kryterium": kryteria["nazwa"],
        "grupa": kryteria["grupa"],
        lider: dane.loc[lider],
        porownaj: dane.loc[porownaj],
        "utracone pkt": ((znormalizowane.loc[lider] - znormalizowane.loc[porownaj])
                         * kryteria_teraz["waga"] * 100).round(1),
    }).sort_values("utracone pkt", ascending=False)

    st.subheader("Największe luki wobec lidera")
    st.caption("Kryteria posortowane wg punktów rankingu, które tracimy. Ujemne = tu jesteśmy lepsi od lidera.")
    st.dataframe(
        luki, width="stretch",
        column_config={"utracone pkt": st.column_config.ProgressColumn(
            "utracone pkt", min_value=0, max_value=float(luki["utracone pkt"].max()), format="%.1f")},
    )
    top = luki[luki["utracone pkt"] > 0].head(5)
    st.success("**Kandydaci na 3–5 kluczowych luk do strategii:** " + ", ".join(top["kryterium"]))

# ---------- Zakładka 3: dane i źródła ----------
with tab_dane:
    st.subheader("Surowe dane")
    st.dataframe(dane.loc[wyniki.index].rename(columns=lambda id_: f"{id_} {kryteria.loc[id_, 'nazwa']}"))

    st.subheader("Źródła")
    zrodla = pd.read_csv(FOLDER / "dane_ujednolicone.csv", sep=";", encoding="utf-8-sig")
    zrodla = zrodla[zrodla["kryterium"].isin(kryteria.index)]
    firma_filtr = st.multiselect("Filtruj firmy:", sorted(zrodla["firma"].unique()))
    if firma_filtr:
        zrodla = zrodla[zrodla["firma"].isin(firma_filtr)]
    st.dataframe(zrodla, width="stretch", hide_index=True,
                 column_config={"zrodlo": st.column_config.LinkColumn("źródło")})
