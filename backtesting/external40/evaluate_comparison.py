"""Paired version deltas and label-based prediction quality; no new selection."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from integer_backtest import MODELS,prepare,windows

HERE=Path(__file__).resolve().parent;OUT=HERE/'results'
def main():
    s=pd.read_csv(OUT/'strategy_comparison.csv',float_precision='round_trip')
    keys=['window','strategy','capital','cost_bps']
    pair=s[s.model.eq('Ranker150_New')].merge(s[s.model.eq('Ranker50_Old')],on=keys,validate='one_to_one',suffixes=('_new','_old'))
    for metric in ['annualized_return','sharpe','max_drawdown','final_capital','total_fees']:
        pair[metric+'_new_minus_old']=pair[metric+'_new']-pair[metric+'_old']
    pair.to_csv(OUT/'new_vs_old_comparison.csv',index=False,float_format='%.17g')
    weeklies=[];summaries=[]
    for model,path in MODELS.items():
        _,pred,_,calendar,_=prepare(path)
        records=[]
        for date,g in pred.groupby('date'):
            actual=g.target1.rank(method='average')
            ric=g.prediction.rank(method='average').corr(actual)
            picks=g.sort_values(['prediction','ticker'],ascending=[False,True]).head(5)
            label_simple=np.expm1(picks.target1)
            relevance=np.floor((actual-1)*5/len(g)).clip(0,4)
            gains=pd.Series(np.exp2(relevance)-1,index=g.index)
            ideal=np.sort(gains)[::-1][:5]
            discount=np.log2(np.arange(2,7))
            ndcg=float(np.sum(gains.loc[picks.index].to_numpy()/discount)/np.sum(ideal/discount))
            records.append(dict(model=model,date=date,stocks=len(g),rank_ic=ric,ndcg_at5=ndcg,top5_label_return=float(label_simple.mean()),pool_label_return=float(np.expm1(g.target1).mean()),top5_positive_label_fraction=float((picks.target1>0).mean())))
        frame=pd.DataFrame(records);weeklies.append(frame)
        for window,dates in windows(calendar).items():
            g=frame[frame.date.isin(dates)];r=g.rank_ic.dropna()
            summaries.append(dict(model=model,window=window,weeks=len(g),rank_ic_valid_weeks=len(r),mean_rank_ic=r.mean(),rank_icir=r.mean()/r.std(ddof=1) if r.std(ddof=1)>0 else np.nan,positive_rank_ic_fraction=(r>0).mean(),mean_ndcg_at5=g.ndcg_at5.mean(),mean_top5_label_return=g.top5_label_return.mean(),mean_pool_label_return=g.pool_label_return.mean(),mean_top5_label_excess=(g.top5_label_return-g.pool_label_return).mean(),top5_positive_label_fraction=g.top5_positive_label_fraction.mean()))
    pd.concat(weeklies,ignore_index=True).to_csv(OUT/'prediction_evaluation_weekly.csv',index=False,float_format='%.17g')
    result=pd.DataFrame(summaries);result.to_csv(OUT/'prediction_evaluation.csv',index=False,float_format='%.17g')
    notes=dict(label='target1: supplied next-week close-to-close log-return label; expm1 for simple returns',rank_ic='Spearman correlation within each signal week; mean over valid weeks',rank_icir='mean weekly Rank IC / sample standard deviation; NOT annualized',ndcg_at5='weekly relevance=floor((target rank - 1)*5/N), clipped 0..4; gain=2^relevance-1; log2 discounts; ties average',portfolio_pnl='uses supplied buy/sell price proxies and integer shares; NOT target1',delta='new minus old; less negative max_drawdown means smaller observed drawdown')
    (OUT/'prediction_metric_definitions.json').write_text(json.dumps(notes,indent=2))
    print(result[result.window.isin(['FullHistory','FinalTest'])].to_string(index=False))
if __name__=='__main__':main()
