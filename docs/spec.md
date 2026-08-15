# Spec: CHP znalostní databáze — archivní analýza zpravodajů Spřežení (fáze 1: 1984–2008)

**Datum:** 2026-08-15
**Autor spec:** Claude (Opus 5) + Fajfka
**Stav:** čeká na schválení Fajfkou (2 otevřené body, viz § Otevřené body)
**Implementuje:** Sonnet 5 — zadávat po fázích: „implementuj fázi N podle /root/chp-znalostni-databaze/docs/spec.md"
**Projekt:** `/root/chp-znalostni-databaze/` (nový — kód NEEXISTUJE, `git init` proveden, adresáře `docs/ 00_inventar/ 01_ocr_raw/ 02_extrakce/ 03_vystupy/` založeny)
**Původ:** Fajfkův „master prompt" (Komplexní archivní analýza zpravodajů Spřežení – Český horský pes, 44 bodů) + brainstorm 2026-08-15 + technický recon 2026-08-15. Memory: `project_chp_znalostni_databaze.md`, `feedback_sequential_subagent_checkpointing`, `project_dog_kennel`, `fajfka_context`.

---

## 1. Cíl a rozhodovací otázka

Z 56 historických čísel klubového zpravodaje **Spřežení** (1984–2008, naskenovaná PDF bez textové vrstvy) vytvořit **strukturovanou, prohledávatelnou a plně citovatelnou znalostní databázi** o tréninku, výživě, výchově, vedení spřežení, chovu, chovných podmínkách a genetice Českého horského psa. Databáze musí umožnit řetězec **dohledat → pochopit → porovnat → vyhodnotit → aplikovat**: u každého poznatku musí být zjistitelný přesný zdroj (číslo, rok, strana, autor, článek), typ informace (fakt × zkušenost × názor × pravidlo × hypotéza) a míra důvěryhodnosti.

Nejde o shrnutí časopisů. Jde o **archivní výzkumný proces s přísnými anti-halucinačními pravidly**, jehož vedlejším produktem je trvale znovupoužitelný textový archiv (OCR po stránkách), takže se 56 PDF už nikdy nemusí procházet znovu.

**Rozhodovací otázka (kvalitativní, ne numerická):** Dá se z degradovaných skenů 1984–2008 vytěžit databáze, která na namátkové kontrole Fajfkou obstojí — tj. citace sedí na skutečný zdroj, žádný poznatek není vymyšlený a žádná podstatná informace ze zkontrolovaných stránek nechybí?

**Negativní výsledek je validní:** pokud se na gate fáze 2 (vzorek OCR) ukáže, že kvalita skenů z 80. let je pod hranicí použitelnosti i po AI dočtení, je legitimní závěr **zúžit scope na čísla od roku X dál** a starší čísla zpracovat jen na úrovni inventáře a názvů článků. To se rozhoduje na gate, ne tichou úpravou v kódu.

**Předchozí evidence (technický recon 2026-08-15):**

| Test | Výsledek | Zdroj |
|---|---|---|
| `pdftotext` na starých číslech (1984–2008) | 0 znaků → čistě obrázkové skeny, OCR nutné u **všech** souborů fáze 1 | recon 08-15 |
| `pdftotext` na číslech cca od 2019 | nativní textová vrstva existuje | recon 08-15 (mimo scope) |
| `pdfinfo` napříč archivem | 56 souborů, **1 715 stran** celkem, 8–56 stran na číslo | ověřeno 08-15 |
| Dostupné nástroje | `pdftotext`, `pdfinfo`, `pdftoppm` (poppler-utils) ANO; `tesseract` NE (apt 5.3.4 dostupný, internet funguje) | ověřeno 08-15 |
| Python balíčky | `openpyxl`, `python-docx`, `pymupdf`, `pytesseract`, `Pillow` chybí; systém je PEP 668 „externally managed" | ověřeno 08-15 |
| Volné místo na `/root` | 7,6 GB (z 38 GB) | ověřeno 08-15 |
| Cesty s diakritikou přes bash | selhávají kvůli NFC/NFD normalizaci Unicode; `os.walk()` z ASCII kořene funguje spolehlivě | recon 08-15 |

**Korekce reconu:** archiv má **56 PDF, ne 55**. Řadových čísel Spřežení je 53 (č. 1–53, bez mezery v číslování), navíc `68-1992-11_sprezeni_special.pdf`, `71-1993-04_sprezeni_special.pdf` a `63-1992-01_chovatelsky_zapisni_rad.pdf`. Mezery jsou v **letech**: chybí ročník **2000** a **2007** (viz Otevřený bod O1).

**Co projekt NEDĚLÁ:**

- **Nesahá na složku `Nové/`** (30 souborů, 2009–2025). Ani nelistuje, ani neindexuje, ani neotevírá, ani z ní necituje. Tvrdý požadavek master promptu (body 1, 35, 42). Platí i pro kód: žádný skript ani konfigurace nesmí mít `Nové` v cestě, glob patternu ani ve výstupu (viz test T9).
- Nedělá fázi 2 (srovnání historické × nové). Ta přijde až na výslovný Fajfkův pokyn, jako samostatná spec.
- **Nedělá žádný internetový výzkum.** Žádné doplňování z webu, žádné moderní články jako zdroj historického tvrzení, žádné moderní veterinární doporučení vydávané za obsah archivu. Externí kontext jen pro vysvětlení dobového pojmu, a jen s doslovným labelem `EXTERNÍ KONTEXT – NENÍ SOUČÁST HISTORICKÉHO ARCHIVU`.
- Nedělá webové UI, dashboard, API ani integraci do HUBu. Výstup jsou soubory (xlsx/docx) + strojově čitelné JSONL.
- Nepřepisuje ani nemaže zdrojová PDF v `/root/Uploads/` (ta je jen staging, read-only).
- Nekoriguje pravopis ani neupravuje dobový jazyk citací.

---

## 2. Přesná pravidla / datový kontrakt

Tato sekce je **závazná doslovně**. Implementer nesmí formáty upravovat, „vylepšovat" ani rozšiřovat.

### 2.1 Tři anti-halucinační pravidla (nadřazená všemu ostatnímu)

