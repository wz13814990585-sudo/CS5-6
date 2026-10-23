"""Add ensemble files to the existing delivery, preserving unrelated files."""
from pathlib import Path
import hashlib,json,shutil,zipfile
import pandas as pd
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;DEST=BASE.parent.parent/'新旧模型整数股回测_20261022'
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
def archive(folder,target):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(folder.rglob('*')):
            if f.is_file() and f.suffix!='.zip' and f.name!='.DS_Store':z.write(f,str(f.relative_to(folder.parent)))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
def main():
    manifest=json.loads((HERE/'results/run_manifest.json').read_text());assert manifest['case_count']==15504
    full=DEST/'完整复现';key=DEST/'重点文件';ens=DEST/'Ensemble重点文件';ens.mkdir(exist_ok=True)
    shutil.copytree(HERE,full/'ensemble_extension',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.log','.DS_Store'))
    for name in ['run_all.py','sync_report_app.py','results/整数股回测报告.md','results/artifact.json','results/report_sources.sqlite','results/report_source_notes.json','results/reviewed_snapshot.json']:
        copy(BASE/name,full/name)
    for name in ['src/data.json','src/content/report/ReportContent.jsx','src/content/report/report-story.json','dist/index.html','dist/data-app-build.json']:
        copy(BASE/'report_app'/name,full/'report_app'/name)
    build=json.loads((BASE/'report_app/dist/data-app-build.json').read_text());copy(BASE/'report_app/dist'/build['snapshot']['path'],full/'report_app/dist'/build['snapshot']['path'])
    for name in ['Common210/FullHistory_Top5.png','Common210/FinalTest_Top10.png','Native366/FullHistory_Top5.png']:
        for folder in [full/'results',key,ens]:copy(HERE/'results/charts'/name,folder/'charts/EnsembleSupplement'/name)
    for name in ['Common210_FullHistory_annualized_return.png','Common210_FinalTest_annualized_return.png']:
        for folder in [full/'results',key,ens]:copy(HERE/'results'/name,folder/('EnsembleSupplement_'+name))
    for old,new in [('01_新旧模型整数股评估报告.html','01_原独立两版报告_保留.html'),('02_评估报告.md','02_原独立两版报告_保留.md'),('03_重点指标_10万10bps.csv','03_原独立两版指标_保留.csv')]:
        if not (key/new).exists():copy(key/old,key/new)
    html=BASE/'report_app/.data-app-offline/exports/新旧模型整数股评估报告.html'
    copy(html,key/'01_新旧模型整数股评估报告.html');copy(html,ens/'01_含Ensemble的完整评估报告.html')
    copy(BASE/'results/整数股回测报告.md',key/'02_评估报告.md');copy(HERE/'results/Ensemble补充评估回测报告.md',ens/'02_Ensemble评估回测报告.md')
    copy(HERE/'results/重点指标_Common210_10万10bps.csv',key/'03_重点指标_10万10bps.csv');copy(HERE/'results/all_models_prediction_evaluation.csv',key/'05_模型排序评估.csv')
    mapping={
      '重点指标_Common210_10万10bps.csv':'03_六模型共同210周指标.csv',
      '重点指标_Native366_10万10bps.csv':'04_集成体系完整366周指标.csv',
      'Ensemble_vs_Ranker150_common210.csv':'05_Ensemble与独立新版配对比较.csv',
      'all_models_prediction_evaluation.csv':'06_六模型排序评估.csv',
      'original_RankIC_reconciliation.csv':'原交付RankIC复算对照.csv',
    }
    for source,name in mapping.items():copy(HERE/'results'/source,ens/name)
    copy(HERE/'results/Ensemble_vs_Ranker150_common210.csv',key/'11_Ensemble与独立新版配对比较.csv')
    for path,name in [('Common210/FullHistory_Top5.png','06_完整期Top5新旧对比.png'),('Common210/FinalTest_Top10.png','07_最终期Top10新旧对比.png'),('Common210/FinalTest_Top5_RankWeighted.png','08_最终期排名加权Top5新旧对比.png')]:copy(HERE/'results/charts'/path,key/name)
    for path,name in [('Common210/FullHistory_Top10.png','07_共同210周Top10折线图.png'),('Native366/FullHistory_Top5.png','08_完整366周Top5折线图.png'),('Common210/FinalTest_Top10.png','09_最终51周Top10折线图.png')]:copy(HERE/'results/charts'/path,ens/name)
    for source,name in [('source/model_configuration.json','模型完整配置.json'),('source/inputs/factor_definitions.csv','因子定义.csv'),('prepared/saved_model_replay_audit.csv','45个滚动模型重放核验.csv'),('prepared/source_audit.json','预测价格关联审计.json'),('prepared/factor_input_alignment.json','五因子数值与排名核对.json')]:copy(HERE/source,ens/name)
    copy(HERE/'README.md',ens/'00_先看这里_模型因子与文件说明.md')
    trades=[pd.read_csv(BASE/'results/Top5_逐笔整数股交易.csv').assign(scope='Common210')]
    weeklies=[pd.read_csv(BASE/'results/Top5_逐周资金.csv').assign(scope='Common210')]
    for job in json.loads((HERE/'prepared/jobs.json').read_text()):
        directory=HERE/'runs'/f'{job["model"]}_{job["scope"]}'
        for chunk in pd.read_csv(directory/'trade_ledger_10bps.csv.gz',chunksize=100000):
            z=chunk[chunk.window.eq('FullHistory')&chunk.strategy.eq('Top5')&chunk.capital.eq(100000)]
            if len(z):trades.append(z)
        z=pd.read_csv(directory/'weekly_nav.csv.gz');weeklies.append(z[z.window.eq('FullHistory')&z.strategy.eq('Top5')&z.capital.eq(100000)&z.cost_bps.eq(10)])
    tx=pd.concat(trades,ignore_index=True);wk=pd.concat(weeklies,ignore_index=True)
    tx.to_csv(key/'09_Top5逐笔交易.csv',index=False,encoding='utf-8-sig');wk.to_csv(key/'10_Top5逐周资金.csv',index=False,encoding='utf-8-sig')
    tx[tx.model.eq('Ensemble')].to_csv(ens/'10_Ensemble_Top5逐笔交易.csv',index=False,encoding='utf-8-sig');wk[wk.model.eq('Ensemble')].to_csv(ens/'11_Ensemble_Top5逐周资金.csv',index=False,encoding='utf-8-sig')
    guide='''# 已补齐Ensemble：六模型完整评估回测

现在包括Ensemble、三个子模型、独立新版150树与独立旧版50树。此前漏交的Ensemble部分已补齐；原独立模型结果保留。

先打开Ensemble重点文件/01_含Ensemble的完整评估报告.html。写报告时用02报告正文、03共同210周指标、04完整366周指标、05配对比较和07至09折线图。重点文件中的01报告、02正文、03主指标、05排序评估和09/10交易资金示例，也已更新为包含Ensemble的版本；旧独立报告另存“保留”文件。

完整复现/ensemble_extension/source/保存原集成交接包，models/有45个权重JSON，code/为源码，model_configuration.json为参数与特征，inputs/factor_definitions.csv为因子定义。Ensemble是三套输出百分位的均值，没有额外的Ensemble权重JSON。

完整复现/ensemble_extension/results/保存全部六模型指标、共同210周与完整366周两种口径、510张新增折线/回撤图、预测评估和验证结果。runs/保存逐模型逐口径的完整资金、交易和股数持仓。共15,504组回测情景，原有386张独立模型图保留。

Common210使用2022-08-26至2026-08-28的同一8,354个股票周公平比较六模型；Native366保留2019-08-30至2026-08-28集成体系13,517个股票周。不同长度的完整期结果不能混比。所有情景按整数股、剩余现金、实际交易额双边费用重算，资金1万/10万，单边0/10/25bps。

共同210周、10万、10bps：Ensemble Top5年化1.96%、Sharpe0.207；Top10年化12.40%、Sharpe0.626。最终51周两者分别-32.28%、-17.90%。完整366周Top5年化11.29%、Top10年化11.89%。使用交付开收盘代理的历史模拟，不代表未来表现。

本地预览：http://127.0.0.1:4185/ 。离线HTML可直接打开。复现六模型用完整复现/run_all.py，单独重跑集成体系见完整复现/ensemble_extension/README.md。
'''
    (DEST/'先看这里.md').write_text(guide,encoding='utf-8');(DEST/'Ensemble已补齐_新增内容说明.md').write_text(guide,encoding='utf-8')
    readme=full/'README.md';old=readme.read_text();prefix='''# Ensemble补充已完成（2026年10月22日）

本交付现在覆盖六个模型，共同210周和集成体系完整366周分别评估；共15,504组情景。新增内容与45个模型权重见ensemble_extension/README.md。默认run_all.py现同时复现原独立两版与新增集成体系。最终整合报告为results/整数股回测报告.md。

下文保留原独立两版的说明，2,856组等数字仅描述原独立模型部分。

---

'''
    if not old.startswith('# Ensemble补充'):readme.write_text(prefix+old,encoding='utf-8')
    print('Folder content updated; writing archives',flush=True)
    oldzip=DEST/'重点文件.zip';backup=DEST/'重点文件_补充前_仅独立两版.zip'
    if oldzip.exists() and not backup.exists():copy(oldzip,backup)
    archive(key,oldzip);archive(ens,DEST/'Ensemble重点文件.zip')
    checks=[]
    for f in sorted(DEST.rglob('*')):
        if f.is_file() and f.name not in ['文件校验清单.json','.DS_Store'] and f.suffix!='.zip':checks.append(dict(path=str(f.relative_to(DEST)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    (DEST/'文件校验清单.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
    archive(DEST,DEST.with_suffix('.zip'))
    assert len(list((full/'ensemble_extension/source/models').glob('*.json')))==45
    assert len(pd.read_csv(full/'ensemble_extension/results/all_models_strategy_comparison.csv'))==15504
    print(json.dumps(dict(status='completed',folder=str(DEST),ensemble_key_folder=str(ens),models=6,cases=15504,new_line_figures=510,model_weights=45,archives_crc_passed=True,full_zip_bytes=DEST.with_suffix('.zip').stat().st_size),ensure_ascii=False))
if __name__=='__main__':main()
