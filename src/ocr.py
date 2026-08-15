"""Fáze 2/3 — hybrid OCR pipeline (spec §2.8).

Tesseract (čeština) přečte každou stránku. Stránky pod prahem jistoty
(nebo s příliš málo rozpoznanými slovy) se označí `needs_vision` a jejich
PNG se ponechá pro ruční/AI dočtení (fáze 3b, mimo tento modul).

Idempotentní: existující `page_XXXX.txt` se znovu nezpracovává (T10).
Fail-safe: chyba na jedné stránce/souboru neshodí celý běh (T9).
Disk guard: běh se zastaví, než dojde místo (T11).

Spouštět jako modul z kořene projektu:
  python3 -m src.ocr --prefixy 45 73 100          # fáze 2 (vzorek)
  python3 -m src.ocr --vsechny                    # fáze 3 (celý archiv)
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
from pathlib import Path

import pytesseract
from PIL import Image

from src.inventar import nacti_config, INVENTAR_JSON

PROJEKT_ROOT = Path(__file__).resolve().parents[1]
OCR_RAW_ROOT = PROJEKT_ROOT / "01_ocr_raw"
LOG_PATH = PROJEKT_ROOT / "logs" / "ocr.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

NECITELNE = "[nečitelné]"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger("ocr")


class NedostatekMista(Exception):
    """Signalizuje, že disk guard zastavil běh."""


def dost_mista(cesta: str, guard_gb: float) -> bool:
    volne_gb = shutil.disk_usage(cesta).free / (1024**3)
    return volne_gb >= guard_gb


def vypocti_confidence(conf_list: list, text_list: list) -> tuple[float, int]:
    """T3 — průměr confidence přes slova s conf>=0 a neprázdným textem po strip()."""
    parovano = []
    for c, t in zip(conf_list, text_list):
        try:
            cf = float(c)
        except (TypeError, ValueError):
            continue
        if cf >= 0 and str(t).strip() != "":
            parovano.append(cf)
    if not parovano:
        return 0.0, 0
    return sum(parovano) / len(parovano), len(parovano)


def potrebuje_vision(prumer_conf: float, pocet_slov: int, prah: float, min_slov: int) -> bool:
    """T3 — guard na téměř prázdnou stránku má přednost před průměrem."""
    if pocet_slov < min_slov:
        return True
    return prumer_conf < prah


def render_stranku(pdf: Path, cislo_stranky: int, dpi: int, tmp_dir: Path) -> Path | None:
    """Renderuje jednu stránku PDF do PNG. Fail-safe: vrátí None při selhání (T9)."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    prefix = tmp_dir / "page"
    try:
        subprocess.run(
            [
                "pdftoppm", "-r", str(dpi), "-gray", "-png",
                "-f", str(cislo_stranky), "-l", str(cislo_stranky),
                str(pdf), str(prefix),
            ],
            check=True, capture_output=True, timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        log.warning("render selhal pro %s str.%d: %s", pdf.name, cislo_stranky, e)
        return None
    kandidati = sorted(tmp_dir.glob("page*.png"))
    return kandidati[0] if kandidati else None


def _slozit_text_z_dat(data: dict) -> str:
    """Poskládá čitelný text z image_to_data (řádek po řádku), aby stačilo
    jedno volání tesseractu na stránku místo dvou (image_to_string + image_to_data)."""
    radky: dict[tuple, list[str]] = {}
    for i, slovo in enumerate(data["text"]):
        if not str(slovo).strip():
            continue
        klic = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        radky.setdefault(klic, []).append(slovo)
    return "\n".join(" ".join(slova) for slova in radky.values())


def ocr_stranku(png: Path, jazyk: str, psm: int) -> dict:
    img = Image.open(png)
    data = pytesseract.image_to_data(
        img, lang=jazyk,
        config=f"--psm {psm} -c preserve_interword_spaces=1",
        output_type=pytesseract.Output.DICT,
    )
    prumer_conf, pocet_slov = vypocti_confidence(data["conf"], data["text"])
    text = _slozit_text_z_dat(data)
    return {"text": text, "conf": prumer_conf, "pocet_slov": pocet_slov}


def _nacti_meta(stem_dir: Path) -> dict:
    meta_path = stem_dir / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {"stranky": []}


def _uloz_meta(stem_dir: Path, meta: dict) -> None:
    (stem_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _zapis_stranku(stem_dir: Path, cislo_stranky: int, cislo_zprav: str, rok: int,
                    soubor: str, text: str, ocr_popis: str) -> None:
    hlavicka = (
        f"# ZDROJ: Spřežení č. {cislo_zprav}, rok {rok}, strana nezjištěna\n"
        f"# SOUBOR: {soubor}\n"
        f"# PDF_STRANA: {cislo_stranky}\n"
        f"# TISTENA_STRANA: nezjištěna\n"
        f"# OCR: {ocr_popis}\n"
        f"---\n"
    )
    cesta = stem_dir / f"page_{cislo_stranky:04d}.txt"
    cesta.write_text(hlavicka + text, encoding="utf-8")


def zpracuj_stranku(pdf: Path, cislo_stranky: int, stem_dir: Path, cfg: dict,
                     cislo_zprav: str, rok: int) -> dict:
    """Zpracuje jednu stránku. Idempotentní (T10), fail-safe (T9). Vrací záznam pro meta.json."""
    txt_cesta = stem_dir / f"page_{cislo_stranky:04d}.txt"
    if txt_cesta.exists():
        return {"skipped": True, "pdf_strana": cislo_stranky}

    ocr_cfg = cfg["ocr"]
    tmp_dir = stem_dir / "_tmp_render"
    try:
        png = render_stranku(pdf, cislo_stranky, ocr_cfg["dpi"], tmp_dir)
        if png is None:
            _zapis_stranku(stem_dir, cislo_stranky, cislo_zprav, rok, pdf.name,
                            NECITELNE, "selhalo")
            return {
                "pdf_strana": cislo_stranky, "tistena_strana": "nezjištěna",
                "conf": 0.0, "ocr_metoda": "selhalo", "pocet_slov": 0, "znaku": len(NECITELNE),
            }

        vysledek = ocr_stranku(png, ocr_cfg["jazyk"], ocr_cfg["psm"])
        needs_vision = potrebuje_vision(
            vysledek["conf"], vysledek["pocet_slov"],
            ocr_cfg["conf_threshold"], ocr_cfg["min_slov_na_strance"],
        )

        if needs_vision:
            metoda = "tesseract-low"
            vision_dir = stem_dir / "_vision"
            vision_dir.mkdir(parents=True, exist_ok=True)
            png_vision = render_stranku(pdf, cislo_stranky, ocr_cfg["dpi_vision"], tmp_dir)
            if png_vision is not None:
                shutil.copy(png_vision, vision_dir / f"page_{cislo_stranky:04d}.png")
            needs_vision_json = stem_dir / "needs_vision.json"
            seznam = json.loads(needs_vision_json.read_text(encoding="utf-8")) if needs_vision_json.exists() else []
            if cislo_stranky not in seznam:
                seznam.append(cislo_stranky)
            needs_vision_json.write_text(
                json.dumps(sorted(seznam), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        else:
            metoda = "tesseract"

        ocr_popis = f"tesseract-5.3.4 / {ocr_cfg['jazyk']} / conf {vysledek['conf']:.1f}"
        _zapis_stranku(stem_dir, cislo_stranky, cislo_zprav, rok, pdf.name,
                        vysledek["text"], ocr_popis)

        return {
            "pdf_strana": cislo_stranky, "tistena_strana": "nezjištěna",
            "conf": round(vysledek["conf"], 1), "ocr_metoda": metoda,
            "pocet_slov": vysledek["pocet_slov"], "znaku": len(vysledek["text"]),
        }
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def zpracuj_soubor(pdf: Path, pocet_stran: int, cfg: dict, cislo_zprav: str, rok: int) -> str:
    """Zpracuje celé PDF stránku po stránce. Vrací stavový text pro report."""
    stem_dir = OCR_RAW_ROOT / pdf.stem
    stem_dir.mkdir(parents=True, exist_ok=True)
    meta = _nacti_meta(stem_dir)
    hotove = {z["pdf_strana"] for z in meta["stranky"]}

    for cislo_stranky in range(1, pocet_stran + 1):
        if cislo_stranky in hotove:
            continue
        if not dost_mista(str(PROJEKT_ROOT), cfg["disk"]["guard_gb"]):
            _uloz_meta(stem_dir, meta)
            log.error("disk guard: zastaveno u %s str.%d", pdf.name, cislo_stranky)
            raise NedostatekMista(f"{pdf.name} str.{cislo_stranky}")
        try:
            zaznam = zpracuj_stranku(pdf, cislo_stranky, stem_dir, cfg, cislo_zprav, rok)
        except Exception as e:  # fail-safe (T9) — jedna stránka nesmí shodit celý běh
            log.warning("stránka selhala %s str.%d: %s", pdf.name, cislo_stranky, e)
            _zapis_stranku(stem_dir, cislo_stranky, cislo_zprav, rok, pdf.name,
                            NECITELNE, "selhalo")
            zaznam = {
                "pdf_strana": cislo_stranky, "tistena_strana": "nezjištěna",
                "conf": 0.0, "ocr_metoda": "selhalo", "pocet_slov": 0, "znaku": len(NECITELNE),
            }
        if not zaznam.get("skipped"):
            meta["stranky"].append(zaznam)
            meta["stranky"].sort(key=lambda z: z["pdf_strana"])
            _uloz_meta(stem_dir, meta)

    flagged = sum(1 for z in meta["stranky"] if z.get("ocr_metoda") == "tesseract-low")
    return f"{pdf.name}: {len(meta['stranky'])}/{pocet_stran} stran, {flagged} needs_vision"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefixy", nargs="*", type=int, help="jen tyto prefixy (fáze 2 vzorek)")
    parser.add_argument("--vsechny", action="store_true", help="celý archiv (fáze 3)")
    args = parser.parse_args()

    cfg = nacti_config()
    inventar = json.loads(INVENTAR_JSON.read_text(encoding="utf-8"))["Inventar"]

    if args.vsechny:
        vyber = inventar
    elif args.prefixy:
        vyber = [z for z in inventar if z["Prefix"] in args.prefixy]
    else:
        parser.error("zadej --prefixy N N N nebo --vsechny")
        return

    for zaznam in vyber:
        pdf = Path(cfg["zdroj_koren"])
        # najdeme reálnou cestu k souboru přes stejný mechanismus jako paths.py
        from src.paths import find_source_pdfs
        kandidati = [p for p in find_source_pdfs(cfg["zdroj_koren"], cfg["zdroj_filtr"], cfg["vylouceno"])
                     if p.name == zaznam["Nazev_souboru"]]
        if not kandidati:
            log.error("soubor nenalezen: %s", zaznam["Nazev_souboru"])
            continue
        pdf = kandidati[0]
        pocet_stran = zaznam["Pocet_stran"]
        if not isinstance(pocet_stran, int):
            log.warning("přeskakuji %s — neznámý počet stran", pdf.name)
            continue
        try:
            zprava = zpracuj_soubor(pdf, pocet_stran, cfg, zaznam["Cislo_zpravodaje"], zaznam["Rok"])
            log.info(zprava)
            print(zprava)
        except NedostatekMista:
            print("ZASTAVENO — nedostatek místa na disku, dosavadní výstupy zachovány")
            break


if __name__ == "__main__":
    main()
