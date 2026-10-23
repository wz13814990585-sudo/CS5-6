"""Independent cash/share accounting, metrics and supplied-script reconciliation."""
from pathlib import Path
import json,importlib.util
import numpy as np
import pandas as pd
from integer_backtest import execute,performance,MODELS

HERE=Path(__file__).resolve().parent;OUT=HERE/'results'
checks=0;maximum=0.
def eq(a,b,label,atol=1e-7):
    global checks,maximum
    a=np.asarray(a,float);b=np.asarray(b,float)
    assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b)),label
    mask=np.isfinite(a)&np.isfinite(b);err=float(abs(a[mask]-b[mask]).max()) if mask.any() else 0.
    assert err<atol,(label,err)
    maximum=max(maximum,err);checks+=a.size

def synthetic():
    d=pd.Timestamp('2026-01-02');p=pd.DataFrame([dict(ticker='A',prediction=1.)]);ctx=dict(open={d:{'A':300.}},close={d:{'A':300.}})
    w,orders,pos=execute([d],{d:p},ctx,'UniverseEqualWeight',2000.,0,detail=True)
    assert int(pos.shares.iloc[0])==6;eq(w.cash.iloc[0],200.,'2000/300 remainder')
    w,orders,pos=execute([d],{d:p},ctx,'UniverseEqualWeight',2000.,10,detail=True)
    assert int(pos.shares.iloc[0])==6;eq(w.cash.iloc[0],198.20,'fee reserved');eq(w.end_capital.iloc[0],1996.40,'both fees')
    ctx['open'][d]['A']=3000.;ctx['close'][d]['A']=3000.
    w,_,pos=execute([d],{d:p},ctx,'UniverseEqualWeight',2000.,10,detail=True);assert not len(pos);eq(w.end_capital.iloc[0],2000.,'unaffordable stock')
    ds=[d,d+pd.Timedelta(weeks=1)];pool=pd.DataFrame([dict(ticker=t,prediction=5-i) for i,t in enumerate('ABCDE')])
    ctx=dict(open={ds[0]:dict.fromkeys('ABCDE',100.),ds[1]:dict.fromkeys('ABCDE',150.)},close={ds[0]:dict.fromkeys('ABCDE',110.),ds[1]:dict.fromkeys('ABCDE',160.)})
    w,orders,pos=execute(ds,dict.fromkeys(ds,pool),ctx,'Top5_Rebalance2w',10000.,0,detail=True)
    eq(w.end_capital.to_numpy(),[11000.,16000.],'2-week shares held through overnight gap')
    assert not len(orders[(orders.date==ds[1])&(orders.timing=='OPEN')])
    x=pd.DataFrame(dict(date=[d],end_capital=[9000.],net_return=[-.1],fees=[0.],cash_ratio=[0.],holdings=[1],traded_fraction=[1.],cash_sizing_cuts=[0]))
    eq(performance(x,10000.)['max_drawdown'],-.1,'drawdown includes initial capital')