1. **Zákaz vymýšlení.** Nikdy nevymýšlet autora, datum, číslo zpravodaje, stránku, citaci, název článku, výsledek závodu, zkušenost, pravidlo, genetický údaj ani tréninkovou metodu. Pokud údaj není jednoznačně zjistitelný ze zdroje, patří tam přesně řetězec:
   ```
   neuvedeno / nelze jednoznačně určit
   ```
2. **Zákaz domýšlení.** Chybějící informace se nikdy nedoplňuje podle domněnky, kontextu ani analogie z jiného čísla. Nečitelné místo v textu se označuje přesně:
   ```
   [nečitelné]
   ```
   Toto platí i pro AI dočtení stránky (vision) — vision NESMÍ „uhodnout" slovo, které nevidí. Když nevidí, píše `[nečitelné]`.
3. **Zákaz míchání úrovní.** Vlastní interpretace se nikdy nepředkládá jako historický fakt. Každý záznam v databázi nese pole `Uroven` (viz 2.3).

### 2.2 Citační formát (master prompt bod 4) — 3 povolené varianty

Přesně tyto tři tvary, včetně hranatých závorek, čárek a českých uvozovek. Žádná čtvrtá varianta neexistuje.

```
[Spřežení č. 12, rok 1989, s. 7, autor: Dana Kupková, „Zbarvení u ČHP"]
[Spřežení č. 12, rok 1989, s. 7, autor neuveden]
[Spřežení č. 12, rok 1989, strana nezjištěna, autor: Dana Kupková]
```

Doplňující pravidla:
- Když název článku není zjistitelný, vypouští se celý poslední člen (ne `„neuvedeno"`).
- U dvou nečíslovaných zvláštních čísel se místo `č. XX` píše `č. zvláštní (1992-11)` resp. `č. zvláštní (1993-04)`, u chovatelského zápisního řádu `Chovatelský a zápisní řád (1992-01)`.
- **Strana = tištěné číslo stránky ze skenu**, pokud je čitelné. Když čitelné není, použije se varianta `strana nezjištěna` a do pole `Strana` v databázi se zapíše `pdf-str. N` (N = pořadí stránky v PDF, 1-based). Nikdy se tištěné a PDF číslo nezaměňují mlčky.
- Krátká doslovná citace ze zdroje je povolená a vítaná (pro ověření významu), do 2 vět. Dlouhé pasáže se nepřepisují.
- Doslovná citace se v poli `Poznatek` uzavírá do českých uvozovek `„...“` — podle toho ji hlídá automatický test T5 (viz § 4).

### 2.3 Čtyři úrovně informace (master prompt bod 2)

Master prompt pracuje se třemi úrovněmi analýzy (A = co je ve zdroji, B = co z toho plyne, C = co lze dnes použít) a zároveň se čtyřmi labely. **Kanonický je čtyřhodnotový enum**, používá se pole `Uroven`:

| Hodnota | Význam |
|---|---|
| `A` | Doložená informace ze zdroje (fakt — je to tam napsané) |
| `B` | Interpretace zdroje (co autor zjevně míní, co z textu plyne) |
| `C` | Analytický závěr (syntéza napříč zdroji, trend, vývoj) |
| `D` | Praktické doporučení pro dnešek |

Záznam s `Uroven` = `C` nebo `D` **musí** mít v poli `Zdroj` uvedené všechny citace, ze kterých vychází (oddělené `; `), a v poli `Poznatek` musí začínat prefixem `SYNTÉZA: ` (bod 8 master promptu — u syntézy z více článků vždy uvést, že jde o syntézu).

### 2.4 Kategorie a podkategorie

Povinný enum `Kategorie` (přesně tyto kódy):

| Kód | Kategorie |
|---|---|
| `KAT1` | Trénink a sportovní výkon spřežení |
| `KAT2` | Výživa psích sportovců |
| `KAT3` | Výchova psa do tahu |
| `KAT4` | Výchova a pěstování leadera |
| `KAT5` | Výcvik celého spřežení |
| `KAT6` | Chovatelská stanice a management |
| `KAT7` | Výchova štěňat |
| `KAT8` | Péče o fenu/matku a reprodukce |
| `KAT9` | Podmínky zařazení do chovu (vývoj pravidel) |
| `KAT10` | Genetika |
| `KAT0` | Ostatní archivní obsah (organizační, výsledky závodů, dopisy, zprávy z klubu) |

`KAT1` má povinnou podkategorii (enum `Podkategorie`):

| Kód | Podkategorie KAT1 |
|---|---|
| `1A` | Saně |
| `1B` | Kolo / bikejöring |
| `1C` | Koloběžka |
| `1D` | Kára / trénink bez sněhu |
| `1E` | Běh / canicross |
| `1F` | Triatlon / kombinovaný trénink |
| `1G` | Obecná kondiční příprava (vytrvalost, síla, rychlost, koordinace, technika, regenerace, mimosezónní příprava, přechod sezón) |

U ostatních kategorií je `Podkategorie` volný text (např. `štěně 8–12 týdnů`, `krmení před výkonem`, `inbreeding`) nebo `neuvedeno / nelze jednoznačně určit`. Jeden poznatek může být relevantní pro víc kategorií — pak se **duplikuje jako samostatný záznam** s jiným `Kategorie` a stejným `Zdroj` (křížové propojení řeší pole `Souvisi_s`).

Rozsah témat k hledání (master prompt bod 6): nejen zjevně sportovní články, ale i krátké poznámky, zkušenosti členů, výsledky závodů, komentáře, dopisy, metodické články, chovatelské informace, zdravotní informace, poznámky k vrhům, informace o konkrétních psech a spřeženích, zkušenosti s krmením, genetické informace, změny pravidel, organizační informace.

### 2.5 Schéma master databáze poznatků (master prompt body 26 + 30 + 31 + 39)

Kanonické úložiště je **append-only JSONL**: `02_extrakce/poznatky.jsonl`, jeden JSON objekt na řádek, UTF-8, `ensure_ascii=false`. Nikdy se nepřepisuje ani nepřepočítává celý soubor — jen se **appenduje**. (Důvod: sekvenční dávky, viz 2.9.)

