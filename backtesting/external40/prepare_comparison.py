"""Replay supplied new weights; align frozen old predictions without re-selection."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    raw_path=HERE/'inputs/test40_with_prices.csv'
    spec=importlib.util.spec_from_file_location('saved',HERE/'source/run_saved_model_simulation.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    raw=module.load_test(raw_path)
    new=module.predict(raw,HERE/'source/models').sort_values(['date','ticker'])
    delivered=pd.read_csv(HERE/'source/predictions/external_test_predictions.csv',parse_dates=['date'])
    joined=new.merge(delivered[['date','ticker','prediction','rank']],on=['date','ticker'],validate='one_to_one',suffixes=('_replayed','_delivered'))
    assert len(joined)==len(new)==len(delivered)
    assert np.array_equal(joined.rank_replayed,joined.rank_delivered)
    err=float(abs(joined.prediction_replayed-joined.prediction_delivered).max())
    assert err<1e-6
    new.to_csv(HERE/'prepared/predictions.csv',index=False,float_format='%.17g')
    old_path=HERE/'old_source/standalone_predictions.csv'
    frozen=pd.read_csv(old_path,parse_dates=['date'],float_precision='round_trip')
    assert not frozen.duplicated(['date','ticker']).any()
    frozen=frozen.rename(columns={'prediction_score':'prediction'})
    old=raw.merge(frozen[['date','ticker','prediction','actual_next_week_log_return','refit_date']],on=['date','ticker'],validate='one_to_one').sort_values(['date','ticker'])
    assert len(old)==len(frozen)==len(new)
    assert old[['date','ticker']].reset_index(drop=True).equals(new[['date','ticker']].reset_index(drop=True))
    assert np.allclose(old.target1,old.actual_next_week_log_return,rtol=0,atol=1e-15)
    old['rank']=old.groupby('date').prediction.rank(method='first',ascending=False)
    old.to_csv(HERE/'prepared/old50_predictions.csv',index=False,float_format='%.17g')
    result=dict(status='aligned',new_model='supplied saved candidate2; 150 trees; nine refits',old_model='frozen predictions from previous standalone candidate1; 50 trees; no re-selection',rows_each=len(old),weeks_each=int(old.date.nunique()),stocks=int(old.ticker.nunique()),first_signal=str(old.date.min().date()),last_signal=str(old.date.max().date()),common_keys_identical=True,new_replayed_max_score_difference=err,new_replayed_ranks_identical=True,input_sha256=digest(raw_path),old_frozen_prediction_sha256=digest(old_path),first_raw_date=str(raw.date.min().date()),last_raw_date=str(raw.date.max().date()))
    (HERE/'prepared/comparison_audit.json').write_text(json.dumps(result,indent=2))
    print(result)
if __name__=='__main__':main()
