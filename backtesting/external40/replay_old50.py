"""Re-run the frozen old hyperparameters; verify, never re-select a winner."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
def main():
    spec=importlib.util.spec_from_file_location('old_reference',HERE/'old_source/run_external40_simulation.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    train,test=m.load_inputs()
    frozen=pd.read_csv(HERE/'old_source/standalone_predictions.csv',parse_dates=['date'],float_precision='round_trip')
    chosen=json.loads((HERE/'old_source/standalone_selection.json').read_text())['chosen_candidate']
    replay=m.rolling_predictions(train,test,chosen,test.date.min(),test.date.max())
    j=replay.merge(frozen,on=['date','ticker'],validate='one_to_one',suffixes=('_replayed','_frozen'))
    assert len(j)==len(frozen)==len(replay)
    error=float(abs(j.prediction-j.prediction_score).max())
    rank_replay=j.groupby('date').prediction.rank(method='first',ascending=False)
    rank_frozen=j.groupby('date').prediction_score.rank(method='first',ascending=False)
    assert error<1e-7 and np.array_equal(rank_replay,rank_frozen)
    result=dict(status='passed',refits=int(replay.refit_date.nunique()),rows=len(j),maximum_score_difference=error,rankings_identical=True,chosen_candidate=chosen,hyperparameter_search_rerun=False,training_test_ticker_overlap=len(set(train.ticker)&set(test.ticker)))
    (HERE/'prepared/old50_replay_audit.json').write_text(json.dumps(result,indent=2))
    print(result)
if __name__=='__main__':main()
