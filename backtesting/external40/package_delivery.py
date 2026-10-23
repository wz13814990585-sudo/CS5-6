"""Package an independent full reproduction plus a small report-writing set."""
from pathlib import Path
import hashlib,json,shutil,zipfile

HERE=Path(__file__).resolve().parent;OUT=HERE/'results'
DEST=HERE.parent.parent/'新旧模型整数股回测_20261022'
def main():
    assert json.loads((OUT/'verification.json').read_text())['both_models_evaluated']
    DEST.mkdir(exist_ok=False);key=DEST/'重点文件';key.mkdir()
    full=DEST/'完整复现'
    ignore=shutil.ignore_patterns('__pycache__','.DS_Store','*.log','quartz_probe.png','.data-app-offline','.git')
    shutil.copytree(HERE,full,ignore=ignore)
    files={
      HERE/'report_app/.data-app-offline/exports/新旧模型整数股评估报告.html':'01_新旧模型整数股评估报告.html',
      OUT/'整数股回测报告.md':'02_评估报告.md',
      OUT/'重点指标_10万10bps.csv':'03_重点指标_10万10bps.csv',
      OUT/'new_vs_old_comparison.csv':'04_新旧模型配对比较.csv',
      OUT/'prediction_evaluation.csv':'05_模型排序评估.csv',
      OUT/'charts/ModelComparison/FullHistory_Top5.png':'06_完整期Top5新旧对比.png',
      OUT/'charts/ModelComparison/FinalTest_Top10.png':'07_最终期Top10新旧对比.png',
      OUT/'charts/ModelComparison/FinalTest_Top5_RankWeighted.png':'08_最终期排名加权Top5新旧对比.png',
      OUT/'Top5_逐笔整数股交易.csv':'09_Top5逐笔交易.csv',
      OUT/'Top5_逐周资金.csv':'10_Top5逐周资金.csv',
      OUT/'FinalTest_annualized_return.png':'FinalTest_annualized_return.png',
    }
    for source,name in files.items():shutil.copy2(source,key/name)
    for name in ['FullHistory_Top5.png','FinalTest_Top10.png']:
        target=key/'charts/ModelComparison'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(OUT/'charts/ModelComparison'/name,target)
    (DEST/'先看这里.md').write_text('''# 新旧版模型整数股回测交付

这次比较的是新版150树与此前旧版50树XGBRanker，已同时完成两版回测。

先打开“重点文件/01_新旧模型整数股评估报告.html”（可双击离线查看）；写项目报告时看02报告正文、03中文指标表，以及06至08折线图。03包含两版全部策略和14窗口的10万资金、10bps结果；04包含全部资金与成本的配对差值。09和10可说明整数股交易过程。

“完整复现”保存共同输入、新版模型权重、旧版原脚本与训练数据、实际预测、整数股引擎、验证脚本、全部2856组指标、216组相位结果、全部费用资金路径、10bps持仓与交易流水、386张折线/回撤图及报告源项目。复现方法见其README.md。

主结果：完整210周、初始10万、单边10bps，等权Top5新版年化-6.26%、Sharpe-0.099、最大回撤55.27%；旧版年化2.82%、Sharpe0.237、最大回撤37.69%。股票池等权年化7.70%。新版并非全面更优。资金与报价同币种；使用交付开收盘代理价格的历史模拟。

本地在线预览 http://127.0.0.1:4185/ 只在当前电脑服务运行时有效。离线HTML不需要该服务。完整复现/source和old_source中的README为原交付材料；本次执行口径以完整复现/README.md和最终报告为准。
''',encoding='utf-8')
    manifest=[]
    for file in sorted(DEST.rglob('*')):
        if file.is_file():manifest.append(dict(path=str(file.relative_to(DEST)),bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    (DEST/'文件校验清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    archive=DEST.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(DEST.rglob('*')):
            if file.is_file():z.write(file,str(file.relative_to(DEST.parent)))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps(dict(folder=str(DEST),zip=str(archive),files=len(manifest)+1,zip_bytes=archive.stat().st_size,zip_crc_passed=True),ensure_ascii=False))
if __name__=='__main__':main()
