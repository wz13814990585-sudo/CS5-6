"""Collect common-period and full-history results without mixing horizons."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=HERE/'results'
sys.path.insert(0,str(BASE));from integer_backtest import windows
LABELS={'Ensemble':'Ensemble等权集成','Model1':'子模型1_156周五因子','Model2':'子模型2_52周两因子','Model3':'子模型3_52周五因子','Ranker150_New':'独立新版150树','Ranker50_Old':'独立旧版50树'}
def save(frame,name):frame.to_csv(OUT/name,index=False,float_format='%.17g',compression='gzip' if name.endswith('.gz') else None)
def main():
    summaries=[pd.read_csv(BASE/'results/strategy_comparison.csv',float_precision='round_trip').assign(scope='Common210')]
    phase=[pd.read_csv(BASE/'results/phase_sensitivity.csv').assign(scope='Common210')]
    weeklycols=['date','model','window','strategy','capital','cost_bps','end_capital','net_return','cash_ratio','holdings','shares','fees']
    def chart_rows(path,scope):
        z=pd.read_csv(path,parse_dates=['date'],usecols=weeklycols,float_precision='round_trip')
        return z[z.capital.eq(100000)&z.cost_bps.eq(10)].assign(scope=scope)
    plots=[chart_rows(BASE/'results/weekly_nav.csv.gz','Common210')]
    pred_summaries=[pd.read_csv(BASE/'results/prediction_evaluation.csv').assign(scope='Common210')]
    pred_weekly=[pd.read_csv(BASE/'results/prediction_evaluation_weekly.csv',parse_dates=['date']).assign(scope='Common210')]
    jobs=json.loads((HERE/'prepared/jobs.json').read_text())
    coverage=[]
    for job in jobs:
        directory=HERE/'runs'/f'{job["model"]}_{job["scope"]}'
        assert json.loads((directory/'verification.json').read_text())['status']=='passed'
        summaries.append(pd.read_csv(directory/'strategy_comparison.csv',float_precision='round_trip'))
        phase.append(pd.read_csv(directory/'phase_sensitivity.csv'))
        plots.append(chart_rows(directory/'weekly_nav.csv.gz',job['scope']))
        p=pd.read_csv(HERE/'prepared'/job['prediction_file'],parse_dates=['date'],float_precision='round_trip');records=[]
        coverage.append(dict(model=job['model'],scope=job['scope'],rows=len(p),weeks=p.date.nunique(),first_signal=p.date.min(),last_signal=p.date.max(),minimum_stocks=p.groupby('date').size().min(),maximum_stocks=p.groupby('date').size().max()))
        for date,g in p.groupby('date'):
            actual=g.target1.rank(method='average');ric=g.prediction.rank(method='average').corr(actual)
            top=g.sort_values(['prediction','ticker'],ascending=[False,True]).head(5)
            relevance=np.floor((actual-1)*5/len(g)).clip(0,4);gain=pd.Series(np.exp2(relevance)-1,index=g.index);discount=np.log2(np.arange(2,7))
            records.append(dict(model=job['model'],scope=job['scope'],date=date,stocks=len(g),rank_ic=ric,ndcg_at5=np.sum(gain.loc[top.index].to_numpy()/discount)/np.sum(np.sort(gain)[::-1][:5]/discount),top5_label_return=np.expm1(top.target1).mean(),pool_label_return=np.expm1(g.target1).mean(),top5_positive_label_fraction=(top.target1>0).mean()))
        frame=pd.DataFrame(records);pred_weekly.append(frame)
        for window,dates in windows(sorted(p.date.unique())).items():
            z=frame[frame.date.isin(dates)];r=z.rank_ic.dropna()
            pred_summaries.append(pd.DataFrame([dict(model=job['model'],scope=job['scope'],window=window,weeks=len(z),rank_ic_valid_weeks=len(r),mean_rank_ic=r.mean(),rank_icir=r.mean()/r.std(ddof=1) if r.std(ddof=1)>0 else np.nan,positive_rank_ic_fraction=(r>0).mean(),mean_ndcg_at5=z.ndcg_at5.mean(),mean_top5_label_return=z.top5_label_return.mean(),mean_pool_label_return=z.pool_label_return.mean(),mean_top5_label_excess=(z.top5_label_return-z.pool_label_return).mean(),top5_positive_label_fraction=z.top5_positive_label_fraction.mean())]))
    s=pd.concat(summaries,ignore_index=True);s['model_label']=s.model.map(LABELS)
    assert not s.duplicated(['model','scope','window','strategy','capital','cost_bps']).any()
    save(s,'all_models_strategy_comparison.csv');save(s[s.scope.eq('Common210')],'common210_strategy_comparison.csv');save(s[s.scope.eq('Native366')],'native366_strategy_comparison.csv')
    save(pd.concat(phase,ignore_index=True),'all_models_phase_sensitivity.csv');save(pd.concat(plots,ignore_index=True),'plot_weekly_100k10bps.csv.gz')
    pe=pd.concat(pred_summaries,ignore_index=True);pe['model_label']=pe.model.map(LABELS);save(pe,'all_models_prediction_evaluation.csv');save(pd.concat(pred_weekly,ignore_index=True),'all_models_prediction_weekly.csv');save(pd.DataFrame(coverage),'coverage.csv')
    baseline=s[s.strategy.eq('UniverseEqualWeight')].pivot(index=['scope','window','capital','cost_bps'],columns='model',values='final_capital')
    for _,row in baseline.iterrows():assert np.allclose(row.dropna(),row.dropna().iloc[0],rtol=0,atol=1e-8)
    common=s[s.scope.eq('Common210')];keys=['scope','window','strategy','capital','cost_bps']
    pair=common[common.model.eq('Ensemble')].merge(common[common.model.eq('Ranker150_New')],on=keys,validate='one_to_one',suffixes=('_ensemble','_ranker150'))
    for metric in ['annualized_return','sharpe','max_drawdown','total_fees','final_capital']:pair[metric+'_ensemble_minus_ranker150']=pair[metric+'_ensemble']-pair[metric+'_ranker150']
    save(pair,'Ensemble_vs_Ranker150_common210.csv')
    for scope in ['Common210','Native366']:
        z=s[s.scope.eq(scope)&s.capital.eq(100000)&s.cost_bps.eq(10)].copy()
        for field in ['annualized_return','max_drawdown','total_return','volatility','mean_cash_ratio']:z[field]=z[field].map(lambda x:f'{x:.4%}')
        z=z[['model_label','scope','window','strategy','weeks','annualized_return','sharpe','max_drawdown','final_capital','total_fees','mean_cash_ratio']]
        z.columns=['模型','样本口径','窗口','策略','周数','年化收益','Sharpe','最大回撤_有符号','期末资金','手续费','平均现金比例']
        z.to_csv(OUT/f'重点指标_{scope}_10万10bps.csv',index=False,encoding='utf-8-sig',float_format='%.8g')
    manifest=dict(status='verified',distinct_models=int(s.model.nunique()),model_labels=LABELS,case_count=len(s),common_cases=int(s.scope.eq('Common210').sum()),native_cases=int(s.scope.eq('Native366').sum()),common_weeks=210,native_weeks=366,primary_strategies=15,extra_comparators=2,common_windows=14,native_windows=17,initial_capitals=[100000,10000],one_way_cost_bps=[0,10,25],all_benchmarks_identical_within_scope=True,old_two_model_results_unchanged=True,ndcg_definition='same exponential-gain definition for all six models: gain=2^weekly relevance-1; differs from original handoff sklearn linear-gain NDCG; original handoff metrics retained in source/outputs/current',price_proxy_caveat=True)
    (OUT/'run_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(manifest)
if __name__=='__main__':main()
