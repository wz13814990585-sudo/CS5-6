"""Integer-share execution at next-open proxies, marked at next-close proxies."""
from pathlib import Path
import json,math,gzip,csv,hashlib
import pandas as pd
import numpy as np

HERE=Path(__file__).resolve().parent;OUT=HERE/'results';OUT.mkdir(exist_ok=True)
STRATEGIES=['Top5','Top10','Top5_PositiveScore','Top10_PositiveScore','Top5_NoLoss4w','Top10_NoLoss4w','Top5_NoLoss13w','Top10_NoLoss13w','Top5_RankWeighted','Top5_LowVol26w','Top5_RankRisk26w','Top5_Buffer10','Top5_Rebalance2w','Top5_Rebalance4w','Top5_Trend26w']
MODELS={'Ranker150_New':'predictions.csv','Ranker50_Old':'old50_predictions.csv'}
CAPITALS=[100000.,10000.];COSTS=[0,10,25]

def capweights(scores,budget,cap=.35):
    active=dict(scores);result={};remaining=min(budget,cap*len(active))
    while active:
        total=sum(active.values());proposed={t:remaining*v/total for t,v in active.items()}
        over=[t for t,v in proposed.items() if v>cap+1e-14]
        if not over:result.update(proposed);break
        for t in over:result[t]=cap;remaining-=cap;active.pop(t)
    return result

def prepare(prediction_file='predictions.csv'):
    raw=pd.read_csv(HERE/'inputs/test40_with_prices.csv',parse_dates=['date'],float_precision='round_trip').sort_values(['date','ticker'])
    p=pd.read_csv(HERE/'prepared'/prediction_file,parse_dates=['date'],float_precision='round_trip')
    assert not raw.duplicated(['date','ticker']).any() and not p.duplicated(['date','ticker']).any()
    assert np.isfinite(raw[['buy_price','sell_price']]).all().all() and raw[['buy_price','sell_price']].gt(0).all().all()
    opening=raw.pivot(index='date',columns='ticker',values='buy_price').sort_index()
    closing=raw.pivot(index='date',columns='ticker',values='sell_price').sort_index()
    # Each row's sell proxy is the following week's close. Shift one row to
    # obtain the close observable on the current signal date.
    observed=closing.shift(1)
    past=observed/observed.shift(1)-1
    vol=past.rolling(26,min_periods=26).std(ddof=1)
    lag={n:observed/observed.shift(n)-1 for n in [4,13]}
    index=(1+past.mean(axis=1).fillna(0)).cumprod()
    trend=(index>index.rolling(26,min_periods=26).mean()).fillna(False)
    context=dict(open={d:s.dropna().to_dict() for d,s in opening.iterrows()},close={d:s.dropna().to_dict() for d,s in closing.iterrows()},
                 observed={d:s.dropna().to_dict() for d,s in observed.iterrows()},vol={d:s.dropna().to_dict() for d,s in vol.iterrows()},
                 lag={n:{d:s.dropna().to_dict() for d,s in frame.iterrows()} for n,frame in lag.items()},trend=trend.to_dict())
    groups={d:g.sort_values(['prediction','ticker'],ascending=[False,True],kind='stable') for d,g in p.groupby('date')}
    calendar=[d for d in opening.index if p.date.min()<=d<=p.date.max()]
    return raw,p,groups,calendar,context

def windows(calendar):
    result={'FullHistory':calendar}
    for n in [13,26,52,104,156]:
        if len(calendar)>=n:result[f'Last{n}w']=calendar[-n:]
    for year in sorted({d.year for d in calendar}):result[f'Year{year}']=[d for d in calendar if d.year==year]
    for name,start,end in [('Development','2022-09-02','2024-08-30'),('Validation','2024-09-06','2025-08-29'),('FinalTest','2025-09-05','2026-08-21')]:
        result[name]=[d for d in calendar if pd.Timestamp(start)<=d<=pd.Timestamp(end)]
    return {k:v for k,v in result.items() if v}

def target_weights(strategy,g,held,date,context):
    names=list(g.ticker);k=10 if strategy.startswith('Top10') else 5
    if strategy=='UniverseEqualWeight':return dict.fromkeys(names,1/len(names)) if names else {}
    if 'PositiveScore' in strategy:names=list(g[g.prediction>0].ticker)
    if 'NoLoss' in strategy:
        n=4 if '4w' in strategy else 13
        names=[t for t in names if context['lag'][n][date].get(t,-np.inf)>=0]
    if strategy=='Top5_Trend26w' and not context['trend'][date]:return {}
    if strategy=='Top5_Buffer10':
        keep=[t for t in names[:10] if held.get(t,0)>0]
        names=keep+[t for t in names if t not in keep][:k-len(keep)]
    if strategy in ['Top5_LowVol26w','Top5_RankRisk26w']:
        names=[t for t in names if t in context['vol'][date]][:5]
        scores={t:(5-i if strategy=='Top5_RankRisk26w' else 1)/max(context['vol'][date][t],1e-8) for i,t in enumerate(names)}
        return capweights(scores,len(names)/5)
    names=names[:k]
    if strategy=='Top5_RankWeighted':return {t:(5-i)/15 for i,t in enumerate(names)}
    return dict.fromkeys(names,1/k)