Povinná pole (všechna, žádné se nevynechává; když hodnota není zjistitelná, patří tam `neuvedeno / nelze jednoznačně určit`):

| Pole | Typ | Pravidlo |
|---|---|---|
| `ID` | string | `P-B<dávka>-<pořadí:03d>`, např. `P-B3-017`. Unikátní napříč celou databází. |
| `Kategorie` | enum | viz 2.4 |
| `Podkategorie` | string | u `KAT1` povinný enum `1A`–`1G` |
| `Poznatek` | string | vlastní obsah; u `Uroven` C/D začíná `SYNTÉZA: ` |
| `Zdroj` | string | plná citace dle 2.2; u syntézy víc citací oddělených `; ` |
| `Cislo` | string | `12` / `zvláštní (1992-11)` / `Chovatelský a zápisní řád (1992-01)` |
| `Rok` | int | 1984–2008 |
| `Strana` | string | tištěné číslo, jinak `pdf-str. N` |
| `Autor` | string | jméno, nebo `neuvedeno / nelze jednoznačně určit` |
| `Clanek` | string | název článku, nebo `neuvedeno / nelze jednoznačně určit` |
| `Typ_informace` | enum | `historický fakt` / `zkušenost chovatele` / `názor` / `metodika` / `pravidlo` / `genetické tvrzení` / `výsledek` / `hypotéza` / `interpretace` |
| `Uroven` | enum | `A` / `B` / `C` / `D` (viz 2.3) |
| `Duveryhodnost` | enum | `VYSOKÁ` / `STŘEDNÍ` / `NÍZKÁ` / `NEJISTÁ` (definice viz 2.6) |
| `Priorita` | enum | `A` (velmi důležité) / `B` (důležité) / `C` (doplňkové) / `D` (jen archivní) |
| `Prakticke_vyuziti` | string | jak by šlo dnes použít, nebo `neuvedeno / nelze jednoznačně určit` |
| `Klicova_slova` | list[string] | 3–8 českých klíčových slov, malými písmeny |
| `Souvisi_s` | list[string] | ID jiných poznatků (stejný pes / chovatel / metoda / téma), může být prázdný list |
| `Davka` | int | číslo dávky 1–8 (viz 2.9) |
| `Ocr_zdroj` | string | relativní cesta k OCR stránce, ze které poznatek pochází, např. `01_ocr_raw/56-1989-11_sprezeni_c_12/page_0007.txt`; u syntézy víc cest oddělených `; ` |

`Ocr_zdroj` je klíčové pole pro automatickou kontrolu proti halucinaci (test T4/T5) — bez něj se záznam neuznává.

**Zvláštní pravidlo pro praktickou zkušenost chovatele (bod 24):** záznam s `Typ_informace` = `zkušenost chovatele` musí mít v `Poznatek` uvedeno kdo / kdy / u jakých psů / za jakých podmínek / s jakým výsledkem — každý údaj buď konkrétně, nebo `neuvedeno / nelze jednoznačně určit`. Zkušenost chovatele se **nikdy neoznačuje jako vědecký fakt**, ale ani se nezahazuje.

### 2.6 Stupnice důvěryhodnosti (master prompt bod 31)

| Hodnota | Kdy |
|---|---|
| `VYSOKÁ` | Opakovaně doloženo — týž poznatek nezávisle ve **2+ různých číslech** nebo od 2+ různých autorů |
| `STŘEDNÍ` | Doloženo jednou, ale metodicky (článek s vysvětlením, oficiální klubové pravidlo, publikovaný výsledek) |
| `NÍZKÁ` | Jednotlivá osobní zkušenost nebo názor jednoho autora bez opory |
| `NEJISTÁ` | Zdroj špatně čitelný, kontext nejasný, nebo poznatek obsahuje `[nečitelné]` v podstatné části |

**Četnost není důkaz účinnosti** (bod 33). Frekvenční statistiky se počítají a reportují, ale nikdy se nepoužívají jako argument, že metoda funguje.

### 2.7 Formát záznamu ROZPOR (master prompt bod 32)

Úložiště `02_extrakce/rozpory.jsonl`, plní se ve fázi 5. Rozpory se **nikdy násilně nespojují** do jednoho „průměrného" tvrzení.

```json
{
  "ID": "ROZPOR č.01",
  "Tema": "Krmení bezprostředně před závodem",
  "Zdroj_A": "[Spřežení č. 21, rok 1992, s. 4, autor: ...]",
  "Tvrzeni_A": "...",
  "Zdroj_B": "[Spřežení č. 40, rok 1998, s. 11, autor: ...]",
  "Tvrzeni_B": "...",
  "Rozdil": "...",
  "Mozne_vysvetleni": "... nebo: neuvedeno / nelze jednoznačně určit",
  "Lze_rozhodnout": "ano / ne / jen s dalšími zdroji",
  "Co_overit": "..."
}
```

`ID` má přesně tvar `ROZPOR č.NN` s dvojmístným číslem od `01`.

### 2.8 OCR kontrakt

**Metoda: hybrid** (schváleno v brainstormu).

1. **Render:** `pdftoppm -r 300 -gray -png -f N -l N <pdf> <tmp>/page` — jedna stránka po druhé, nikdy ne celé PDF najednou (disk!).
2. **OCR:** Tesseract 5.3.4 s českým jazykovým modelem: `-l ces --psm 3 -c preserve_interword_spaces=1`. Per-slovo confidence z TSV výstupu (`tessedit_create_tsv=1`, nebo `pytesseract.image_to_data`).
3. **Confidence stránky** = aritmetický průměr confidence všech slov, kde `conf >= 0` a text slova po `strip()` není prázdný.
4. **Práh = 85,0.** Chování:
   - `page_conf >= 85.0` → text z Tesseractu se bere jako finální, PNG se **smaže**.
   - `page_conf < 85.0` → stránka se označí `needs_vision`, její PNG se **ponechá** v `01_ocr_raw/<stem>/_vision/page_XXXX.png` (přerenderovaná na `-r 200 -gray`, kvůli velikosti) a zapíše se do `01_ocr_raw/<stem>/needs_vision.json`. Tesseractový text se zatím uloží, ale s `ocr_metoda: "tesseract-low"`.
   - **Guard na prázdnou stránku:** pokud stránka má méně než 5 rozpoznaných slov s `conf >= 0`, jde vždy na `needs_vision` bez ohledu na průměr (jinak prázdná strana dostane vysoký průměr z jednoho artefaktu).
