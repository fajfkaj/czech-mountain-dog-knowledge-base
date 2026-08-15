import unicodedata

from src.paths import find_source_pdfs

DIAKR_JMENO = "Zpravodaj Spřežení"
VYLOUCENO = ["Nov"]


def _postav_strom(base, jmeno_adresare_forma):
    """Postaví syntetický strom s adresářem `jmeno_adresare_forma` (NFC nebo NFD)
    obsahujícím 3 PDF a podadresářem Nové/ s 1 PDF navíc."""
    root_dir = base / jmeno_adresare_forma
    root_dir.mkdir(parents=True)
    for i in range(3):
        (root_dir / f"soubor_{i}.pdf").write_bytes(b"%PDF-1.4 test")
    nove_dir = root_dir / "Nové"
    nove_dir.mkdir()
    (nove_dir / "novy.pdf").write_bytes(b"%PDF-1.4 test")
    return root_dir


def test_t1_nalezeni_zdroju_nfc(tmp_path):
    jmeno_nfc = unicodedata.normalize("NFC", DIAKR_JMENO)
    _postav_strom(tmp_path, jmeno_nfc)
    nalezene = find_source_pdfs(str(tmp_path), "Zpravodaj", VYLOUCENO)
    assert len(nalezene) == 3


def test_t1_nalezeni_zdroju_nfd(tmp_path):
    jmeno_nfd = unicodedata.normalize("NFD", DIAKR_JMENO)
    _postav_strom(tmp_path, jmeno_nfd)
    nalezene = find_source_pdfs(str(tmp_path), "Zpravodaj", VYLOUCENO)
    assert len(nalezene) == 3


def test_t2_tvrde_vylouceni_nove(tmp_path):
    jmeno = unicodedata.normalize("NFC", DIAKR_JMENO)
    root_dir = _postav_strom(tmp_path, jmeno)
    nalezene = find_source_pdfs(str(tmp_path), "Zpravodaj", VYLOUCENO)
    assert all("Nov" not in p.parent.name for p in nalezene)
    assert not any((root_dir / "Nové" / "novy.pdf").samefile(p) for p in nalezene)


def test_t2_grep_zadne_nove_v_projektu():
    import pathlib

    projekt = pathlib.Path(__file__).resolve().parents[1]
    zakazane = ["Nové", "Nove"]
    prohledat = [projekt / "src", projekt / "config", projekt / "03_vystupy"]
    nalezy = []
    for adresar in prohledat:
        if not adresar.exists():
            continue
        for soubor in adresar.rglob("*"):
            if not soubor.is_file():
                continue
            try:
                obsah = soubor.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for zakaz in zakazane:
                if zakaz in obsah:
                    nalezy.append((str(soubor), zakaz))
    assert nalezy == [], f"nalezeno zakázané 'Nové/Nove' v projektových souborech: {nalezy}"
