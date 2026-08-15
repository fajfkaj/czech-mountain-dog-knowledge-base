import json

import pytest

from src import ocr


# --- T3 — confidence a práh -------------------------------------------------

def test_t3_vypocti_confidence_ignoruje_zaporne_a_prazdne():
    conf = ["95.0", "-1", "80.0", "-1", "60.0"]
    text = ["pes", "", "spřežení", "  ", "leader"]
    prumer, pocet = ocr.vypocti_confidence(conf, text)
    assert pocet == 3
    assert prumer == pytest.approx((95.0 + 80.0 + 60.0) / 3)


def test_t3_vypocti_confidence_prazdny_vstup():
    prumer, pocet = ocr.vypocti_confidence([], [])
    assert (prumer, pocet) == (0.0, 0)


def test_t3_prah_nad_hranici_nepotrebuje_vision():
    assert ocr.potrebuje_vision(90.0, 50, prah=85.0, min_slov=5) is False


def test_t3_prah_pod_hranici_potrebuje_vision():
    assert ocr.potrebuje_vision(80.0, 50, prah=85.0, min_slov=5) is True


def test_t3_guard_malo_slov_ma_prednost_pred_prumerem():
    # vysoký průměr, ale jen 2 slova rozpoznaná → přesto needs_vision
    assert ocr.potrebuje_vision(99.0, 2, prah=85.0, min_slov=5) is True


# --- T9 — fail-safe ----------------------------------------------------------

def _cfg(tmp_path, guard_gb=0.0):
    return {
        "ocr": {"dpi": 300, "dpi_vision": 200, "jazyk": "ces", "psm": 3,
                "conf_threshold": 85.0, "min_slov_na_strance": 5},
        "disk": {"guard_gb": guard_gb},
    }


def test_t9_poskozeny_pdf_nezastavi_beh(tmp_path):
    poskozeny_pdf = tmp_path / "poskozeny.pdf"
    poskozeny_pdf.write_bytes(b"")  # 0 bajtů
    stem_dir = tmp_path / "stem"
    stem_dir.mkdir()
    cfg = _cfg(tmp_path)

    zaznam = ocr.zpracuj_stranku(poskozeny_pdf, 1, stem_dir, cfg, "1", 1984)

    assert zaznam["ocr_metoda"] == "selhalo"
    obsah = (stem_dir / "page_0001.txt").read_text(encoding="utf-8")
    assert ocr.NECITELNE in obsah
    assert "# OCR: selhalo" in obsah


def test_t9_zpracuj_soubor_pokracuje_po_selhani_stranky(tmp_path, monkeypatch):
    poskozeny_pdf = tmp_path / "poskozeny.pdf"
    poskozeny_pdf.write_bytes(b"")
    monkeypatch.setattr(ocr, "OCR_RAW_ROOT", tmp_path / "01_ocr_raw")
    cfg = _cfg(tmp_path)

    zprava = ocr.zpracuj_soubor(poskozeny_pdf, 3, cfg, "1", 1984)

    assert "3/3 stran" in zprava
    meta = json.loads((tmp_path / "01_ocr_raw" / poskozeny_pdf.stem / "meta.json").read_text())
    assert len(meta["stranky"]) == 3
    assert all(z["ocr_metoda"] == "selhalo" for z in meta["stranky"])


# --- T10 — idempotence --------------------------------------------------------

def test_t10_existujici_stranka_se_nepreepisuje(tmp_path):
    stem_dir = tmp_path / "stem"
    stem_dir.mkdir()
    sentinel = "# ZDROJ: sentinel, nepřepisovat\n---\npůvodní text"
    (stem_dir / "page_0001.txt").write_text(sentinel, encoding="utf-8")
    cfg = _cfg(tmp_path)

    zaznam = ocr.zpracuj_stranku(tmp_path / "neexistuje.pdf", 1, stem_dir, cfg, "1", 1984)

    assert zaznam.get("skipped") is True
    assert (stem_dir / "page_0001.txt").read_text(encoding="utf-8") == sentinel


def test_t10_zpracuj_soubor_druhy_beh_neselze(tmp_path, monkeypatch):
    monkeypatch.setattr(ocr, "OCR_RAW_ROOT", tmp_path / "01_ocr_raw")
    poskozeny_pdf = tmp_path / "poskozeny.pdf"
    poskozeny_pdf.write_bytes(b"")
    cfg = _cfg(tmp_path)

    ocr.zpracuj_soubor(poskozeny_pdf, 2, cfg, "1", 1984)
    stem_dir = tmp_path / "01_ocr_raw" / poskozeny_pdf.stem
    obsah_pred = (stem_dir / "page_0001.txt").read_text(encoding="utf-8")

    zprava = ocr.zpracuj_soubor(poskozeny_pdf, 2, cfg, "1", 1984)

    assert (stem_dir / "page_0001.txt").read_text(encoding="utf-8") == obsah_pred
    assert "2/2 stran" in zprava


# --- T11 — disk guard ----------------------------------------------------------

def test_t11_dost_mista_pod_prahem(monkeypatch, tmp_path):
    import shutil as shutil_modul

    class FalesnyUsage:
        free = int(0.5 * 1024**3)  # 0.5 GB volno

    monkeypatch.setattr(shutil_modul, "disk_usage", lambda cesta: FalesnyUsage())
    assert ocr.dost_mista(str(tmp_path), guard_gb=1.5) is False


def test_t11_zpracuj_soubor_zastavi_beh_pred_dalsi_strankou(tmp_path, monkeypatch):
    import shutil as shutil_modul

    class FalesnyUsage:
        free = int(0.5 * 1024**3)

    monkeypatch.setattr(shutil_modul, "disk_usage", lambda cesta: FalesnyUsage())
    monkeypatch.setattr(ocr, "OCR_RAW_ROOT", tmp_path / "01_ocr_raw")
    poskozeny_pdf = tmp_path / "poskozeny.pdf"
    poskozeny_pdf.write_bytes(b"")
    cfg = _cfg(tmp_path, guard_gb=1.5)

    with pytest.raises(ocr.NedostatekMista):
        ocr.zpracuj_soubor(poskozeny_pdf, 5, cfg, "1", 1984)

    stem_dir = tmp_path / "01_ocr_raw" / poskozeny_pdf.stem
    meta = json.loads((stem_dir / "meta.json").read_text())
    assert meta["stranky"] == []