5. **Vision dočtení** (fáze 3b): implementer / subagent přečte ponechaný PNG nástrojem Read a přepíše obsah `page_XXXX.txt`. Platí anti-halucinační pravidlo — nečitelné slovo = `[nečitelné]`, nikdy odhad. Po dokončení souboru se celý adresář `_vision/` smaže.
6. **Nikdy se nemaže `01_ocr_raw/*.txt` ani `meta.json`** (bod 36 master promptu) — je to trvalý archiv. Maže se výhradně rastr (`.png`).

**Formát stránkového souboru** `01_ocr_raw/<stem>/page_0007.txt`:

```
# ZDROJ: Spřežení č. 12, rok 1989, s. 7
# SOUBOR: 56-1989-11_sprezeni_c_12.pdf
# PDF_STRANA: 7
# TISTENA_STRANA: 7
# OCR: tesseract-5.3.4 / ces / conf 91.2
---
<čistý OCR text stránky>
```

Když tištěné číslo strany není čitelné: `# TISTENA_STRANA: nezjištěna` a hlavička `# ZDROJ:` použije variantu `strana nezjištěna`.

**Formát** `01_ocr_raw/<stem>/meta.json`: jeden objekt se seznamem stránek — `pdf_strana`, `tistena_strana`, `conf`, `ocr_metoda` (`tesseract` / `tesseract-low` / `vision`), `pocet_slov`, `znaku`.

### 2.9 Dávkování extrakce a SEKVENČNÍ zpracování

**Rozdělení do 8 dávek po 7 souborech** (podle prefixu v názvu souboru, chronologicky):

| Dávka | Soubory (prefix) | Období |
|---|---|---|
| 1 | 45–51 | 1984-06 … 1987-06 |
| 2 | 52–58 | 1987-11 … 1990-10 |
| 3 | 59–65 | 1991-01 … 1992-05 |
| 4 | 66–72 | 1992-07 … 1993-10 |
| 5 | 73–79 | 1994-07 … 1996-01 |
| 6 | 80–86 | 1996-01 … 1998-08 |
| 7 | 87–93 | 1998-11 … 2001 |
| 8 | 94–100 | 2002 … 2008 |

**KRITICKÉ — dávkové subagenty se spouštějí striktně SEKVENČNĚ, nikdy paralelně.** Fajfkův explicitní požadavek: *„subagenty na to posílej postupně, pravděpodobně dojdu tokeny, tak ať se vždy něco dokončí a uloží než tokeny dojdou."*

Pravidla:
1. Dávka `N+1` se nesmí spustit dřív, než dávka `N` **prokazatelně zapsala** své záznamy do `02_extrakce/poznatky.jsonl` (a `zdroje.jsonl`, `psi.jsonl`) na disk.
2. Ověření zápisu = spočítat řádky souboru před a po dávce; nárůst musí být > 0. Když nárůst = 0, dávka se považuje za selhanou a **další se nespouští** — reportovat Fajfkovi.
3. Subagent **appenduje**, nikdy nepřepisuje. Žádný `w` mód nad master soubory.
4. Po každé dávce zapsat řádek do `02_extrakce/postup.md` (dávka, soubory, počet nových záznamů, čas) — checkpoint pro pokračování po vyčerpání tokenů.

> **Odchylka od zavedeného zvyku — zdůvodnění:** graphify a `superpowers:dispatching-parallel-agents` jako default paralelizují dispatch subagentů. **Tady se to výslovně NEDĚLÁ.** Důvod: běh přes 1 715 stran archivu spolehlivě narazí na token/budget limit uprostřed práce; paralelní běh znamená, že v tu chvíli přijde o rozpracovaný výstup několik agentů naráz. Sekvenční běh s checkpointem na disk po každé dávce znamená ztrátu maximálně jedné dávky. Implementer tuto odchylku nesmí „optimalizovat" zpět na paralelní.

### 2.10 Vedlejší úložiště v `02_extrakce/`

Všechna append-only JSONL, UTF-8:

- `poznatky.jsonl` — master databáze (schéma 2.5), plní dávkové subagenty (fáze 4)
- `zdroje.jsonl` — index zdrojů/článků (master prompt bod 38): `ID_zdroje`, `Cislo`, `Rok`, `Strana`, `Autor`, `Clanek`, `Kategorie` (list — článek může mít víc kategorií), `Klicova_slova` (list), `Ocr_zdroj`. Plní dávkové subagenty.
- `psi.jsonl` — profily konkrétních psů a spřežení (body 22–23), zakládá se jen pro psy/spřežení zmíněné **opakovaně** (2+ výskyty): `Jmeno`, `Rodice`, `Rok_narozeni`, `Chovatel`, `Majitel`, `Vysledky` (list), `Pozice_ve_sprezeni`, `Charakter`, `Zdravi`, `Reprodukce`, `Potomstvo`, `Genetika`, `Popis_leadera`, `Trenink`, `Zdroje` (list citací). Nezjistitelná pole = `neuvedeno / nelze jednoznačně určit`. Plní dávkové subagenty, doplňují napříč dávkami (nový výskyt = nový append s týmž `Jmeno`, slévá se ve fázi 5).
- `rozpory.jsonl` — rozpory (schéma 2.7), plní se ve fázi 5 (jsou cross-batch).
- `teze.jsonl` — teze (bod 19): `Teze`, `Stav` ∈ {`POTVRZENÁ`, `PRAVDĚPODOBNÁ`, `ROZPORUPLNÁ`, `NEOVĚŘENÁ`, `VYVRÁCENÁ/OPUŠTĚNÁ`}, `Zdroje` (list), `Obdobi`, `Dukazy`, `Mira_jistoty`, `Co_overit`. Plní se ve fázi 5.
- `postup.md` — checkpoint log dávek (2.9).

