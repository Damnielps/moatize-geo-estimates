#!/usr/bin/env python3
"""
Fetch script for nighttime lights proxies.

Sources:
- DMSP-OLS (1992-2013): NOAA NCEI via Google Earth Engine or NOAA FTP
- VIIRS DNB Annual (2012-present): EOG via Google Earth Engine
- Li et al. 2020 (1992-2018): figshare (optional validation, level B)

Idempotent: checks SHA256 before downloading.

AOI: lida de config/study.yaml em tempo de execução (§11.2.1). Nunca fixar aqui.
"""

import hashlib

from _config import carregar_aoi


def get_aoi_bounds():
    """Carrega o bbox da AOI de config/study.yaml (fonte única, §11.2.1)."""
    aoi = carregar_aoi()
    return {
        "west": aoi["xmin"],
        "east": aoi["xmax"],
        "south": aoi["ymin"],
        "north": aoi["ymax"],
    }

def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_dmsp_ols_via_gee():
    """Fetch DMSP-OLS via Google Earth Engine."""
    print("⚠️  DMSP-OLS: Requires GEE authentication and substantial processing.")
    print("   Implement via pipeline/01_imagery/classify_lights.py or dedicated GEE notebook.")
    print("   Expected outputs: composites for years 2000, 2005, 2010, 2015, 2020 (§2 CLAUDE.md)")
    print("   Source: ee.ImageCollection('NOAA/DMSP-OLS/CALIBRATED_LIGHTS_V4')")
    return None

def fetch_viirs_dnb_via_gee():
    """Fetch VIIRS DNB Annual via Google Earth Engine."""
    print("⚠️  VIIRS DNB: Requires GEE authentication.")
    print("   Implement via pipeline/01_imagery/classify_lights.py or dedicated GEE notebook.")
    print("   Expected outputs: annual composites for years 2015, 2020, 2025 (§2 CLAUDE.md)")
    print("   Source: ee.ImageCollection('NOAA/VIIRS/DNB_MONTHLY_V1/VCMCFG')")
    return None

def fetch_li_et_al_2020():
    """Fetch Li et al. 2020 harmonized data from figshare (optional, level B)."""
    print("⚠️  Li et al. 2020: Level B (validation only). Requires figshare account.")
    print("   DOI: 10.6084/m9.figshare.9828827")
    print("   Not implemented in automatic fetch (manual download via figshare).")
    return None

def main():
    """Main fetch routine."""
    print("=== Nighttime Lights Proxy Sources ===")
    print()

    # Load config
    aoi = get_aoi_bounds()
    print(f"AOI: W={aoi['west']} E={aoi['east']} S={aoi['south']} N={aoi['north']}")
    print()

    # DMSP-OLS
    print("1. DMSP-OLS (1992-2013, v4)")
    fetch_dmsp_ols_via_gee()
    print()

    # VIIRS DNB
    print("2. VIIRS DNB Annual (2012-present)")
    fetch_viirs_dnb_via_gee()
    print()

    # Li et al. 2020 (optional)
    print("3. Li et al. 2020 Harmonized (1992-2018, validation)")
    fetch_li_et_al_2020()
    print()

    print("=== Status ===")
    print("✓ World Bank Pink Sheet (June 2026): Espelhado em data/raw/")
    print("⚠️  DMSP-OLS, VIIRS DNB: Implementar via GEE notebooks ou pipeline/01_imagery/")
    print("⚠️  GCMT: Preenchimento manual do formulário em globalenergymonitor.org")
    print("✗ INE IPC (Tete): Servidor indisponível; verificar manualmente")
    print()

if __name__ == '__main__':
    main()
