"""Generate loan-mix composition charts for the 9 non-CANBK banks, from the
screener Key-Points 'Advance/Loan Book Mix' (Q3 FY26, sourced). CANBK already has its
loan_mix + corp_exposure charts. Mirrors the CANBK exemplar standard.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from framework.charts import composition_chart      # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "charts"

# Domestic / gross advance mix, Q3 FY26 (sourced: screener Key Points panel).
LOAN_MIX = {
    "SBIN":       {"Retail": 42, "Corporate": 33, "SME": 15, "Agri": 10},
    "BANKBARODA": {"Corporate": 38, "Retail": 31, "Agriculture": 16, "MSME": 15},
    "PNB":        {"Corporate & Others": 43, "Retail": 24, "Agriculture": 16, "MSME": 16},
    "UNIONBANK":  {"Corporate & Other": 43, "Retail": 24, "Agriculture": 17, "MSME": 15},
    "INDIANB":    {"Corporates": 34, "Agriculture": 25, "Retail": 23, "MSME": 18},
    "BANKINDIA":  {"Corporate & Others": 41, "Retail": 25, "Agriculture": 18, "MSME": 16},
    "IOB":        {"Agri": 34, "Retail": 30, "Corporate/Others": 28, "MSME": 18},
    "MAHABANK":   {"Corporate & Other": 36, "Retail": 30, "MSME": 19, "Agriculture": 13, "Overseas": 1},
    "UCOBANK":    {"Corporate": 33, "Retail": 30, "MSME": 21, "Agri": 16},
}

if __name__ == "__main__":
    for sym, mix in LOAN_MIX.items():
        p = composition_chart(
            f"{sym} — domestic advance mix (Q3 FY26, sourced: screener)",
            mix, OUT / f"{sym}_loan_mix.png", unit="%")
        print("wrote", p, "sum=", sum(mix.values()), "%")
