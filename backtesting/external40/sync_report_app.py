"""Refresh the local report's reviewed evidence and copy, preserving its ID."""
from pathlib import Path
import json
import pandas as pd

HERE=Path(__file__).resolve().parent;OUT=HERE/'results'
def main():
    payload=json.loads((OUT/'artifact.json').read_text());manifest=payload['manifest']
    sources={s['id']:s for s in manifest['sources']};queries={}
    for key,rows in payload['snapshot']['datasets'].items():
        asset=next((a for a in manifest['charts']+manifest['tables'] if a['dataset']==key),None)
        sid=payload.get('package_info',{}).get('datasetSources',{}).get(key) or (asset['sourceId'] if asset else ('weekly' if key.endswith('nav') else 'prediction' if key=='prediction' else 'summary'))
        source=sources[sid]
        filename=source.get('files') or [{'weekly':'weekly_nav.csv.gz','prediction':'prediction_evaluation.csv','summary':'strategy_comparison.csv'}.get(sid,source['label'])]
        queries[key]=dict(rows=rows,source=dict(label=source['label'],sql=source['query']['sql'],tables=source['query']['tables_used'],files=filename,classification='local supplied data and historical modeled scenarios',filters=[source['query'].get('description','按数据中的scope与window区分共同210周和集成体系完整366周；图表资金100000、单边10bps')],metricDefinitions=[dict(label='评估口径',definition='；'.join(source['query']['metric_definitions']))],caveats=['开收盘代理价格尚未独立核验复权与可成交性；无外汇转换','target1仅用于预测评估，组合盈亏依据价格和整数股']),methods=[dict(language='python',code='Reproduce with prepare_comparison.py, replay_old50.py, integer_backtest.py, evaluate_comparison.py, build_report.py; ensemble_extension/complete_ensemble.py, verify_extension.py, evaluate_extension.py, extend_report.py. Filter recorded SQL results to the named scope/window/strategy; NAV=end_capital/capital. Initial NAV=1 uses first signal minus seven days as an initial marker, not a trade-date claim.')])
    queries['all_cases']=dict(rows=json.loads(pd.read_csv(OUT/'strategy_comparison.csv').to_json(orient='records',double_precision=15)),source=dict(queries['full']['source']))
    queries['all_cases']['source']['filters']=['两版全部2856情景，14窗口×17规则×2资金×3费用']
    snapshot=dict(surface='report',title=manifest['title'],generatedAt='2026-10-22T00:00:00+11:00',status='ready',filters=[],queries=queries,buildStatus='complete',report={})
    target=HERE/'report_app/src/data.json'
    if target.exists():snapshot['id']=json.loads(target.read_text())['id']
    else:raise RuntimeError('Prepare report_app with the Data app preparer before syncing. Numerical results and Markdown do not depend on this step.')
    target.write_text(json.dumps(snapshot,ensure_ascii=False))
    (HERE/'report_app/src/content/report/report-story.json').write_text(json.dumps(manifest,ensure_ascii=False))
    (OUT/'reviewed_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False))
    notes=json.loads((OUT/'report_source_notes.json').read_text());notes['surface']='local shared Data report app; portable offline HTML and Markdown; requested PNG figures';notes['replay_audits']=['prepared/comparison_audit.json','prepared/old50_replay_audit.json'];(OUT/'report_source_notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
    print('Synced report; preserved ID',snapshot['id'])
if __name__=='__main__':main()
