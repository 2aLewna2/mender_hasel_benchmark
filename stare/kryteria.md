# Kryteria benchmarkingu — menedżery haseł (wersja robocza v1)

Mieszanka skal (slajd 19): 6 × 0/1, 5 × 1–5, 5 × ilościowe = 16 kryteriów.
S = stymulanta (więcej = lepiej), D = destymulanta (mniej = lepiej).

| ID | Kryterium | Skala | Typ | Definicja pomiaru | Skąd w arkuszu zespołu |
|----|-----------|-------|-----|-------------------|------------------------|
| K1 | Wersja darmowa | 1–5 | S | 1 = brak darmowej (tylko trial); 2 = darmowa mocno ograniczona (limit haseł lub 1 urządzenie); 3 = darmowa z limitem typu urządzeń / kluczowych funkcji; 4 = darmowa bez limitu haseł i urządzeń, część funkcji płatna; 5 = całkowicie darmowy produkt | scalone: „Darmowy” + „Limit haseł/urządzeń w darmowej” |
| K2 | Cena planu płatnego | USD/rok | D | Najtańszy płatny plan indywidualny przy płatności rocznej, cena katalogowa bez promocji. Produkt w pełni darmowy = 0 | „cena planu płatnego” |
| K3 | Liczba obsługiwanych platform | szt. (0–10) | S | Liczba z listy: Windows, macOS, Linux, iOS, Android, rozszerzenie Chrome, Firefox, Safari, Edge, sejf webowy (web vault) | „ilość platform” |
| K4 | Monitoring wycieków | 0/1 | S | Alerty, gdy zapisane hasło/e-mail pojawi się w wycieku (dark web / HIBP) | „monitoring wycieków” |
| K5 | Szyfrowanie E2E (zero-knowledge) domyślnie | 0/1 | S | 1 = dostawca nie ma dostępu do haseł, domyślnie, bez ręcznego włączania | „szyfrowanie end-to-end” |
| K6 | Historia incydentów bezpieczeństwa | liczba | D | Liczba publicznie potwierdzonych naruszeń / wycieków dotyczących produktu menedżera haseł w latach 2015–2026 | „historia wycieków” |
| K7 | Open source | 0/1 | S | 1 = kod klientów publicznie dostępny (np. na GitHub) | „open source” |
| K8 | Niezależne audyty bezpieczeństwa | 1–5 | S | 1 = brak publicznych audytów; 2 = pojedynczy stary audyt; 3 = audyty/certyfikat (SOC 2 / ISO 27001), ale bez publikacji raportów; 4 = regularne audyty + certyfikaty; 5 = regularne, publikowane raporty + certyfikaty + publiczny bug bounty | „Niezależne audyty” |
| K9 | Przenoszenie danych | 1–5 | S | Łatwość importu/eksportu: liczba obsługiwanych formatów i źródeł importu, eksport z poziomu aplikacji, eksport zaszyfrowany, obsługa standardu CXF/CXP | „Łatwość przenoszenia danych” |
| K10 | Udostępnianie haseł | 1–5 | S | 1 = brak; 2 = pojedyncze hasło jednej osobie; 3 = współdzielone grupy/foldery; 4 = + uprawnienia (tylko odczyt itp.); 5 = + bezpieczne udostępnianie osobom bez konta (link jednorazowy) | „Udostępnianie haseł” |
| K11 | Przejrzystość interfejsu | 1–5 | S | Wstępnie: na podstawie recenzji (PCMag, Wirecutter, TechRadar, Security.org); docelowo: średnia ocen członków zespołu po teście | „przejrzystość interfejsu” |
| K12 | Ocena użytkowników | 1–5 (śr.) | S | Średnia ocena z App Store (USA) i Google Play. Gdy produkt nie ma samodzielnej aplikacji — zaznaczyć brak i podać najlepszy zamiennik ze źródłem | „Ocena w App Store / Google Play” |
| K13 | Metody 2FA do konta | liczba | S | Liczba metod zabezpieczenia konta/sejfu: aplikacja TOTP, klucz sprzętowy FIDO2/U2F, passkey do logowania, SMS, e-mail, push, Duo itp. | przerobione z „dwuetapowa weryfikacja” (wszyscy mają 2FA → 0/1 nie różnicowało) |
| K14 | Wbudowany generator kodów 2FA (TOTP) | 0/1 | S | Menedżer sam przechowuje i generuje kody 2FA dla innych serwisów (w dowolnym planie) | nowe |
| K15 | Dostęp awaryjny / dziedziczenie | 0/1 | S | Zaufana osoba może uzyskać dostęp do sejfu w razie śmierci/utraty dostępu (emergency access) | nowe |
| K16 | Język polski | 0/1 | S | Aplikacja dostępna po polsku | nowe |