### 2.11 Přesný seznam 10 výstupních souborů (master prompt bod 37)

Do `03_vystupy/`, přesně tato jména, žádná jiná:

| # | Soubor | Obsah |
|---|---|---|
| 1 | `01_ARCHIVNI_INVENTAR.xlsx` | inventář 56 souborů + časová osa + mezery v číslování (bod 5) |
| 2 | `02_DATABAZE_POZNATKU.xlsx` | plná databáze poznatků, sloupce dle 2.5 |
| 3 | `03_DETAILNI_ARCHIVNI_VYTAH.docx` | detailní výtah po kategoriích — interní znalostní základna, musí umět odpovědět např. „co se psalo o výživě před závodem" |
| 4 | `04_EXECUTIVE_SUMMARY.docx` | 13 sekcí přesně dle bodu 28 (viz 2.12) |
| 5 | `05_PRAKTICKA_APLIKACE.docx` | sekce A–O dle bodu 29 (viz 2.13) |
| 6 | `06_CASOVA_OSA_VYVOJE.docx` | vývoj myšlení v čase, historická období (body 19, 25) |
| 7 | `07_GENETIKA_A_CHOV.docx` | KAT10 + KAT9, vč. samostatné části k článkům Dany Kupkové |
| 8 | `08_TRENING_A_VYCVIK.docx` | KAT1 + KAT3 + KAT4 + KAT5, vč. tréninkových modelů (bod 8) |
| 9 | `09_ROZPORY_A_NEOVERENE_TEZE.docx` | rozpory (2.7) + 5 seznamů tezí (2.10) + kapitola „TEZE K OVĚŘENÍ V NOVÝCH ZPRAVODAJÍCH" (bod 41) |
| 10 | `10_INDEX_ZDROJU.xlsx` | index zdrojů dle bodu 38 |

`.xlsx` přes `openpyxl`, `.docx` přes `python-docx`. Každý xlsx má zamrzlý první řádek (`freeze_panes="A2"`) a autofiltr.

**Navíc povinné sekce, které nemají vlastní soubor** (umístit takto):
- **TOP 50 nejzajímavějších poznatků** (bod 34) → poslední kapitola `04_EXECUTIVE_SUMMARY.docx`, sloupce: poznatek, proč zajímavý, zdroj, historický význam, využití dnes, důvěryhodnost, co ověřit.
- **Frekvenční/statistické vyhodnocení** (bod 33) → samostatný list `Statistika` v `02_DATABAZE_POZNATKU.xlsx` (četnost témat a metod po obdobích) + odstavec s výslovným upozorněním, že četnost není důkaz účinnosti.
- **Profily psů a spřežení** (body 22–23) → samostatný list `Psi` v `02_DATABAZE_POZNATKU.xlsx`.
- **Závěrečná analýza — 16 otázek** (bod 40) → předposlední kapitola `04_EXECUTIVE_SUMMARY.docx`, každá otázka zodpovězená explicitně a samostatně; když zdroje neumožňují odpověď, doslova `neuvedeno / nelze jednoznačně určit` a čím to je.

### 2.12 Struktura `04_EXECUTIVE_SUMMARY.docx` (bod 28, pořadí závazné)

1. Historie tréninku — 2. Vývoj práce se spřežením — 3. Vývoj výchovy leadera — 4. Vývoj práce se štěňaty — 5. Výživa — 6. Chov a management — 7. Podmínky zařazení do chovu — 8. Genetika — 9. Nejzajímavější historické postupy — 10. Co může být použitelné dnes — 11. Co je potřeba ověřit — 12. Největší rozpory — 13. Nejzajímavější otázky pro fázi 2. (+ Závěrečná analýza 16 otázek, + TOP 50, viz 2.11.)

### 2.13 Struktura `05_PRAKTICKA_APLIKACE.docx` (bod 29, sekce A–O)

A. Výchova štěněte — B. Příprava do tahu — C. Výcvik leadera — D. Výcvik spřežení — E. Kondiční trénink — F. Trénink saně — G. Trénink kolo — H. Trénink koloběžka — I. Trénink kára — J. Kombinovaný trénink — K. Výživa — L. Regenerace — M. Management stanice — N. Péče o štěňata a fenu — O. Chov a chovné podmínky.

U **každého** bodu čtyři povinné části v tomto pořadí: **co říkají zdroje → co lze převzít → jak prakticky aplikovat → limity a co ověřit.**

Součástí je návrh tréninkového plánu (8 a 12 týdnů; přípravné / předzávodní / závodní období), **jen pokud zdroje stačí** — jinak se výslovně napíše, že nestačí a proč. Každé doporučení v plánu nese jeden ze čtyř štítků:

```
HISTORICKY DOLOŽENO / ODVOZENO ZE ZDROJŮ / ANALYTICKÝ NÁVRH / VYŽADUJE OVĚŘENÍ
```

Nikdy nezaměňovat historickou informaci za moderní veterinární doporučení — u výživy a zdraví povinná věta, že jde o historický materiál a moderní veterinární doporučení se může lišit.

### 2.14 Unicode gotcha — cesty s diakritikou (POVINNÉ)

Zdrojová cesta `/root/Uploads/Zpravodaj Spřežení/` obsahuje `ř` a `ž`. V reconu se ukázalo, že **ručně psaný accented string selhává** (bash `cd`/quoting i Python porovnání) kvůli NFC/NFD normalizaci Unicode — název na disku je v jiné normalizaci než literál v kódu. Ověřeno prakticky: `if root.endswith('Spřežení')` vrátilo prázdný výsledek, přestože adresář existuje.

**Závazné řešení:**
- Vždy začínat `os.walk('/root/Uploads')` (ASCII kořen) a používat **path objekty vrácené z walku**, nikdy ručně psaný accented literál.
- Filtrovat jen přes ASCII substringy: `'Zpravodaj' in root`, `'Nov' in root` (pro vyloučení).
- Nikdy nepředávat accented cesty přes shell — pracovat s nimi v Pythonu, případně `subprocess.run([...])` se seznamem argumentů (ne `shell=True`).
- Vlastní projektové adresáře a všechny generované soubory jsou **ASCII-only** (`01_ocr_raw/56-1989-11_sprezeni_c_12/`) — diakritika žije jen v obsahu souborů, nikdy v cestách.

