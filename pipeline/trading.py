from __future__ import annotations

import math
import statistics

import numpy as np
import pandas as pd

from . import ROOT
from .contracts import load_module, require



ORDER_COLUMNS = ['date', 'ticker', 'side', 'timing', 'reason', 'shares', 'price', 'amount',
                 'fee', 'cash_after', 'target_weight', 'requested_shares']
HOLDING_COLUMNS = ['date', 'ticker', 'shares', 'buy_proxy', 'close_proxy', 'market_value',
                   'target_weight', 'requested_shares', 'opening_capital']
# Strategies whose weekly targets are rebuilt here from ranks and prices.
SIZED_STRATEGIES = ['Top5', 'Top10', 'Top5_RankWeighted', 'Top5_NoLoss13w']


def _ledger(frame, columns, name):
    """Accept an empty ledger without columns (all-cash run); otherwise require the schema."""
    if frame.empty and not set(columns) <= set(frame.columns):
        return pd.DataFrame(columns=columns)
    require(set(columns) <= set(frame.columns), f'{name} table is missing columns')
    return frame


def _expected_open_orders(cash, held, targets, quote, date, cost):
    """Rebuild the OPEN orders implied by target weights.

    Mirrors the documented rule: requested = floor(weight * opening equity /
    (open * (1 + fee))); sell down to the request in ticker order, then buy in
    rank order, truncated only when cash cannot fund another share.
    Returns [(ticker, side, shares)] and the requested shares per target.
    """
    held = dict(held)
    equity = cash + math.fsum(q * quote[(date, t)][0] for t, q in held.items())
    requested = {t: math.floor(w * equity / (quote[(date, t)][0] * (1 + cost))) for t, w in targets}
    expected = []
    for ticker in sorted(held):
        qty = max(0, held[ticker] - requested.get(ticker, 0))
        if qty:
            amount = qty * quote[(date, ticker)][0]
            cash += amount - amount * cost
            held[ticker] -= qty
            expected.append((ticker, 'SELL', qty))
    for ticker, _ in targets:
        price = quote[(date, ticker)][0]
        need = max(0, requested[ticker] - held.get(ticker, 0))
        affordable = max(0, int(math.floor(max(cash, 0) / (price * (1 + cost)))))
        qty = min(need, affordable)
        if qty:
            amount = qty * price
            cash -= amount + amount * cost
            held[ticker] = held.get(ticker, 0) + qty
            expected.append((ticker, 'BUY', qty))
    return expected, requested


def implementation():
    return load_module('repro_integer_engine', ROOT / 'backtesting/external40/integer_backtest.py')




