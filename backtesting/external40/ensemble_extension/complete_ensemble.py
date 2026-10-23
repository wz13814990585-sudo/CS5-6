"""Saved-model replay and integer backtests for ensemble and all components."""
from pathlib import Path
import gc,hashlib,json,sys
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE));import integer_backtest as engine
MODEL_COLUMNS={'Ensemble':'ensemble_ranking_score','Model1':'model_1_raw_score','Model2':'model_2_raw_score','Model3':'model_3_raw_score'}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def prepare():
    sys.path.insert(0,str(HERE/'source/code'))
    import ranker_core as core
    from prediction_helpers import load_test,training_window,score_block
    from xgboost import XGBRanker
    train,_=core.load_data(HERE/'source/inputs/train66.csv')
    test,_=load_test(HERE/'source/inputs/test40.csv',train)
    reference=pd.read_csv(HERE/'source/outputs/current/predictions/stock_rankings.csv',parse_dates=['date'],float_precision='round_trip')
    components={};audit=[]
    for number,spec in enumerate(core.COMPONENTS,1):
        blocks=[]
        for refit in range(core.FORMAL_START_WEEK,core.TOTAL_EXPECTED_WEEKS,core.REFIT_INTERVAL_WEEKS):
            training=training_window(train,spec,refit)
            block=test[test.week_index.between(refit,min(refit+26,core.TOTAL_EXPECTED_WEEKS)-1)]
            model_id=f'{spec.component_id}_refit_{refit:04d}'
            model=XGBRanker(n_jobs=1);model.load_model(HERE/'source/models'/f'{model_id}.json')
            predicted=score_block(model,spec,block)
            predicted['component_id']=spec.component_id;predicted['model_id']=model_id;predicted['refit_week']=refit
            match=predicted.merge(reference[['date','ticker',f'model_{number}_raw_score']],on=['date','ticker'],validate='one_to_one')
            np.testing.assert_array_equal(match.raw_ranking_score,match[f'model_{number}_raw_score'])
            audit.append(dict(model_id=model_id,rows=len(match),maximum_score_difference=0.,training_weeks=int(training.week_index.nunique()),last_training_signal=str(training.date.max().date()),refit_date=str(block.date.min().date()),training_label_observable=bool(training.label_end_week.max()<=refit)))
            blocks.append(predicted)
        components[spec.component_id]=pd.concat(blocks,ignore_index=True)
    replay=core.build_ensemble(components)
    match=replay.merge(reference,on=['date','ticker'],validate='one_to_one',suffixes=('_replay','_reference'))
    for column in list(MODEL_COLUMNS.values())+['model_1_percentile','model_2_percentile','model_3_percentile','ensemble_predicted_rank']:
        np.testing.assert_array_equal(match[column+'_replay'],match[column+'_reference'])
    np.testing.assert_allclose(reference.ensemble_ranking_score,reference[['model_1_percentile','model_2_percentile','model_3_percentile']].mean(axis=1),rtol=0,atol=1e-15)
    raw=pd.read_csv(BASE/'inputs/test40_with_prices.csv',parse_dates=['date'],float_precision='round_trip')
    joined=reference.merge(raw,on=['date','ticker'],validate='one_to_one',suffixes=('_source',''))
    assert len(joined)==len(reference)==13517
    np.testing.assert_allclose(joined.actual_next_week_log_return,joined.target1,rtol=0,atol=1e-12)
    factor_check=test[['date','ticker',*core.FIVE_FEATURES]].merge(raw[['date','ticker',*core.FIVE_FEATURES]],on=['date','ticker'],validate='one_to_one',suffixes=('_prediction','_price_input'))
    assert len(factor_check)==len(reference)
    for factor in core.FIVE_FEATURES:np.testing.assert_allclose(factor_check[factor+'_prediction'],factor_check[factor+'_price_input'],rtol=0,atol=1e-12)
    common=pd.read_csv(BASE/'prepared/predictions.csv',parse_dates=['date'])[['date','ticker']]
    assert len(joined.merge(common,on=['date','ticker'],validate='one_to_one'))==len(common)==8354
    jobs=[]
    for model,column in MODEL_COLUMNS.items():
        p=joined[list(raw.columns)].copy();p['prediction']=joined[column];p=p.sort_values(['date','ticker'])
        p['rank']=p.groupby('date').prediction.rank(method='first',ascending=False)
        expected=joined[['date','ticker','ensemble_predicted_rank' if model=='Ensemble' else f'model_{model[-1]}_predicted_rank']]
        checked=p.merge(expected,on=['date','ticker'],validate='one_to_one')
        assert np.array_equal(checked['rank'],checked.iloc[:,-1])
        for scope,frame in [('Native366',p),('Common210',p.merge(common,on=['date','ticker'],validate='one_to_one'))]:
            filename=f'{model}_{scope}.csv';frame.to_csv(HERE/'prepared'/filename,index=False,float_format='%.17g')
            jobs.append(dict(model=model,scope=scope,prediction_file=filename,weeks=int(frame.date.nunique()),rows=len(frame)))
    pd.DataFrame(audit).to_csv(HERE/'prepared/saved_model_replay_audit.csv',index=False)
    info=dict(status='passed',saved_models_replayed=len(audit),maximum_raw_score_error=0,ensemble_formula_verified=True,native_rows=len(joined),native_weeks=int(joined.date.nunique()),native_first=str(joined.date.min().date()),native_last=str(joined.date.max().date()),native_min_stocks=int(joined.groupby('date').size().min()),native_max_stocks=int(joined.groupby('date').size().max()),common_rows=len(common),common_weeks=int(common.date.nunique()),prediction_source_sha256=digest(HERE/'source/outputs/current/predictions/stock_rankings.csv'),price_source_sha256=digest(BASE/'inputs/test40_with_prices.csv'),models_retrained=False,hyperparameters_changed=False,labels_used_for_trading=False)
    (HERE/'prepared/source_audit.json').write_text(json.dumps(info,indent=2));(HERE/'prepared/jobs.json').write_text(json.dumps(jobs,indent=2))
    print('Ensemble replay and price-key audit',info,flush=True)
    return jobs

def main():
    jobs=prepare()
    for job in jobs:
        directory=HERE/'runs'/f'{job["model"]}_{job["scope"]}';directory.mkdir(exist_ok=True)
        predicted=HERE/'prepared'/job['prediction_file']
        identity=dict(engine_sha256=digest(BASE/'integer_backtest.py'),prediction_sha256=digest(predicted))
        manifest=directory/'run_manifest.json'
        if manifest.exists() and all(json.loads(manifest.read_text()).get(k)==v for k,v in identity.items()):
            print('Reuse completed',directory.name,flush=True);continue
        result=engine.simulate_model(job['model'],str(predicted))
        for i,name in enumerate(['strategy_comparison.csv','weekly_nav.csv.gz','trade_ledger_10bps.csv.gz','holdings_10bps.csv.gz','phase_sensitivity.csv']):
            result[i].assign(scope=job['scope']).to_csv(directory/name,index=False,float_format='%.17g',compression='gzip' if name.endswith('.gz') else None)
        manifest.write_text(json.dumps(dict(**job,**identity,status='computed_pending_verification',summary_cases=len(result[0]),coverage=result[5]),indent=2))
        print('Saved',directory.name,len(result[0]),flush=True)
        del result;gc.collect()
if __name__=='__main__':main()
