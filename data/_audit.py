"""Data-source audit: hit each live source, report shape/columns/sample.

Run:  uv run python -m data._audit
This is a VERIFICATION harness, not production code. It tells us which sources
actually return clean data today, and exactly what shape, before we build on them.
"""

from __future__ import annotations

import datetime as dt
import traceback


def _ok(name: str, df) -> None:
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            print(f"\n[OK] {name}: DataFrame {df.shape}, cols={list(df.columns)[:12]}")
            print(df.tail(2).to_string()[:600])
        else:
            n = len(df) if hasattr(df, "__len__") else "?"
            print(f"\n[OK] {name}: {type(df).__name__} len={n} sample={str(df)[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"\n[OK?] {name}: returned {type(df)} but display failed: {e}")


def _fail(name: str, e: Exception) -> None:
    print(f"\n[FAIL] {name}: {type(e).__name__}: {e}")
    print("       " + traceback.format_exc().strip().replace("\n", "\n       ")[-700:])


def audit() -> None:
    end = dt.date.today()
    start = end - dt.timedelta(days=120)

    # 1. jugaad-data — primary historical backtest source
    try:
        from jugaad_data.nse import stock_df
        df = stock_df(symbol="RELIANCE", from_date=start, to_date=end, series="EQ")
        _ok("jugaad stock_df(RELIANCE)", df)
    except Exception as e:  # noqa: BLE001
        _fail("jugaad stock_df", e)

    # 2. nsepython — indices / constituents / FII-DII
    try:
        from nsepython import nse_eq
        _ok("nsepython nse_eq(RELIANCE)", nse_eq("RELIANCE"))
    except Exception as e:  # noqa: BLE001
        _fail("nsepython nse_eq", e)
    try:
        import nsepython as np
        fn = [x for x in dir(np) if "fii" in x.lower() or "dii" in x.lower() or "index" in x.lower()]
        print(f"\n[INFO] nsepython index/fii fns: {fn}")
    except Exception as e:  # noqa: BLE001
        _fail("nsepython dir", e)

    # 3. yfinance — fallback
    try:
        import yfinance as yf
        df = yf.download("RELIANCE.NS", start=start, end=end, progress=False)
        _ok("yfinance RELIANCE.NS", df)
    except Exception as e:  # noqa: BLE001
        _fail("yfinance", e)

    # 4. mftool — AMFI scheme NAV (the missing 'schemes' piece)
    try:
        from mftool import Mftool
        mf = Mftool()
        schemes = mf.get_scheme_codes()
        print(f"\n[OK] mftool get_scheme_codes: {len(schemes)} schemes")
        # pick one banking-ish scheme code to test NAV history
        code = next(iter(schemes))
        _ok(f"mftool get_scheme_historical_nav({code})",
            mf.get_scheme_historical_nav(code))
    except Exception as e:  # noqa: BLE001
        _fail("mftool", e)

    # 5. niftystocks — live sectoral constituents
    try:
        from niftystocks import ns
        _ok("niftystocks get_nifty_it", ns.get_nifty_it())
    except Exception as e:  # noqa: BLE001
        _fail("niftystocks", e)


if __name__ == "__main__":
    audit()
