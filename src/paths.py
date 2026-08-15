"""Bezpečné hledání zdrojových PDF v /root/Uploads (§2.14 spec).

Cesty s diakritikou (ř, ž) selhávají při ručním psaní literálu kvůli
NFC/NFD normalizaci Unicode. Řešení: nikdy neporovnávat celý accented
název adresáře — jen ASCII substringy, a vždy chodit přes os.walk()
z ASCII kořene s path objekty, které walk sám vrátí.
"""
from __future__ import annotations

import os
from pathlib import Path


def find_source_pdfs(zdroj_koren: str, zdroj_filtr: str, vylouceno: list[str]) -> list[Path]:
    """Najde všechny .pdf pod `zdroj_koren`, jejichž cesta obsahuje ASCII
    substring `zdroj_filtr`, a vynechá jakýkoli adresář, jehož jméno
    obsahuje některý z `vylouceno` substringů (podadresář s novějšími
    čísly zpravodaje je takto natvrdo vyřazen ze scope fáze 1).

    Vyloučení se řeší úpravou `dirs` in-place během os.walk (topdown),
    takže se do vyloučených podadresářů vůbec nesestoupí.
    """
    nalezene: list[Path] = []
    for root, dirs, files in os.walk(zdroj_koren):
        dirs[:] = sorted(
            d for d in dirs if not any(v in d for v in vylouceno)
        )
        if zdroj_filtr not in root:
            continue
        for f in files:
            if f.lower().endswith(".pdf"):
                nalezene.append(Path(root) / f)
    return sorted(nalezene, key=lambda p: p.name)