def execute(dates,groups,context,strategy,initial,cost,phase=0,detail=False):
    fee=cost/10000;cash=float(initial);held={};last=None;prior_nav=float(initial)
    weekly=[];ledger=[];holdings=[]
    roundtrip=strategy=='Top5_WeeklyRoundTrip'
    for i,date in enumerate(dates):
        op=context['open'][date];cl=context['close'][date];g=groups.get(date,pd.DataFrame(columns=['ticker','prediction']))
        assert all(t in op and t in cl for t in held),('missing held stock prices',date,held)
        open_equity=cash+sum(q*op[t] for t,q in held.items())
        start_cash=cash;old=dict(held);orders=[];buy_fee=sell_fee=buy_amount=sell_amount=0.;sizing_cuts=0
        period=2 if strategy=='Top5_Rebalance2w' else 4 if strategy=='Top5_Rebalance4w' else 1
        rebalance=(period==1 or last is None or i-last>=period or not held)
        if i<phase:rebalance=True;weights={}
        elif not len(g):rebalance=True;weights={};last=None
        elif rebalance:
            weights=target_weights('Top5' if roundtrip else strategy,g,held,date,context);last=i
        else:weights=None
        requested={}
        def order(t,side,qty,price,timing,reason,weight=0.,planned=0):
            nonlocal cash,buy_fee,sell_fee,buy_amount,sell_amount
            amount=qty*price;charge=amount*fee
            if side=='BUY':cash-=amount+charge;held[t]=held.get(t,0)+qty;buy_fee+=charge;buy_amount+=amount
            else:
                cash+=amount-charge;held[t]-=qty;sell_fee+=charge;sell_amount+=amount
                if held[t]==0:held.pop(t)
            orders.append(dict(date=date,ticker=t,side=side,timing=timing,reason=reason,shares=int(qty),price=price,amount=amount,fee=charge,cash_after=cash,target_weight=weight,requested_shares=int(planned)))
            assert cash>=-1e-7,(date,cash)
        if rebalance:
            # Each target allocation reserves the BUY fee. Sells execute first;
            # any residual cash constraint truncates buys in fixed rank order.
            requested={t:int(math.floor(weights[t]*open_equity/(op[t]*(1+fee)))) for t in weights}
            for t in sorted(old):
                qty=max(0,old[t]-requested.get(t,0))
                if qty:order(t,'SELL',qty,op[t],'OPEN','rebalance',weights.get(t,0),requested.get(t,0))
            for t in weights:
                need=max(0,requested[t]-held.get(t,0))
                affordable=max(0,int(math.floor(max(cash,0)/(op[t]*(1+fee)))))
                quantity=min(need,affordable)
                if quantity<need:sizing_cuts+=1
                if quantity:order(t,'BUY',quantity,op[t],'OPEN','rebalance',weights[t],requested[t])
        endcash_before_close=cash;mark_positions=dict(held)
        mark_value=cash+sum(q*cl[t] for t,q in held.items())
        if roundtrip or i==len(dates)-1:
            for t in sorted(list(held)):order(t,'SELL',held[t],cl[t],'CLOSE','weekly_roundtrip' if roundtrip else 'window_end')
        end_nav=cash+sum(q*cl[t] for t,q in held.items())
        weekly.append(dict(date=date,start_capital=prior_nav,opening_capital=open_equity,end_capital=end_nav,cash=endcash_before_close,
            cash_ratio=endcash_before_close/mark_value if mark_value else 1.,net_return=end_nav/prior_nav-1,
            buy_amount=buy_amount,sell_amount=sell_amount,buy_fees=buy_fee,sell_fees=sell_fee,fees=buy_fee+sell_fee,
            traded_fraction=(buy_amount+sell_amount)/open_equity,holdings=len(mark_positions),shares=sum(mark_positions.values()),
            rebalance=rebalance,forced_window_liquidation=i==len(dates)-1,cash_sizing_cuts=sizing_cuts,signal_missing=not len(g),
            opening_cash=start_cash,post_execution_cash=cash))
        if detail:
            ledger.extend(orders)
            for t,q in mark_positions.items():holdings.append(dict(date=date,ticker=t,shares=int(q),buy_proxy=op[t],close_proxy=cl[t],market_value=q*cl[t],target_weight=weights.get(t,np.nan) if weights is not None else np.nan,requested_shares=requested.get(t,np.nan),opening_capital=open_equity))
        prior_nav=end_nav
    return pd.DataFrame(weekly),pd.DataFrame(ledger),pd.DataFrame(holdings)