def main():
    global checks
    synthetic()
    w=pd.read_csv(OUT/'weekly_nav.csv.gz',parse_dates=['date'],float_precision='round_trip')
    ledger=pd.read_csv(OUT/'trade_ledger_10bps.csv.gz',parse_dates=['date'],float_precision='round_trip')
    pos=pd.read_csv(OUT/'holdings_10bps.csv.gz',parse_dates=['date'],float_precision='round_trip')
    assert (ledger.shares>=1).all() and (ledger.shares==np.floor(ledger.shares)).all()
    assert (pos.shares>=1).all() and (pos.shares==np.floor(pos.shares)).all();checks+=len(ledger)+len(pos)
    eq(ledger.amount,ledger.shares*ledger.price,'trade amount');eq(ledger.fee,ledger.amount*.001,'trade fees')
    assert ledger.cash_after.min()>-1e-7
    keys=['model','window','strategy','capital','cost_bps']
    grouped={k:g.sort_values('date') for k,g in w.groupby(keys)}
    summary=pd.read_csv(OUT/'strategy_comparison.csv',float_precision='round_trip')
    for row in summary.itertuples():
        g=grouped[row.model,row.window,row.strategy,row.capital,row.cost_bps]
        nav=np.r_[row.capital,g.end_capital];r=g.net_return.to_numpy();vol=r.std(ddof=1)*np.sqrt(52)
        eq(g.start_capital.to_numpy(),nav[:-1],'starting capital path')
        eq(r,nav[1:]/nav[:-1]-1,'net weekly returns')
        stats=[nav[-1],nav[-1]/row.capital-1,(nav[-1]/row.capital)**(52/len(r))-1,(nav/np.maximum.accumulate(nav)-1).min(),vol,r.mean()*52/vol if vol>0 else np.nan,g.fees.sum()]
        eq([row.final_capital,row.total_return,row.annualized_return,row.max_drawdown,row.volatility,row.sharpe,row.total_fees],stats,'summary statistics')
    # Reconstruct all 10bps cash and integer holdings directly from trade orders.
    ordergroups={k:g for k,g in ledger.groupby(keys,sort=False)}
    posgroups={k:g for k,g in pos.groupby(keys,sort=False)}
    raw=pd.read_csv(HERE/'inputs/test40_with_prices.csv',parse_dates=['date'],float_precision='round_trip')
    prices={(r.date,r.ticker):(r.buy_price,r.sell_price) for r in raw.itertuples()}
    for key,g in grouped.items():
        if key[-1]!=10:continue
        cash=key[-2];shares={}
        tx={d:a for d,a in ordergroups.get(key,ledger.iloc[:0]).groupby('date',sort=False)}
        mark={d:a for d,a in posgroups.get(key,pos.iloc[:0]).groupby('date',sort=False)}
        for row in g.itertuples():
            trades=tx.get(row.date,ledger.iloc[:0]);before=cash+sum(q*prices[row.date,t][0] for t,q in shares.items())
            eq(before,row.opening_capital,'opening marked equity')
            buyfee=sellfee=0.
            for timing in ['OPEN','CLOSE']:
                if timing=='CLOSE':
                    eq(cash,row.cash,'cash before close');p=mark.get(row.date,pos.iloc[:0]);expected=dict(zip(p.ticker,p.shares))
                    assert shares==expected,(key,row.date,'shares mismatch');checks+=len(shares)
                for trade in trades[trades.timing.eq(timing)].itertuples():
                    eq(trade.price,prices[row.date,trade.ticker][0 if timing=='OPEN' else 1],'execution price source')
                    if trade.side=='BUY':
                        cash-=trade.shares*trade.price*(1.001);shares[trade.ticker]=shares.get(trade.ticker,0)+int(trade.shares);buyfee+=trade.fee
                        assert trade.requested_shares>=shares[trade.ticker]
                        # Fixed target budget includes buy-side fee; residual cash is never redistributed.
                        target=int(np.floor(trade.target_weight*before/(trade.price*1.001)))
                        assert trade.requested_shares==target
                    else:
                        assert shares.get(trade.ticker,0)>=trade.shares
                        cash+=trade.shares*trade.price*(.999);shares[trade.ticker]-=int(trade.shares);sellfee+=trade.fee
                        if not shares[trade.ticker]:shares.pop(trade.ticker)
                    eq(cash,trade.cash_after,'cash ledger')
            eq([cash+sum(q*prices[row.date,t][1] for t,q in shares.items()),buyfee,sellfee],[row.end_capital,row.buy_fees,row.sell_fees],'closing equity and fees')
        assert not shares
    # Twelve references: both frozen prediction paths against the supplied
    # weekly-close integer prototype (two capitals and three fees each).
    spec=importlib.util.spec_from_file_location('reference',HERE/'source/run_saved_model_simulation.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for model,path in MODELS.items():
        predictions=pd.read_csv(HERE/'prepared'/path,parse_dates=['date'],float_precision='round_trip')
        for capital in [100000.,10000.]:
            for cost in [0,10,25]:
                mod.INITIAL_CAPITAL=capital;mod.FEE_RATE=cost/10000
                reference,trades=mod.simulate(predictions)
                calculated=grouped[model,'FullHistory','Top5_WeeklyRoundTrip',capital,cost]
                eq(reference.end_capital.to_numpy(),calculated.end_capital.to_numpy(),'supplied integer script reference',1e-6)
    # The version-label correction must not change any computed new-model case.
    prior_path=HERE/'prepared/new150_previous_summary.csv'
    if prior_path.exists():
        prior=pd.read_csv(prior_path,float_precision='round_trip')
        new=summary[summary.model.eq('Ranker150_New')].reset_index(drop=True)
        fields=['final_capital','annualized_return','sharpe','max_drawdown','total_fees']
        eq(new[fields],prior[fields],'new model unchanged after comparison update')
    # Identical benchmark inputs must give identical results for both labels.
    base=summary[summary.strategy.eq('UniverseEqualWeight')].pivot(index=['window','capital','cost_bps'],columns='model',values='final_capital')
    eq(base.Ranker150_New,base.Ranker50_Old,'same universe benchmark across models')
    phases=pd.read_csv(OUT/'phase_sensitivity.csv');zero=phases[phases.initial_delay_weeks.eq(0)].merge(summary,on=keys,suffixes=('_phase','_main'),validate='one_to_one')
    eq(zero.annualized_return_phase,zero.annualized_return_main,'phase zero')
    result=dict(status='passed',checks=checks,maximum_absolute_error=maximum,summary_cases=len(summary),trade_orders_checked=len(ledger),holdings_checked=len(pos),supplied_script_reference_cases=12,integer_example='2000 budget / 300 price = 6 shares; 200 cash before fees',cash_nonnegative=True,all_windows_start_fresh=True,both_models_evaluated=True)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2))
    mf=OUT/'run_manifest.json';m=json.loads(mf.read_text());m['status']='both_models_completed_verified';m['independent_checks']=checks;mf.write_text(json.dumps(m,indent=2))
    print(result)

if __name__=='__main__':main()
