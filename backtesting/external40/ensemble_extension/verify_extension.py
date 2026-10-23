"""Independent vector cash/share reconciliation for every added 10bps order."""
from pathlib import Path
import gc,importlib.util,json,sys
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE));from verify_integer import synthetic
KEYS=['model','scope','window','strategy','capital','cost_bps']
checks=0;max_error=0.
def eq(a,b,label,atol=1e-6):
    global checks,max_error
    a=np.asarray(a,float);b=np.asarray(b,float)
    assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b)),label
    finite=np.isfinite(a)&np.isfinite(b)
    error=float(np.max(abs(a[finite]-b[finite]))) if finite.any() else 0.
    assert np.allclose(a,b,rtol=1e-11,atol=atol,equal_nan=True),(label,error)
    checks+=a.size;max_error=max(max_error,error)
def verify(directory,job):
    global checks
    before_checks=checks
    w=pd.read_csv(directory/'weekly_nav.csv.gz',parse_dates=['date'],float_precision='round_trip').sort_values(KEYS+['date'])
    s=pd.read_csv(directory/'strategy_comparison.csv',float_precision='round_trip')
    ledger=pd.read_csv(directory/'trade_ledger_10bps.csv.gz',parse_dates=['date'],float_precision='round_trip')
    p=pd.read_csv(directory/'holdings_10bps.csv.gz',parse_dates=['date'],float_precision='round_trip')
    for g in [ledger,p]:assert g.shares.gt(0).all() and g.shares.eq(np.floor(g.shares)).all();checks+=len(g)
    assert w.shares.eq(np.floor(w.shares)).all() and w.cash.min()>-1e-6
    eq(ledger.amount,ledger.shares*ledger.price,'integer trade amount');eq(ledger.fee,ledger.amount*.001,'10bps both sides')
    groups={key:g for key,g in w.groupby(KEYS,sort=False)}
    for row in s.itertuples():
        key=tuple(getattr(row,k) for k in KEYS);g=groups[key];nav=np.r_[row.capital,g.end_capital];r=nav[1:]/nav[:-1]-1;vol=r.std(ddof=1)*np.sqrt(52)
        eq(g.start_capital,nav[:-1],'capital path');eq(g.net_return,r,'returns')
        stats=[nav[-1],nav[-1]/row.capital-1,(nav[-1]/row.capital)**(52/len(r))-1,vol,r.mean()*52/vol if vol>0 else np.nan,(nav/np.maximum.accumulate(nav)-1).min(),g.fees.sum()]
        eq([row.final_capital,row.total_return,row.annualized_return,row.volatility,row.sharpe,row.max_drawdown,row.total_fees],stats,'all case metrics')
    l=ledger.copy();l['flow']=np.where(l.side.eq('BUY'),-l.amount-l.fee,l.amount-l.fee)
    eq(l.groupby(KEYS,sort=False).flow.cumsum()+l.capital,l.cash_after,'all chronological cash balances')
    assert l.cash_after.min()>-1e-6
    l['delta']=np.where(l.side.eq('BUY'),l.shares,-l.shares)
    l['close_sold']=np.where(l.timing.eq('CLOSE'),l.shares,0)
    l['open_delta']=np.where(l.timing.eq('OPEN'),l.delta,0)
    index=KEYS+['date','ticker'];stock_keys=KEYS+['ticker']
    inventory=l.groupby(index,as_index=False,sort=False)[['delta','close_sold','open_delta']].sum().merge(p[index+['shares']],on=index,how='outer',validate='one_to_one').fillna({'delta':0,'close_sold':0,'open_delta':0,'shares':0}).sort_values(stock_keys+['date'])
    inventory['end_shares']=inventory.groupby(stock_keys,sort=False).delta.cumsum()
    inventory['preclose_shares']=inventory.end_shares+inventory.close_sold
    inventory['opening_shares']=inventory.preclose_shares-inventory.open_delta
    assert inventory[['end_shares','preclose_shares','opening_shares']].ge(0).all().all()
    assert inventory.groupby(stock_keys,sort=False).end_shares.last().eq(0).all()
    eq(inventory.preclose_shares,inventory.shares,'all saved integer holdings')
    raw=pd.read_csv(BASE/'inputs/test40_with_prices.csv',parse_dates=['date'],float_precision='round_trip')
    inventory=inventory.merge(raw[['date','ticker','buy_price','sell_price']],on=['date','ticker'],validate='many_to_one')
    inventory['opening_stock_value']=inventory.opening_shares*inventory.buy_price
    inventory['end_stock_value']=inventory.end_shares*inventory.sell_price
    inventory['mark_stock_value']=inventory.preclose_shares*inventory.sell_price
    values=inventory.groupby(KEYS+['date'],as_index=False)[['opening_stock_value','end_stock_value','mark_stock_value']].sum()
    detailed=w[w.cost_bps.eq(10)].copy()
    detailed['prior_cash']=detailed.groupby(KEYS,sort=False).post_execution_cash.shift().fillna(detailed.capital)
    flows=l.groupby(KEYS+['date'],as_index=False).flow.sum().rename(columns={'flow':'all_flow'})
    openflows=l[l.timing.eq('OPEN')].groupby(KEYS+['date'],as_index=False).flow.sum().rename(columns={'flow':'open_flow'})
    z=detailed.merge(values,on=KEYS+['date'],how='left',validate='one_to_one').merge(flows,on=KEYS+['date'],how='left',validate='one_to_one').merge(openflows,on=KEYS+['date'],how='left',validate='one_to_one')
    for col in ['opening_stock_value','end_stock_value','mark_stock_value','all_flow','open_flow']:z[col]=z[col].fillna(0)
    eq(z.prior_cash+z.open_flow,z.cash,'weekly cash before close')
    eq(z.prior_cash+z.all_flow,z.post_execution_cash,'weekly cash after close')
    eq(z.prior_cash+z.opening_stock_value,z.opening_capital,'opening equity from shares')
    eq(z.post_execution_cash+z.end_stock_value,z.end_capital,'closing equity from shares')
    eq(z.cash/(z.cash+z.mark_stock_value),z.cash_ratio,'cash ratio')
    bought=l[l.side.eq('BUY')].merge(detailed[KEYS+['date','opening_capital']],on=KEYS+['date'],validate='many_to_one')
    eq(np.floor(bought.target_weight*bought.opening_capital/(bought.price*1.001)),bought.requested_shares,'fee-reserved target shares')
    # Independent delivered round-trip implementation on each prediction path.
    spec=importlib.util.spec_from_file_location('prototype',BASE/'source/run_saved_model_simulation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    prediction=pd.read_csv(HERE/'prepared'/job['prediction_file'],parse_dates=['date'],float_precision='round_trip')
    for capital in [100000.,10000.]:
        for cost in [0,10,25]:
            m.INITIAL_CAPITAL=capital;m.FEE_RATE=cost/10000
            ref,_=m.simulate(prediction)
            g=groups[(job['model'],job['scope'],'FullHistory','Top5_WeeklyRoundTrip',capital,cost)]
            eq(ref.end_capital,g.end_capital,'supplied prototype reference')
    phase=pd.read_csv(directory/'phase_sensitivity.csv');zero=phase[phase.initial_delay_weeks.eq(0)].merge(s,on=KEYS,validate='one_to_one',suffixes=('_phase','_main'))
    eq(zero.final_capital_phase,zero.final_capital_main,'phase zero')
    result=dict(status='passed',cases=len(s),orders=len(l),holdings=len(p),weekly_rows=len(w),prototype_cases=6,checks=checks-before_checks,maximum_absolute_error=max_error)
    (directory/'verification.json').write_text(json.dumps(result,indent=2))
    f=directory/'run_manifest.json';manifest=json.loads(f.read_text());manifest['status']='verified';f.write_text(json.dumps(manifest,indent=2))
    print('Verified',directory.name,result,flush=True)
    return result
def main():
    synthetic();results=[]
    jobs=json.loads((HERE/'prepared/jobs.json').read_text())
    for job in jobs:
        directory=HERE/'runs'/f'{job["model"]}_{job["scope"]}'
        if not (directory/'run_manifest.json').exists():
            if '--ready-only' in sys.argv:continue
            raise RuntimeError(f'Backtest incomplete: {directory}')
        if (directory/'verification.json').exists() and json.loads((directory/'run_manifest.json').read_text())['status']=='verified':
            results.append(json.loads((directory/'verification.json').read_text()));continue
        results.append(verify(directory,job));gc.collect()
    summary=dict(status='passed' if len(results)==len(jobs) else 'partial',jobs_verified=len(results),jobs_expected=len(jobs),checks=sum(r['checks'] for r in results),maximum_absolute_error=max(r['maximum_absolute_error'] for r in results),added_cases=sum(r['cases'] for r in results),trade_orders=sum(r['orders'] for r in results),holdings=sum(r['holdings'] for r in results),prototype_cases=sum(r['prototype_cases'] for r in results),source_audit='prepared/source_audit.json')
    (HERE/'results/verification.json').write_text(json.dumps(summary,indent=2));print(summary)
if __name__=='__main__':main()
