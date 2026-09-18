"""SEC Company Facts helper for the six external financial factors."""

from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


CIK_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "")
SEC_REQUEST_TIMEOUT_SECONDS = 5

FUNDAMENTAL_DEFINITIONS = [
    ("revenue_growth_yoy", "Quarter revenue / revenue from the same fiscal quarter last year - 1"),
    ("gross_margin_change_yoy", "Current TTM gross margin minus TTM gross margin four quarters earlier"),
    ("operating_profitability", "TTM operating income / average assets versus the same quarter last year"),
    ("cashflow_to_assets", "TTM operating cash flow / average assets versus the same quarter last year"),
    ("debt_to_assets", "Interest-bearing debt / total assets at the reporting date"),
    ("asset_growth_yoy", "Current total assets / total assets four quarters earlier - 1"),
]

TAGS = {
    "revenue": ("us-gaap", ["RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "Revenues"]),
    "gross_profit": ("us-gaap", ["GrossProfit"]),
    "cost_of_revenue": ("us-gaap", ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]),
    "operating_income": ("us-gaap", ["OperatingIncomeLoss"]),
    "operating_cash_flow": ("us-gaap", ["NetCashProvidedByUsedInOperatingActivities"]),
    "assets": ("us-gaap", ["Assets"]),
    "debt": ("us-gaap", ["LongTermDebtAndCurrent", "LongTermDebtCurrent", "LongTermDebtNoncurrent"]),
}


def require_user_agent() -> None:
    if "@" not in SEC_USER_AGENT or "your.email" in SEC_USER_AGENT.lower():
        raise RuntimeError("PLEASE SET TARE VALUE SEC_USER_AGENT，for example $env:SEC_USER_AGENT = 'SafeCapitalCoursework/1.0 your email@university.edu.au'")


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": SEC_USER_AGENT})
    with urlopen(request, timeout=SEC_REQUEST_TIMEOUT_SECONDS) as response:
        payload = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"
    time.sleep(0.2)
    return json.loads(payload.decode(encoding))


def cik_by_ticker() -> dict[str, int]:
    payload = fetch_json(CIK_URL)
    positions = {name: index for index, name in enumerate(payload["fields"])}
    return {str(row[positions["ticker"]]).upper(): int(row[positions["cik"]]) for row in payload["data"] if row[positions["ticker"]]}


def fact_rows(facts: dict[str, Any], taxonomy: str, tags: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    concepts = facts.get("facts", {}).get(taxonomy, {})
    for priority, tag in enumerate(tags):
        entries = concepts.get(tag, {}).get("units", {}).get("USD", [])
        if entries:
            frame = pd.DataFrame(entries)
            frame["priority"] = priority
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    data = pd.concat(frames, ignore_index=True)
    data = data.loc[data["form"].isin(["10-Q", "10-K"])].copy()
    for name in ("start", "end", "filed"):
        if name in data:
            data[name] = pd.to_datetime(data[name], errors="coerce")
        elif name == "start":
            data[name] = pd.NaT
    data["val"] = pd.to_numeric(data["val"], errors="coerce")
    return data.dropna(subset=["end", "filed", "val"])


def duration_values(facts: pd.DataFrame) -> pd.DataFrame:
    """Convert 10-Q year-to-date values to discrete quarters, then TTM."""
    if facts.empty:
        return pd.DataFrame(columns=["end", "filed", "quarter", "ttm"])
    data = facts.dropna(subset=["start"]).copy()
    data["days"] = (data["end"] - data["start"]).dt.days + 1
    data = data.loc[data["days"].between(20, 400)].sort_values(["end", "days", "priority", "filed"], ascending=[True, False, True, True])
    data = data.drop_duplicates("end", keep="first")
    data["fy_group"] = data.get("fy", data["end"].dt.year).fillna(data["end"].dt.year).astype(str)
    data = data.sort_values(["fy_group", "end"]).reset_index(drop=True)
    data["quarter"] = data.groupby("fy_group")["val"].diff().fillna(data["val"])
    data["ttm"] = data["quarter"].rolling(4, min_periods=4).sum()
    return data[["end", "filed", "quarter", "ttm"]]


def instant_values(facts: pd.DataFrame, name: str) -> pd.DataFrame:
    if facts.empty:
        return pd.DataFrame(columns=["end", f"filed_{name}", name])
    data = facts.sort_values(["end", "priority", "filed"]).drop_duplicates("end", keep="first")
    return data[["end", "filed", "val"]].rename(columns={"filed": f"filed_{name}", "val": name})


def financial_quarters(facts: dict[str, Any]) -> pd.DataFrame:
    duration: dict[str, pd.DataFrame] = {}
    for name in ("revenue", "gross_profit", "cost_of_revenue", "operating_income", "operating_cash_flow"):
        taxonomy, tags = TAGS[name]
        duration[name] = duration_values(fact_rows(facts, taxonomy, tags))
    quarters = duration["revenue"].rename(columns={"filed": "filed_revenue", "quarter": "revenue_q", "ttm": "revenue_ttm"})
    for name in ("gross_profit", "cost_of_revenue", "operating_income", "operating_cash_flow"):
        item = duration[name].rename(columns={"filed": f"filed_{name}", "quarter": f"{name}_q", "ttm": f"{name}_ttm"})
        quarters = quarters.merge(item, on="end", how="outer")
    for name in ("assets", "debt"):
        taxonomy, tags = TAGS[name]
        quarters = quarters.merge(instant_values(fact_rows(facts, taxonomy, tags), name), on="end", how="outer")
    filed = [column for column in quarters if column.startswith("filed_")]
    quarters["available_date"] = quarters[filed].apply(pd.to_datetime, errors="coerce").max(axis=1)
    quarters = quarters.dropna(subset=["end", "available_date"]).sort_values("end").reset_index(drop=True)
    average_assets = (quarters["assets"] + quarters["assets"].shift(4)) / 2
    gross_profit = quarters["gross_profit_ttm"].combine_first(quarters["revenue_ttm"] - quarters["cost_of_revenue_ttm"])
    gross_margin = gross_profit / quarters["revenue_ttm"]
    quarters["revenue_growth_yoy"] = quarters["revenue_q"] / quarters["revenue_q"].shift(4) - 1
    quarters["gross_margin_change_yoy"] = gross_margin - gross_margin.shift(4)
    quarters["operating_profitability"] = quarters["operating_income_ttm"] / average_assets
    quarters["cashflow_to_assets"] = quarters["operating_cash_flow_ttm"] / average_assets
    quarters["debt_to_assets"] = quarters["debt"] / quarters["assets"]
    quarters["asset_growth_yoy"] = quarters["assets"] / quarters["assets"].shift(4) - 1
    names = [name for name, _ in FUNDAMENTAL_DEFINITIONS]
    quarters[names] = quarters[names].replace([np.inf, -np.inf], np.nan)
    return quarters[["available_date", *names]]


def next_market_day(dates: pd.Series, market_dates: pd.Series) -> pd.Series:
    calendar = pd.DatetimeIndex(pd.to_datetime(market_dates).dropna().unique()).sort_values()
    positions = calendar.searchsorted(pd.DatetimeIndex(pd.to_datetime(dates)), side="right")
    return pd.Series([calendar[p] if p < len(calendar) else pd.NaT for p in positions], index=dates.index)


def collect_financial_factors(base: pd.DataFrame, market_dates: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch each available issuer and point-in-time merge its six factors."""
    names = [name for name, _ in FUNDAMENTAL_DEFINITIONS]
    result = base[["date", "ticker"]].copy()
    for name in names:
        result[name] = np.nan
    mapping = cik_by_ticker()
    logs: list[dict[str, str]] = []
    all_quarters: list[pd.DataFrame] = []
    for ticker in sorted(base["ticker"].unique()):
        cik = mapping.get(ticker) or mapping.get(ticker.replace("-", "."))
        if cik is None:
            logs.append({"ticker": ticker, "status": "failed", "message": "Ticker not in SEC mapping"})
            continue
        try:
            quarters = financial_quarters(fetch_json(FACTS_URL.format(cik=cik)))
            if quarters.empty:
                raise ValueError("No usable 10-Q/10-K facts")
            quarters["ticker"] = ticker
            quarters["available_at"] = next_market_day(quarters["available_date"], market_dates)
            all_quarters.append(quarters.dropna(subset=["available_at"]))
            logs.append({"ticker": ticker, "status": "success", "message": ""})
        except Exception as error:
            logs.append({"ticker": ticker, "status": "failed", "message": str(error)})
    if not all_quarters:
        return result, pd.DataFrame(logs)
    all_data = pd.concat(all_quarters, ignore_index=True)
    frames: list[pd.DataFrame] = []
    for ticker, keys in base[["date", "ticker"]].groupby("ticker", sort=False):
        events = all_data.loc[all_data["ticker"] == ticker, ["available_at", *names]].sort_values("available_at")
        if events.empty:
            joined = keys.copy()
            for name in names:
                joined[name] = np.nan
        else:
            joined = pd.merge_asof(keys.sort_values("date"), events, left_on="date", right_on="available_at", direction="backward").drop(columns="available_at")
        frames.append(joined)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(logs)
