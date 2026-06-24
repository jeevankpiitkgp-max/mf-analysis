import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SCHEMES = {
    "HDFC_Top_100_Direct": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841,
}

def fetch_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    meta = data.get("meta", {})
    nav_df = pd.DataFrame(data.get("data", []))
    nav_df["scheme_code"] = scheme_code
    nav_df["scheme_name"] = meta.get("scheme_name")
    return nav_df, meta

if __name__ == "__main__":
    all_nav = []
    for name, code in SCHEMES.items():
        try:
            nav_df, meta = fetch_nav(code)
            outfile = RAW_DIR / f"live_nav_{name}.csv"
            nav_df.to_csv(outfile, index=False)
            print(f"✅ {name} ({code}): {len(nav_df)} records saved to {outfile.name}")
            print(f"   Fund house: {meta.get('fund_house')}, Scheme type: {meta.get('scheme_type')}")
            all_nav.append(nav_df)
        except Exception as e:
            print(f"❌ Failed for {name} ({code}): {e}")

    if all_nav:
        combined = pd.concat(all_nav, ignore_index=True)
        combined.to_csv(RAW_DIR / "live_nav_combined.csv", index=False)
        print(f"\nCombined live NAV history: {combined.shape[0]} rows, {combined.shape[1]} columns")
        print(f"Schemes covered: {combined['scheme_name'].nunique()}")