def independent_case(summary, weekly, orders, holdings, prices, predictions, *, quote_lookup=None, rank_lookup=None):
    """Rebuild an account using order cashflows; do not invoke execute/performance."""
    orders = _ledger(orders, ORDER_COLUMNS, 'Orders')
    holdings = _ledger(holdings, HOLDING_COLUMNS, 'Holdings')
    initial = float(summary.capital)
    cost = float(summary.cost_bps) / 10000
    cash, prior, peak = initial, initial, initial
    held = {}
    returns, fees, navs = [], [], []
    maximum_error = 0.
    checks = 0
    def near(actual, expected, label):
        nonlocal maximum_error, checks
        error = abs(float(actual) - float(expected))
        maximum_error = max(maximum_error, error)
        require(error <= 1e-7 + 1e-10 * abs(float(expected)), f'{label}: actual={actual}, expected={expected}')
        checks += 1
    quote = quote_lookup if quote_lookup is not None else {
        (r.date, r.ticker): (float(r.buy_price), float(r.sell_price)) for r in prices.itertuples(index=False)}
    ranks = rank_lookup if rank_lookup is not None else {
        d: list(g.sort_values(['prediction', 'ticker'], ascending=[False, True], kind='stable').ticker)
        for d, g in predictions.groupby('date')}
    lag13 = None
    if summary.strategy == 'Top5_NoLoss13w':
        closes = prices.pivot(index='date', columns='ticker', values='sell_price').sort_index()
        observed = closes.shift(1)
        trailing = observed / observed.shift(13) - 1
        lag13 = {d: row.dropna().to_dict() for d, row in trailing.iterrows()}
    order_groups = {d: g for d, g in orders.groupby('date', sort=False)}
    holding_groups = {d: g for d, g in holdings.groupby('date', sort=False)}
    require(set(orders.date) <= set(weekly.date), 'Orders outside weekly account')
    require(set(holdings.date) <= set(weekly.date), 'Holdings outside weekly account')
    for row in weekly.sort_values('date').itertuples(index=False):
        date = row.date
        near(row.opening_cash, cash, 'opening cash')
        near(row.start_capital, prior, 'prior NAV')
        equity = cash + math.fsum(q * quote[(date, ticker)][0] for ticker, q in held.items())
        near(row.opening_capital, equity, 'opening equity')
        day = order_groups.get(date, orders.iloc[:0])
        day_fees = 0.
        def apply(order):
            nonlocal cash, day_fees
            qty = int(order.shares)
            require(qty == order.shares and qty > 0, 'Noninteger or nonpositive order')
            expected_price = quote[(date, order.ticker)][0 if order.timing == 'OPEN' else 1]
            near(order.price, expected_price, 'execution quote')
            amount = qty * expected_price
            fee = amount * cost
            near(order.amount, amount, 'trade amount')
            near(order.fee, fee, 'trade fee')
            if order.side == 'BUY':
                cash -= amount + fee
                held[order.ticker] = held.get(order.ticker, 0) + qty
            else:
                require(order.side == 'SELL' and held.get(order.ticker, 0) >= qty, 'Invalid sell/short position')
                cash += amount - fee
                held[order.ticker] -= qty
                if not held[order.ticker]:
                    del held[order.ticker]
            require(cash >= -1e-7, 'Negative cash')
            near(order.cash_after, cash, 'order cash balance')
            day_fees += fee
        require(day.timing.isin(['OPEN', 'CLOSE']).all(), 'Unknown execution timing')
        open_orders = day[day.timing.eq('OPEN')]
        expected_requests = None
        if summary.strategy in SIZED_STRATEGIES:
            count = 10 if summary.strategy == 'Top10' else 5
            names = ranks.get(date, [])
            if summary.strategy == 'Top5_NoLoss13w':
                names = [t for t in names if lag13[date].get(t, -math.inf) >= 0]
            names = names[:count]
            targets = [(t, (5 - i) / 15 if summary.strategy == 'Top5_RankWeighted' else 1 / count)
                       for i, t in enumerate(names)]
            expected_orders, expected_requests = _expected_open_orders(cash, held, targets, quote, date, cost)
            actual_orders = [(o.ticker, o.side, o.shares) for o in open_orders.itertuples(index=False)]
        for order in open_orders.itertuples(index=False):
            apply(order)
        position = holding_groups.get(date, holdings.iloc[:0])
        require(not position.ticker.duplicated().any(), 'Duplicate holding')
        observed = dict(zip(position.ticker, position.shares))
        require(observed == held, f'Holdings disagree with reconstructed shares on {date}')
        for item in position.itertuples(index=False):
            near(item.market_value, held[item.ticker] * quote[(date, item.ticker)][1], 'position mark')
        if summary.strategy in ['Top5', 'Top10', 'Top5_RankWeighted', 'Top5_NoLoss13w']:
            count = 10 if summary.strategy == 'Top10' else 5
            expected_names = ranks.get(date, [])
            if summary.strategy == 'Top5_NoLoss13w':
                expected_names = [
                    ticker for ticker in expected_names
                    if lag13[date].get(ticker, -math.inf) >= 0
                ]
            expected_names = expected_names[:count]
            require(set(held) <= set(expected_names), 'Selection includes a stock outside the predicted ranks or trailing 13-week loss filter')
            positive_targets = set()
            for ticker in expected_names:
                weight = (5 - expected_names.index(ticker)) / 15 if summary.strategy == 'Top5_RankWeighted' else 1 / count
                expected_request = math.floor(weight * equity / (quote[(date, ticker)][0] * (1 + cost)))
                if expected_request > 0:
                    positive_targets.add(ticker)
            if summary.strategy == 'Top5_NoLoss13w':
                require(set(held) == positive_targets, 'Filtered Top5 holdings do not match independently selected names')
            for item in position.itertuples(index=False):
                weight = (5 - expected_names.index(item.ticker)) / 15 if summary.strategy == 'Top5_RankWeighted' else 1 / count
                expected_request = math.floor(weight * equity / (quote[(date, item.ticker)][0] * (1 + cost)))
                near(item.requested_shares, expected_request, 'independent target share sizing')
                require(item.shares <= expected_request, 'Held shares exceed target')
        if expected_requests is not None:
            require(actual_orders == expected_orders,
                    f'Open orders on {date} do not match independently rebuilt target positions '
                    f'(partial, excess or missing trades): actual={actual_orders}, expected={expected_orders}')
            for ticker, request in expected_requests.items():
                shares = held.get(ticker, 0)
                if shares != request:
                    one_more = quote[(date, ticker)][0] * (1 + cost)
                    require(shares < request and cash < one_more,
                            f'{ticker} on {date}: holds {shares} of {request} target shares while cash {cash:.2f} '
                            f'could fund more')
        marked_nav = cash + math.fsum(q * quote[(date, ticker)][1] for ticker, q in held.items())
        near(row.cash, cash, 'post-open cash')
        near(row.cash_ratio, cash / marked_nav if marked_nav else 1., 'cash ratio')
        near(row.shares, sum(held.values()), 'marked share total')
        near(row.holdings, len(held), 'holding count')
        for order in day[day.timing.eq('CLOSE')].itertuples(index=False):
            apply(order)
        final_nav = cash + math.fsum(q * quote[(date, ticker)][1] for ticker, q in held.items())
        near(row.end_capital, final_nav, 'end NAV')
        near(row.post_execution_cash, cash, 'post-close cash')
        near(row.net_return, final_nav / prior - 1, 'weekly return')
        near(row.fees, day_fees, 'weekly fees')
        returns.append(final_nav / prior - 1)
        fees.append(day_fees)
        navs.append(final_nav)
        prior = final_nav
    require(not held, 'Final holdings were not liquidated')
    require(len(weekly) == summary.weeks, 'Summary week count')
    near(summary.final_capital, prior, 'summary final capital')
    near(summary.total_return, prior / initial - 1, 'summary return')
    near(summary.annualized_return, (prior / initial) ** (52 / len(returns)) - 1, 'annualization')
    near(summary.total_fees, math.fsum(fees), 'summary fees')
    drawdown = 0.
    for nav in navs:
        peak = max(peak, nav)
        drawdown = min(drawdown, nav / peak - 1)
    near(summary.max_drawdown, drawdown, 'drawdown including initial capital')
    near(summary.win_rate, sum(r > 0 for r in returns) / len(returns), 'win rate')
    if len(returns) > 1:
        vol = statistics.stdev(returns) * math.sqrt(52)
        near(summary.volatility, vol, 'volatility')
        if vol > 0:
            near(summary.sharpe, statistics.mean(returns) * 52 / vol, 'Sharpe')
    return {'checks': checks, 'maximum_absolute_error': maximum_error, 'orders': len(orders), 'holdings': len(holdings)}