### 2.15 Instalace prostředí a fail-safe

- `apt install -y tesseract-ocr tesseract-ocr-ces`
- `pip install --break-system-packages pytesseract Pillow openpyxl python-docx` (systém je PEP 668; venv je povolená alternativa, ale pak ho zapsat do `docs/spec.md` poznámkou a používat důsledně).
- **Disk guard:** před zpracováním každého PDF zkontrolovat volné místo (`shutil.disk_usage('/root')`). Pod **1,5 GB** volných → běh se zastaví s jasnou hláškou a neztratí dosud zpracované soubory. PNG se maže hned po OCR stránky (mimo `needs_vision`).
- **Fail-safe zásada:** poškozený nebo nečitelný PDF **neshodí celý běh** — zapíše se WARNING, do inventáře `dostupnost: chyba: <důvod>` a pokračuje se dalším souborem. Totéž pro jednotlivou stránku (render selže → `# OCR: selhalo`, obsah `[nečitelné]`, běh pokračuje).
- OCR je **idempotentní**: pokud `page_XXXX.txt` už existuje a `meta.json` ho eviduje jako hotový, přeskočit (umožňuje pokračovat po přerušení).

### 2.16 Inventář (master prompt bod 5) — schéma

`00_inventar/inventar.json` + list `Inventar` v `01_ARCHIVNI_INVENTAR.xlsx`, sloupce:

`Nazev_souboru`, `Prefix` (číslo v názvu), `Cislo_zpravodaje`, `Rok`, `Mesic`, `Pocet_stran`, `Dostupnost_textu` (`skenované` / `textové` / `chyba: <důvod>`), `Nutnost_OCR` (ano/ne), `Problemy_s_kvalitou` (volný text), `Typ_dokumentu` (`řadové číslo` / `zvláštní číslo` / `chovatelský a zápisní řád`).

Druhý list `Casova_osa`: rok → čísla vydaná v tom roce; třetí list `Mezery`: chybějící ročníky a chybějící čísla s poznámkou, že mezera je v datech, ne domněnka o neexistenci čísla.

---

## 3. Architektura

Konvence převzít z: **sesterské projekty nejsou přímo použitelné** (jsou to trading boti / dashboardy s jiným tvarem). Převzít se má jen obecný projektový návyk z `/root/tradingbot-rotace/` a `/root/jarvis/`: `config/config.yaml` + loader, logging do `logs/`, `tests/` s pytest, `docs/spec.md` jako zdroj pravdy. Před implementací se podívej na `config/config.yaml` v `/root/tradingbot-rotace/` kvůli stylu configu — **nic dalšího z těch projektů nekopírovat**.

```
/root/chp-znalostni-databaze/
├── config/
│   └── config.yaml            # cesty, dpi, ocr_conf_threshold: 85.0, jazyk, dávky, disk_guard_gb
├── src/
│   ├── paths.py               # bezpečné hledání zdrojů přes os.walk (§2.14), vyloučení Nové/
│   ├── inventar.py            # fáze 1 — pdfinfo + metadata z názvů → 00_inventar/inventar.json
│   ├── ocr.py                 # fáze 2/3 — render + tesseract + confidence + needs_vision + meta.json
│   ├── db.py                  # append/read JSONL, validace schématu 2.5, generování ID
│   ├── kontrola.py            # anti-halucinační kontroly (referenční integrita, ověření citací) — §4 T4/T5
│   └── export.py              # fáze 5a — JSONL → xlsx (openpyxl); pomocné buildery pro docx
├── tests/
│   ├── test_paths.py
│   ├── test_ocr.py
│   ├── test_db.py
│   ├── test_kontrola.py
│   └── test_export.py
├── 00_inventar/               # inventar.json (+ log problémů)
├── 01_ocr_raw/<stem>/         # page_XXXX.txt, meta.json, dočasně _vision/*.png — TRVALÝ ARCHIV, nemazat
├── 02_extrakce/               # poznatky.jsonl, zdroje.jsonl, psi.jsonl, rozpory.jsonl, teze.jsonl, postup.md
├── 03_vystupy/                # 10 souborů dle 2.11
├── logs/
└── docs/spec.md
```

Skripty se spouští jako moduly z kořene projektu (`python3 -m src.ocr --file <stem>`), aby cesty nezávisely na `cwd`.

`config/config.yaml` (inline, závazné výchozí hodnoty):

```yaml
zdroj_koren: /root/Uploads          # ASCII kořen, adresář se hledá přes os.walk (§2.14)
zdroj_filtr: Zpravodaj              # ASCII substring pro nalezení archivu
vylouceno: [Nov]                    # tvrdé vyloučení složky Nové/ (§1)
projekt: /root/chp-znalostni-databaze

ocr:
  dpi: 300
  dpi_vision: 200
  jazyk: ces
  psm: 3
  conf_threshold: 85.0
  min_slov_na_strance: 5

disk:
  guard_gb: 1.5

davky:
  1: [45, 46, 47, 48, 49, 50, 51]
  2: [52, 53, 54, 55, 56, 57, 58]
  3: [59, 60, 61, 62, 63, 64, 65]
  4: [66, 67, 68, 69, 70, 71, 72]
  5: [73, 74, 75, 76, 77, 78, 79]
  6: [80, 81, 82, 83, 84, 85, 86]
  7: [87, 88, 89, 90, 91, 92, 93]
  8: [94, 95, 96, 97, 98, 99, 100]
```

---

## 4. Testy (pytest)

Povinné pokrytí, případ po případu:

- **T1 — nalezení zdrojů:** `paths.py` najde přesně 56 PDF pod `/root/Uploads` s filtrem `Zpravodaj`, na syntetickém stromu s diakritickým názvem adresáře (test si adresář vytvoří sám, obě normalizace NFC i NFD) — musí projít v obou.
- **T2 — tvrdé vyloučení `Nové/`:** na syntetickém stromu s podadresářem `Nové/` obsahujícím PDF vrátí `paths.py` **nula** souborů z toho podadresáře. Zároveň grep test: v `src/`, `config/` ani `03_vystupy/` se nikde nevyskytuje řetězec `Nové` / `Nove` v roli cesty.
- **T3 — confidence a práh:** na syntetickém TSV výstupu ověřit výpočet průměru (ignoruje `conf = -1` a prázdná slova), správné vyhodnocení `>= 85.0` vs `< 85.0` a guard „méně než 5 slov → vždy needs_vision".
- **T4 — referenční integrita databáze (anti-halucinace):** pro každý záznam v `poznatky.jsonl` musí platit, že (a) `Cislo`+`Rok` odpovídá existující položce inventáře, (b) soubor uvedený v `Ocr_zdroj` na disku existuje, (c) `Strana` odpovídá hlavičce toho OCR souboru. Jakákoli neshoda = FAIL se seznamem vadných ID.
- **T5 — ověření doslovných citací (anti-halucinace):** každý úsek `Poznatek` uzavřený v `„...“` se musí objevit v textu odpovídajícího OCR souboru. Porovnání po normalizaci (lowercase, sloučení bílých znaků, odstranění dělení slov na konci řádku, odstranění `[nečitelné]`), tolerance `difflib.SequenceMatcher.ratio() >= 0.85` (OCR chybovost). Pod prahem = FAIL se seznamem ID.
- **T6 — validace schématu:** záznam bez některého povinného pole, s hodnotou mimo enum (`Kategorie`, `Typ_informace`, `Uroven`, `Duveryhodnost`, `Priorita`), s `KAT1` bez podkategorie `1A`–`1G`, nebo s `Uroven` C/D bez prefixu `SYNTÉZA: ` → odmítnut při zápisu.
- **T7 — formát citace:** validátor přijme přesně tři varianty z 2.2 a odmítne čtvrtou (např. chybějící `rok`, anglické uvozovky, `s.` bez čísla).
- **T8 — append-only:** dvojí zápis do `poznatky.jsonl` nikdy neztratí dřívější řádky; volání s existujícím `ID` je odmítnuto (duplicita ID).
- **T9 — fail-safe:** poškozený PDF (0 bajtů) a stránka, jejíž render selže, nezastaví běh — vznikne WARNING v logu, položka v inventáři s `chyba:` a běh pokračuje dalším souborem.
- **T10 — idempotence OCR:** druhý běh nad už zpracovaným souborem nepřepíše existující `page_XXXX.txt` a doběhne bez chyby.
- **T11 — disk guard:** při simulovaném volném místě pod `guard_gb` se běh zastaví před zpracováním dalšího souboru a dosavadní výstupy zůstanou nedotčené.
- **T12 — export:** z malé syntetické `poznatky.jsonl` vznikne validní `.xlsx` se všemi sloupci 2.5 v daném pořadí a `.docx` s očekávanými nadpisy; ověřit počet řádků a názvy listů.

`pytest` musí být zelený před každým gate. Testy nesmí sahat na reálná zdrojová PDF (kromě T1, který jen počítá soubory) — pracují na syntetických datech v `tmp_path`.

---

## 5. Fáze a gaty

| Fáze | Obsah | Gate |
|------|-------|------|
| **1** | Setup prostředí (apt tesseract+ces, pip balíčky), `config.yaml`, `paths.py`, `inventar.py`. Vygenerovat kompletní inventář 56 souborů + časovou osu + mezery. | Testy T1, T2 zelené + **Fajfka schválí inventář** (počty stran, roky, čísla sedí) a **rozhodne Otevřený bod O1** |
| **2** | OCR pipeline (`ocr.py`) postavená a spuštěná na **vzorku 3 čísel**: `45-1984-06` (nejstarší), `73-1994-07` (střed), `100-2008` (nejnovější). Vision dočtení flagged stránek vzorku. | Testy T3, T9, T10, T11 zelené + **Fajfka ručně zkontroluje OCR výstup vzorku proti skenu** (čitelnost, sloupce nerozházené, `[nečitelné]` použito poctivě). Zároveň se změří **podíl flagged stránek** → **rozhodnutí Otevřeného bodu O2** |
| **3** | OCR celého archivu (zbylých 53 souborů), soubor po souboru, s disk guardem. Následně 3b: vision dočtení všech flagged stránek, pak smazání `_vision/`. | Všech 56 souborů má `meta.json`; žádná stránka nezůstala ve stavu `tesseract-low`; disk v pořádku; krátký report (počet stran, podíl vision, problémové soubory) **Fajfkovi na vědomí** |
| **4** | Extrakce po dávkách 1–8, **sekvenčně** (§2.9). Subagent na dávku čte OCR text dávky a appenduje do `poznatky.jsonl`, `zdroje.jsonl`, `psi.jsonl`. | **Po dávce 1 STOP** — testy T4–T8 zelené nad výstupem dávky 1 + **Fajfka namátkově zkontroluje ~10 záznamů proti zdroji** (citace sedí, nic vymyšleného, nic podstatného nechybí). Teprve pak dávky 2–8. Po dávce 8 znovu T4–T8 nad celou databází. |
| **5** | 5a: skriptem `01_ARCHIVNI_INVENTAR.xlsx`, `02_DATABAZE_POZNATKU.xlsx`, `10_INDEX_ZDROJU.xlsx`. 5b: syntéza — `rozpory.jsonl`, `teze.jsonl`, pak 7 docx dokumentů, **jeden subagent na dokument, sekvenčně**, každý zapíše soubor na disk před spuštěním dalšího. | T12 zelený; všech 10 souborů existuje se jmény dle 2.11; **Fajfka přečte `04_EXECUTIVE_SUMMARY.docx` a `05_PRAKTICKA_APLIKACE.docx`** |
| **6** | Finální review s Fajfkou — kontrola konzistence, oprava nálezů, commit, zápis do memory. | **Rozhodovací kritérium § 6 splněno** = projekt uzavřen jako hotový, fáze 2 (`Nové/`) čeká na samostatný pokyn |

Každá fáze: testy zelené + krátký report Fajfkovi česky. **Nezačínat další fázi bez schválení gatu.**