## Usunięte z wersji zespołu (uzasadnienie do raportu — pułapki ze slajdu 13)
- **Odblokowanie biometrią**: mają je wszyscy badani → min = max, kryterium nie różnicuje (dzielenie przez 0 w min-max).
- **Dwuetapowa weryfikacja (0/1)**: jw. — zamieniona na liczbę metod (K13).
- **„Darmowy” i „Limit w darmowej wersji”**: mierzą to samo (zdublowane kryterium) → scalone w K1.

## Wagi (wersja robocza v1, ustalone PRZED zebraniem danych, żeby nie dopasowywać wag do wyniku)
Metoda punktowa: 100 pkt rozdzielone na 4 grupy wg znaczenia dla klienta, potem na kryteria (wᵢ = pkt/100).

| Grupa | Pkt | Kryteria (pkt) | Uzasadnienie |
|-------|-----|----------------|--------------|
| Bezpieczeństwo | 45 | K5 E2E 12, K6 incydenty 12, K8 audyty 10, K13 metody 2FA 6, K7 open source 5 (K4 usunięte – 6 pkt przeniesione na K5/K6/K8) | Menedżer haseł to „sejf” — klient kupuje przede wszystkim zaufanie; jeden wyciek (LastPass 2022) niszczy markę |
| Koszt | 17 | K2 cena 10, K1 wersja darmowa 7 | Klient indywidualny jest wrażliwy cenowo, silna konkurencja darmowych menedżerów wbudowanych |
| Funkcjonalność | 24 | K3 platformy 7, K10 udostępnianie 5, K9 przenoszenie 4, K14 TOTP 4, K15 dostęp awaryjny 4 | Menedżer musi działać wszędzie, gdzie użytkownik się loguje; reszta to funkcje „dodatkowe” |
| Doświadczenie użytkownika | 14 | K11 interfejs 6, K12 oceny 6, K16 język polski 2 | Wygoda decyduje o tym, czy użytkownik faktycznie korzysta z menedżera; PL ważne lokalnie, ale niszowe |
| **Razem** | **100** | | |

## Zmiany po zebraniu danych (v2)
- **K4 Monitoring wycieków usunięte** — po zebraniu danych okazało się, że mają go wszystkie 10 produktów (min = max). Zostaje **15 kryteriów** (minimum z zadania).
  Skale: 5 × 0/1 (K5, K7, K14, K15, K16), 5 × 1–5 (K1, K8, K9, K10, K11), 5 × ilościowe (K2, K3, K6, K12, K13).

## Reguły ujednolicenia (agenci liczyli różnie — przyjęto jedną regułę dla wszystkich)
- **R1 (K6):** liczymy tylko potwierdzone incydenty, w których wyciekły dane użytkowników/klientów. Podatności zgłoszone przez badaczy i incydenty bez wycieku danych — nie. → Bitwarden 1→0 (atak na npm CLI 2026 bez wycieku).
- **R2:** liczą się tylko funkcje dostępne w planach dla klienta indywidualnego (nie tylko biznesowych). → LastPass K14 1→0; 1Password K13 4→3; Keeper K13 6→4.
- **R3:** płatny dodatek dostępny dla klienta indywidualnego się liczy (np. Keeper BreachWatch).
- **R4 (K2):** cena regularna (odnowienie), nie promocja na pierwszy rok.
- **R5 (K12):** produkty bez osobnej aplikacji — ocena aplikacji-zamiennika (Google → Chrome, Microsoft → Edge); Apple tylko App Store (brak na Androidzie). Opisane jako ograniczenie.
