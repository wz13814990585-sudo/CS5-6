"""Training preparation from supplied processed weekly data only."""
from __future__ import annotations
import numpy as np
import pandas as pd
import exchange_calendars as xcals
from . import ROOT
from .contracts import ContractError, require, sha, write_frame, write_json

FEATURES = ['revenue_growth_yoy', 'operating_profitability', 'cashflow_to_assets',
            'debt_to_assets', 'asset_growth_yoy']

DAILY_PRICES = ROOT / 'data/clean_basic_data.csv'


def read_csv(path):
    return pd.read_csv(path, float_precision='round_trip', parse_dates=['date'])


def nyse_calendar(start, end):
    return xcals.get_calendar('XNYS', start=str(pd.Timestamp(start).date()), end=str(pd.Timestamp(end).date()))


def execution_dates(signal_dates):
    dates = pd.Series(pd.to_datetime(signal_dates)).reset_index(drop=True)
    cal = nyse_calendar(dates.min() - pd.Timedelta(days=7), dates.max() + pd.Timedelta(days=21))
    sessions = pd.Series(cal.sessions.tz_localize(None))
    ends = sessions.groupby(sessions.dt.to_period('W-FRI')).max()
    starts = sessions.groupby(sessions.dt.to_period('W-FRI')).min()
    periods = dates.dt.to_period('W-FRI')
    require(all(dates.eq(periods.map(ends))), 'Signal dates must be final official NYSE sessions of complete weeks')
    return pd.DataFrame({'date': dates, 'expected_buy_date': (periods + 1).map(starts),
                         'expected_sell_date': (periods + 1).map(ends)})


def validate_panel(frame, name, expected_tickers, numeric):
    require({'date', 'ticker', *numeric} <= set(frame), f'{name}: missing columns')
    require(not frame.empty and not frame.duplicated(['date', 'ticker']).any(), f'{name}: empty or duplicate keys')
    require(frame.date.notna().all() and frame.ticker.notna().all(), f'{name}: missing keys')
    require(set(frame.ticker) == expected_tickers, f'{name}: unexpected/missing ticker universe')
    require(np.isfinite(frame[numeric].to_numpy(float)).all(), f'{name}: NaN or infinite numeric inputs')
    execution_dates(frame.date.drop_duplicates())



def preflight():
    files = [ROOT / 'data/reproducible/train66_corrected_complete.csv',
             ROOT / 'data/reproducible/train_universe.csv',
             DAILY_PRICES]
    return files, [str(p) for p in files if not p.is_file()]


def verify_targets_against_daily(train, daily=None):
    """Check every label, including rows before a missing week and the final week.

    The adjacent-week check cannot see rows whose next weekly row is absent, so each
    target is recomputed as ln(daily adj close on label_end_date / weekly adj close).
    """
    if daily is None:
        daily = pd.read_csv(DAILY_PRICES, usecols=['date', 'ticker', 'adj_close'],
                            parse_dates=['date'], float_precision='round_trip')
    daily = daily[daily.ticker.isin(set(train.ticker))]
    require(not daily.duplicated(['date', 'ticker']).any(), 'Daily prices: duplicate date/ticker keys')
    reference = daily.rename(columns={'adj_close': 'daily_close'})
    start = train[['date', 'ticker']].merge(reference, on=['date', 'ticker'], how='left', validate='one_to_one')
    end = train[['label_end_date', 'ticker']].merge(
        reference.rename(columns={'date': 'label_end_date', 'daily_close': 'label_close'}),
        on=['label_end_date', 'ticker'], how='left', validate='many_to_one')
    require(start.daily_close.notna().all(), 'Daily price missing for a training signal date')
    require(end.label_close.notna().all() and end.label_close.gt(0).all(),
            'Daily price missing or nonpositive on a training label end date')
    require(np.allclose(train.adj_close.to_numpy(float), start.daily_close.to_numpy(float), rtol=1e-12, atol=1e-8),
            'Weekly training price differs from the daily adjusted close')
    expected = np.log(end.label_close.to_numpy(float) / train.adj_close.to_numpy(float))
    bad = ~np.isclose(train.target.to_numpy(float), expected, rtol=0, atol=1e-8)
    if bad.any():
        sample = train.loc[bad, ['ticker', 'date', 'target']].head(5).to_dict('records')
        raise ContractError(f'{int(bad.sum())} training targets differ from the daily next-week close return, e.g. {sample}')
    return int(len(train))


def prepare_training(train):
    universe = pd.read_csv(ROOT / 'data/reproducible/train_universe.csv')
    require(len(universe) == 66 and universe.ticker.notna().all() and not universe.ticker.duplicated().any(),
            'Training universe must contain 66 distinct tickers')
    train = train.sort_values(['date', 'ticker'], kind='stable').reset_index(drop=True).copy()
    validate_panel(train, 'train', set(universe.ticker), ['adj_close', 'target', *FEATURES])
    require(train.adj_close.gt(0).all(), 'Nonpositive training price')
    calendar = pd.DatetimeIndex(sorted(train.date.unique()))
    periods = calendar.to_period('W-FRI')
    require(all(periods[1:] == periods[:-1] + 1), 'Training calendar skips an entire trading week')
    require(len(calendar) == 521 and calendar[0] == pd.Timestamp('2016-09-02')
            and calendar[-1] == pd.Timestamp('2026-08-21'), 'Unexpected supplied weekly training coverage')
    train['week_index'] = train.date.map({d: i for i, d in enumerate(calendar)}).astype(int)
    train = train.drop(columns=['label_end_date'], errors='ignore').merge(
        execution_dates(calendar).rename(columns={'expected_sell_date': 'label_end_date'}),
        on='date', validate='many_to_one').drop(columns='expected_buy_date')
    ordered = train.sort_values(['ticker', 'date'])
    future_index = ordered.groupby('ticker').week_index.shift(-1)
    future_price = ordered.groupby('ticker').adj_close.shift(-1)
    check = future_index.eq(ordered.week_index + 1)
    require(np.allclose(ordered.loc[check, 'target'],
                        np.log(future_price[check] / ordered.loc[check, 'adj_close']),
                        rtol=0, atol=1e-8), 'Training target is not its documented next-week close return')
    verify_targets_against_daily(train)
    return train


def prepare(run, options):
    destination = run / 'prepare'
    source = ROOT / 'data/reproducible/train66_corrected_complete.csv'
    train = prepare_training(read_csv(source))
    write_frame(train, destination / 'train.csv')
    calendar = train[['date', 'week_index', 'label_end_date']].drop_duplicates().sort_values('date')
    write_frame(calendar, destination / 'calendar.csv')
    info = dict(protocol='processed-weekly-ensemble-training-v1', weeks=len(calendar),
                training_rows=len(train), training_tickers=int(train.ticker.nunique()),
                first_signal=str(calendar.date.min().date()), last_signal=str(calendar.date.max().date()),
                source_sha256=sha(source), input_scope='supplied processed weekly data',
                target_check='every row: ln(daily adjusted close on label_end_date / weekly adjusted close); adjacent weekly closes also checked',
                target_reference=str(DAILY_PRICES.relative_to(ROOT)).replace('\\', '/'),
                target_reference_sha256=sha(DAILY_PRICES),
                external_data_used=False)
    write_json(destination / 'data_audit.json', info)
    return info
