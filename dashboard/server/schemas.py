"""Stable v1 response fields. Returns are decimal fractions, dates are ISO strings."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)


class Run(Model):
    id: str
    label: str
    finished_utc: str
    status: Literal["passed"]
    models_loaded: int
    prediction_rows: int
    prediction_weeks: int
    backtest_weeks: int
    manifest_sha256: str


class Runs(Model):
    runs: list[Run]
    default_run_id: str | None
    rejected_runs: int


class Health(Model):
    status: Literal["ok"]
    verified_runs: int
    rejected_runs: int


class PublicConfig(Model):
    app_version: str
    api_version: Literal["v1"]
    public_url: str
    data_mode: Literal["historical_read_only"]


class Summary(Model):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    initial_capital: float
    final_capital: float
    total_return: float = Field(description="Decimal fraction, 0.10 means 10%")
    annualized_return: float
    sharpe: float
    max_drawdown: float
    weeks: int
    first_signal: str
    last_signal: str
    cost_bps: float
    win_rate: float
    total_fees: float
    strategy: str


class Overview(Model):
    run: Run
    summary: Summary
    dates: list[str]
    prediction_first_date: str
    prediction_last_date: str
    ticker_count: int
    ranking_notice: str


class EquityRow(Model):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    date: str
    start_capital: float
    end_capital: float
    net_return: float
    cash: float
    fees: float
    drawdown: float = Field(
        description="Computed using all preceding history, including initial capital"
    )


class Equity(Model):
    rows: list[EquityRow]


class RankingRow(Model):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    date: str
    ticker: str
    ensemble_predicted_rank: int
    ensemble_ranking_score: float = Field(
        description="Mean of three weekly percentile scores; not a return forecast"
    )
    model_1_percentile: float
    model_2_percentile: float
    model_3_percentile: float


class Rankings(Model):
    date: str
    total: int
    page: int
    page_size: int
    rows: list[RankingRow]


class ErrorDetail(Model):
    code: str
    message: str
    request_id: str
    fields: list[str] = []


class ErrorResponse(Model):
    error: ErrorDetail
    detail: str = Field(description="Compatibility message for legacy /api clients")


class InputColumn(Model):
    key: str
    label: str
    type: Literal["string", "number"]


class InputDataset(Model):
    id: Literal["factors", "prices"]
    title: str
    purpose: str
    source_file: str
    sha256: str
    bytes: int
    source_rows: int
    source_dates: list[str]
    output_aligned_rows: int
    output_dates: list[str]
    ticker_count: int
    columns: list[InputColumn]
    source_columns: list[str]
    omitted_columns: list[str]


class InputCatalog(Model):
    available: bool
    reason: str | None
    run_id: str
    datasets: list[InputDataset]
    model: dict[str, str | int] | None


class InputRows(Model):
    dataset: Literal["factors", "prices"]
    scope: Literal["output", "source"]
    date: str | None
    total: int
    page: int
    page_size: int
    rows: list[dict[str, str | float]]