def performance(w,initial):
    r=w.net_return.to_numpy();nav=np.r_[initial,w.end_capital.to_numpy()];drawdown=nav/np.maximum.accumulate(nav)-1
    vol=np.std(r,ddof=1)*np.sqrt(52) if len(r)>1 else np.nan
    return dict(weeks=len(w),first_signal=w.date.min(),last_signal=w.date.max(),initial_capital=initial,final_capital=nav[-1],
        total_return=nav[-1]/initial-1,annualized_return=np.expm1(np.log(nav[-1]/initial)*52/len(r)),
        volatility=vol,sharpe=np.mean(r)*52/vol if vol>0 else np.nan,max_drawdown=drawdown.min(),
        win_rate=np.mean(r>0),total_fees=w.fees.sum(),fees_to_initial=w.fees.sum()/initial,
        mean_cash_ratio=w.cash_ratio.mean(),mean_holdings=w.holdings.mean(),mean_traded_fraction=w.traded_fraction.mean(),
        cash_sizing_cuts=int(w.cash_sizing_cuts.sum()))

def simulate_model(model,prediction_file):
    raw,p,groups,calendar,context=prepare(prediction_file);summaries=[];weeklies=[];orders=[];holdings=[];phase_rows=[]
    for window,dates in windows(calendar).items():
        for capital in CAPITALS:
            for cost in COSTS:
                for strategy in STRATEGIES+['UniverseEqualWeight','Top5_WeeklyRoundTrip']:
                    detailed=cost==10
                    w,ledger,pos=execute(dates,groups,context,strategy,capital,cost,detail=detailed)
                    meta=dict(model=model,window=window,strategy=strategy,capital=capital,cost_bps=cost)
                    summaries.append(dict(**meta,**performance(w,capital)))
                    weeklies.append(w.assign(**meta))
                    if detailed:
                        if len(ledger):orders.append(ledger.assign(**meta))
                        if len(pos):holdings.append(pos.assign(**meta))
            if window in ['FullHistory','Validation','FinalTest']:
                for strategy,period in [('Top5_Rebalance2w',2),('Top5_Rebalance4w',4)]:
                    for phase in range(period):
                        for cost in COSTS:
                            w,_,_=execute(dates,groups,context,strategy,capital,cost,phase=phase)
                            phase_rows.append(dict(model=model,window=window,strategy=strategy,capital=capital,cost_bps=cost,initial_delay_weeks=phase,**performance(w,capital)))
        print('Integer-share window complete',model,window,len(dates),flush=True)
    coverage=dict(model=model,input_rows=len(p),weeks=p.date.nunique(),first_signal=str(p.date.min().date()),last_signal=str(p.date.max().date()),stocks=p.ticker.nunique())
    return pd.DataFrame(summaries),pd.concat(weeklies,ignore_index=True),pd.concat(orders,ignore_index=True),pd.concat(holdings,ignore_index=True),pd.DataFrame(phase_rows),coverage

def main():
    runs=[simulate_model(model,path) for model,path in MODELS.items()]
    summary,weekly,orders,holdings,phases=[pd.concat([r[i] for r in runs],ignore_index=True) for i in range(5)]
    summary.to_csv(OUT/'strategy_comparison.csv',index=False,float_format='%.17g')
    weekly.to_csv(OUT/'weekly_nav.csv.gz',index=False,compression='gzip',float_format='%.17g')
    orders.to_csv(OUT/'trade_ledger_10bps.csv.gz',index=False,compression='gzip',float_format='%.17g')
    holdings.to_csv(OUT/'holdings_10bps.csv.gz',index=False,compression='gzip',float_format='%.17g')
    phases.to_csv(OUT/'phase_sensitivity.csv',index=False,float_format='%.17g')
    coverage=[r[5] for r in runs]
    (OUT/'coverage.json').write_text(json.dumps(coverage,indent=2))
    manifest=dict(status='computed_pending_verification',models_available=list(MODELS),version_mapping={'Ranker150_New':'new supplied saved model, candidate2, 150 trees','Ranker50_Old':'previous frozen predictions from standalone handoff, candidate1, 50 trees'},case_count=len(summary),main_strategies=15,extra_comparators=['UniverseEqualWeight','Top5_WeeklyRoundTrip'],window_count=summary.window.nunique(),capital=CAPITALS,cost_bps=COSTS,integer_shares=True,
        price_source='next-week open/close proxies supplied in test40_with_prices.csv',hold_overnight=True,window_end_liquidation=True,currency='same units as quoted prices; no FX conversion; not labelled AUD',risk_free_rate=0,stock_cap_on_risk_weights=.35,
        selection_features='historical filters use prior rows sell_price shifted to signal date; no future target1',zero_fractional_shares=True,all_costs_resimulated=True,summary_sha256=hashlib.sha256((OUT/'strategy_comparison.csv').read_bytes()).hexdigest())
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
