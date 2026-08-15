"""Fáze 3c — vizuální archiv: raster každé stránky pro pozdější použití
(fotky psů, nákresy saní/postrojů/bud s rozměry, formuláře...).

Čistě CPU/pdftoppm, žádný LLM ani OCR — levné, běží pro všechny stránky,
i ty s vysokou OCR confidencí, kde se PNG v `ocr.py` maže. Zdroj pravdy
zůstává originální PDF v Uploads, tohle je jen kešovaná kopie pro rychlý
náhled bez nutnosti znovu-renderovat z PDF.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from src.inventar import nacti_config, INVENTAR_JSON
import json

PROJEKT = Path(__file__).resolve().parent.parent
VYSTUP_KOREN = PROJEKT / "05_vizualni_material"


def over_stranku(pdf: Path, cislo_stranky: int, dpi: int, cil: Path) -> bool:
    """Vyrenderuje jednu stránku PDF přímo do JPG. True = úspěch (T9-styl fail-safe)."""
    cil.parent.mkdir(parents=True, exist_ok=True)
    prefix = cil.parent / f"_tmp_{cislo_stranky}"
    try:
        subprocess.run(
            [
                "pdftoppm", "-r", str(dpi), "-gray", "-jpeg",
                "-f", str(cislo_stranky), "-l", str(cislo_stranky),
                str(pdf), str(prefix),
            ],
            check=True, capture_output=True, timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    kandidati = sorted(cil.parent.glob(f"_tmp_{cislo_stranky}*.jpg"))
    if not kandidati:
        return False
    kandidati[0].rename(cil)
    return True


def zpracuj_soubor(pdf: Path, stem: str, pocet_stran: int, dpi: int) -> tuple[int, int]:
    cil_dir = VYSTUP_KOREN / stem
    ok, chyby = 0, 0
    for n in range(1, pocet_stran + 1):
        cil = cil_dir / f"page_{n:04d}.jpg"
        if cil.exists():
            ok += 1
            continue
        if over_stranku(pdf, n, dpi, cil):
            ok += 1
        else:
            chyby += 1
    return ok, chyby


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefixy", nargs="*", type=int, required=True)
    args = parser.parse_args()

    cfg = nacti_config()
    inv = json.loads(INVENTAR_JSON.read_text(encoding="utf-8"))
    zaznamy = {r["Prefix"]: r for r in inv["Inventar"]}

    zdroj_koren = Path(cfg["zdroj_koren"])
    import os
    pdf_by_prefix: dict[int, Path] = {}
    for root, _dirs, files in os.walk(zdroj_koren):
        if cfg["zdroj_filtr"] not in root:
            continue
        for f in files:
            if f.endswith(".pdf"):
                pref = f.split("-")[0]
                if pref.isdigit():
                    pdf_by_prefix[int(pref)] = Path(root) / f

    for pref in args.prefixy:
        rec = zaznamy.get(pref)
        pdf = pdf_by_prefix.get(pref)
        if rec is None or pdf is None:
            print(f"{pref}: nenalezen v inventáři/zdroji, přeskočeno")
            continue
        stem = rec["Nazev_souboru"].removesuffix(".pdf")
        ok, chyby = zpracuj_soubor(pdf, stem, rec["Pocet_stran"], cfg["ocr"]["dpi_vision"])
        print(f"{stem}: {ok} stránek OK, {chyby} chyb")


if __name__ == "__main__":
    main()
