"""Focused round-2 audit: the functions we ACTUALLY need from nsepython + mftool.

Round-1 (_audit.py) found jugaad/yfinance/mftool-codes work; niftystocks stale;
nse_eq blocked. This probes the real targets: NSE index history, FII/DII, and a
real mutual-fund NAV series.
"""

from __future__ import annotations

import datetime as dt
import traceback


def show(name, obj):
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            print(f"\n[OK] {name}: DataFrame {obj.shape} cols={list(obj.columns)[:10]}")
            print(obj.head(3).to_string()[:500])
        elif isinstance(obj, (list, dict)):
            print(f"\n[OK] {name}: {type(obj).__name__} len={len(obj)} sample={str(obj)[:400]}")
        else:
            print(f"\n[OK] {name}: {type(obj).__name__} = {str(obj)[:400]}")
    except Exception as e:  # noqa: BLE001
        print(f"\n[OK?] {name}: {type(obj)} display err {e}")


def fail(name, e):
    print(f"\n[FAIL] {name}: {type(e).__name__}: {e}")
    print("   " + traceback.format_exc().strip().splitlines()[-1])


def main():
    end = dt.date.today()
    start = end - dt.timedelta(days=120)
    d, m, y = "%d-%b-%Y", None, None

    # nsepython: index OHLC history (sector index price series we need for rel-strength)
    try:
        from nsepython import index_history
        df = index_history("NIFTY PSU BANK", start.strftime(d), end.strftime(d))
        show("nsepython index_history(NIFTY PSU BANK)", df)
    except Exception as e:  # noqa: BLE001
        fail("nsepython index_history", e)

    # nsepython: FII/DII daily cash flows (institutional flow = core thesis input)
    try:
        from nsepython import nse_fiidii
        show("nsepython nse_fiidii", nse_fiidii())
    except Exception as e:  # noqa: BLE001
        fail("nsepython nse_fiidii", e)

    # nsepython: list of indices (to validate names for index_history)
    try:
        from nsepython import nse_get_index_list
        lst = nse_get_index_list()
        show("nsepython nse_get_index_list", lst)
    except Exception as e:  # noqa: BLE001
        fail("nsepython nse_get_index_list", e)

    # mftool: real scheme NAV history. Pick a real banking-fund code from the map.
    try:
        from mftool import Mftool
        mf = Mftool()
        codes = mf.get_scheme_codes()  # dict {code: name}
        # find a banking/PSU scheme to make it relevant
        hit = next(((c, n) for c, n in codes.items()
                    if "bank" in str(n).lower() and "psu" in str(n).lower()), None)
        if hit is None:
            hit = next(((c, n) for c, n in codes.items() if "bank" in str(n).lower()), None)
        code, nm = hit
        print(f"\n[INFO] mftool picked code={code} name={nm}")
        nav = mf.get_scheme_historical_nav(code)
        show(f"mftool get_scheme_historical_nav({code})", nav)
    except Exception as e:  # noqa: BLE001
        fail("mftool NAV", e)


if __name__ == "__main__":
    main()