**Gaty fáze 2 a 4 jsou výslovně lidské, ne automatické.** Kvalitu OCR historických skenů a věrnost extrakce nelze plně otestovat strojově — analogie k patternu „shoda s ruční kontrolou na vzorku" ze šablony pro infra/dashboard specy. „Testy zelené" tady NESTAČÍ.

**Observační gate po dokončení:** projekt nesahá na peníze ani na živý účet → **1 týden observace** ve smyslu „Fajfka databázi používá, hlásí nesrovnalosti". Bez dry-runu.

---

## 6. Rozhodovací kritérium (go/no-go)

Kritérium je **kvalitativní**, ne numerické — nejde o obchodní strategii, ale o věrnost archivu. Projekt se přijímá jen pokud platí **všechny** body:

1. **Žádná vymyšlená citace.** Fajfka vybere náhodně **10 záznamů** z `02_DATABAZE_POZNATKU.xlsx`, dohledá je ve zdrojovém PDF a u všech 10 sedí číslo, rok, strana i autor. **Tolerance: 0 chyb.** Jedna vymyšlená citace = no-go a povinná analýza příčiny.
2. **Automatické kontroly čisté.** Testy T4 (referenční integrita) a T5 (ověření doslovných citací) prochází nad **celou** databází bez FAILu.
3. **Žádná ztráta podstatné informace.** Fajfka vybere **2 celé stránky** ze zdroje a porovná je s OCR textem a s tím, co se z nich dostalo do databáze — na stránce nesmí zůstat nepovšimnutá podstatná chovatelská/tréninková informace. Drobné organizační zprávy (`KAT0`) nevadí.
4. **Rozlišení úrovní drží.** V namátkové kontrole není žádný záznam s `Uroven` = `A`, který je ve skutečnosti interpretace nebo doporučení implementera.
5. **Složka `Nové/` je netknutá.** V žádném výstupu, logu ani `Zdroj` poli se neobjeví soubor z `Nové/`.
6. Všech 10 výstupních souborů existuje pod přesnými jmény z 2.11 a otevřou se bez chyby.

**Když kritérium nevyjde:** nepřepisovat mlčky. Sepsat analýzu (co selhalo, na kolika záznamech, proč) a předložit Fajfkovi novou iteraci spec ke schválení. Legitimní výsledky jsou i **zúžení scope na čitelnější ročníky** nebo **snížení ambice u konkrétní kategorie** (např. genetika, pokud v archivu prostě není dost materiálu) — negativní zjištění je platné zjištění a zapisuje se, nikdy se nenahrazuje domyšleným obsahem.

---

## Otevřené body — eskalace na Fajfku

| Bod | Varianty + trade-off | Doporučení | Blokuje |
|---|---|---|---|
| **O1 — 56 souborů, ne 55: co se 3 nestandardními dokumenty** (`68-1992-11_sprezeni_special.pdf`, `71-1993-04_sprezeni_special.pdf`, `63-1992-01_chovatelsky_zapisni_rad.pdf`) | (A) zahrnout všechny 3 do plné analýzy — zápisní řád je přímý primární zdroj ke `KAT9` (podmínky zařazení do chovu), zvláštní čísla bývají tematická; cena: nutná zvláštní citační varianta (řešeno v 2.2). (B) zpracovat jen 53 řadových čísel, zbytek jen do inventáře; jednodušší, ale přijdeme o nejlepší zdroj ke `KAT9`. | **(A) zahrnout všechny 3**, označit v inventáři polem `Typ_dokumentu` | Gate fáze 1 |
| **O2 — co když je pod prahem 85 % příliš mnoho stránek** | Vzorek ve fázi 2 změří podíl flagged. Pokud vyjde **> 40 %**, hybrid přestává být „levný" a je třeba rozhodnout: (A) přijmout náklad a dočíst všechno visionem (nejvyšší kvalita, nejdražší), (B) snížit práh na 75 % a smířit se s vyšší chybovostí u části textu, (C) zkusit lepší preprocessing (vyšší dpi, `--psm 1`, binarizace) a přeměřit, (D) zúžit scope na čitelnější ročníky. | **(C) nejdřív přeměřit s lepším preprocessingem, pak rozhodnout mezi (A) a (B)** — a rozhodnout podle skutečného čísla, ne odhadem | Fázi 3 (OCR celého archivu) |

Otevřený bod **NIKDY nerozhoduje implementer.** Fáze, kterou blokuje, nesmí začít před Fajfkovým rozhodnutím.

---

## 7. Co spec záměrně NEřeší

- **Fáze 2 — porovnání historické × nové (`Nové/`, 2009–2025, 30 souborů).** Samostatná spec, až na výslovný pokyn. Až přijde, platí bod 42 master promptu: **NE nový souhrn**, ale srovnání s vyhodnocením `POTVRZENO / ČÁSTEČNĚ POTVRZENO / VYVRÁCENO / AKTUALIZOVÁNO / NOVÉ POZNATKY / STÁLE NEJISTÉ`. Podklad k tomu vzniká už teď: kapitola „TEZE K OVĚŘENÍ V NOVÝCH ZPRAVODAJÍCH" v `09_ROZPORY_A_NEOVERENE_TEZE.docx` + `teze.jsonl`.
- **Duplicitní soubor `111-2014_sprezeni_c_11 2.pdf` v `Nové/`** — jen evidováno v memory, neřeší se, do fáze 1 nepatří. (Pozor: podle `feedback_graphify_numbered_files` nejsou „ 2" soubory z graphify duplikáty; tenhle konkrétní ale duplikát je — nemazat, jen vyřešit ve fázi 2.)
- **Vyhledávací UI / integrace do HUBu** nad hotovou databází — možné pokračování, samostatné zadání. Teď stačí xlsx + JSONL.
- **Vektorové/sémantické vyhledávání nad OCR archivem** (embeddings, graphify import) — odloženo; `01_ocr_raw/` je k tomu připravený, ale není součástí tohoto zadání.
- **Modernizace doporučení podle současné veterinární literatury** — vědomě mimo scope, archiv se nesmí kontaminovat moderními zdroji (bod 35).
- **OCR čísel od 2019 dál**, která mají nativní textovou vrstvu a `pdftotext` by u nich stačil — patří do fáze 2.
