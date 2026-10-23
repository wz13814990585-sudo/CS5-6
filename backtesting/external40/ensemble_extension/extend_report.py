"""Add ensemble findings to the existing report, retaining independent-model work."""
from pathlib import Path
import json,sqlite3
import pandas as pd
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=HERE/'results'
sys_labels={'Ensemble':'Ensemble等权集成','Ranker150_New':'独立新版150树','Ranker50_Old':'独立旧版50树','Model1':'子模型1（156周/五因子）','Model2':'子模型2（52周/两因子）','Model3':'子模型3（52周/五因子）','Benchmark':'共同股票池等权'}
def records(frame):return json.loads(frame.to_json(orient='records',date_format='iso',double_precision=12))
def main():
    verification=json.loads((OUT/'verification.json').read_text());assert verification['status']=='passed'
    basefile=BASE/'results/artifact.json';base=json.loads(basefile.read_text())
    # Always extend the preserved two-version report, never recursively append.
    original=HERE/'prepared/original_two_model_artifact.json'
    original_md=HERE/'prepared/original_two_model_report.md'
    if not base.get('package_info',{}).get('ensembleComplete'):
        original.write_text(basefile.read_text());original_md.write_text((BASE/'results/整数股回测报告.md').read_text())
    base=json.loads(original.read_text());m=base['manifest'];datasets=base['snapshot']['datasets']
    c=sqlite3.connect(BASE/'results/report_sources.sqlite')
    for file,table in [('all_models_strategy_comparison.csv','ensemble_strategy_comparison'),('plot_weekly_100k10bps.csv.gz','ensemble_weekly_chart'),('all_models_prediction_evaluation.csv','ensemble_prediction_evaluation')]:
        pd.read_csv(OUT/file).to_sql(table,c,if_exists='replace',index=False)
    pd.read_csv(HERE/'prepared/saved_model_replay_audit.csv').to_sql('ensemble_saved_model_audit',c,if_exists='replace',index=False)
    s=pd.read_sql_query('SELECT * FROM ensemble_strategy_comparison',c)
    w=pd.read_sql_query('SELECT * FROM ensemble_weekly_chart',c,parse_dates=['date'])
    e=pd.read_sql_query('SELECT * FROM ensemble_prediction_evaluation',c)
    audit=pd.read_sql_query('SELECT * FROM ensemble_saved_model_audit',c)
    headline=s[s.capital.eq(100000)&s.cost_bps.eq(10)]
    def row(model,scope,window,strategy):return headline[headline.model.eq(model)&headline.scope.eq(scope)&headline.window.eq(window)&headline.strategy.eq(strategy)].iloc[0]
    ens5=row('Ensemble','Common210','FullHistory','Top5');ens10=row('Ensemble','Common210','FullHistory','Top10');final5=row('Ensemble','Common210','FinalTest','Top5');final10=row('Ensemble','Common210','FinalTest','Top10');new5=row('Ranker150_New','Common210','FullHistory','Top5');new10=row('Ranker150_New','Common210','FullHistory','Top10');native5=row('Ensemble','Native366','FullHistory','Top5');native10=row('Ensemble','Native366','FullHistory','Top10');benchmark=row('Ensemble','Common210','FullHistory','UniverseEqualWeight')
    blocks=[];charts=[];tables=[];md=[]
    def prose(id,heading,body,source='ensemble_summary'):
        value=heading+'\n\n'+body;blocks.append(dict(id=id,type='markdown',body=value,sourceId=source));md.append(value)
    def table(id,title,dataset,frame,cols,source='ensemble_summary'):
        datasets[dataset]=records(frame);tables.append(dict(id=id,title=title,dataset=dataset,sourceId=source,layout='full',columns=[dict(field=f,label=l,**({'format':fmt} if fmt else {})) for f,l,fmt in cols]));blocks.append(dict(id=id+'-block',type='table',tableId=id))
        def fmt(v,typ):return f'{v:.2%}' if typ=='percent' else f'{v:.4f}' if isinstance(v,float) else str(v)
        md.append('### '+title+'\n\n| '+' | '.join(l for _,l,_ in cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(fmt(r[f],form) for f,_,form in cols)+' |' for _,r in frame.iterrows()))
    def chart(id,title,dataset,frame,kind='line',x='date',y='nav',series='label'):
        datasets[dataset]=records(frame);spec=dict(id=id,title=title,dataset=dataset,sourceId='ensemble_weekly' if kind=='line' else 'ensemble_summary',type=kind,layout='full',question=title,encodings=dict(x=dict(field=x,type='temporal' if x=='date' else 'nominal'),y=dict(field=y,type='quantitative'),color=dict(field=series,type='nominal')),palette=dict(kind='categorical'))
        if y=='annualized_return':spec['encodings']['y']['format']='percent'
        charts.append(spec);blocks.append(dict(id=id+'-block',type='chart',chartId=id))
    def curve(scope,window,strategy,models):
        z=w[w.scope.eq(scope)&w.window.eq(window)&((w.strategy.eq(strategy)&w.model.isin(models))|(w.strategy.eq('UniverseEqualWeight')&w.model.eq('Ensemble')))].copy()
        z['label']=[sys_labels['Benchmark' if st=='UniverseEqualWeight' else model] for model,st in zip(z.model,z.strategy)];z['nav']=z.end_capital/z.capital
        initial=[]
        for label,g in z.groupby('label'):
            r=g.sort_values('date').iloc[0].copy();r['date']-=pd.Timedelta(days=7);r['nav']=1.;r['end_capital']=r.capital;r['net_return']=0.;initial.append(r)
        return pd.concat([z,pd.DataFrame(initial)],ignore_index=True).sort_values(['label','date'])
    title='Ensemble与独立Ranker：完整整数股评估回测'
    prose('ensemble-summary','## 完整评估结论',
        f'**已补齐Ensemble及三个子模型。** 现在包括等权集成、三个子模型、独立新版150树、独立旧版50树，共六个预测模型；Ensemble是三个子模型百分位分数的等权平均，没有第四套独立训练权重。\n\n'
        f'**共同210周中，Ensemble的Top10表现较好，但优势没有延续到最终期。** 初始资金10万、单边10bps：Ensemble Top10年化{ens10.annualized_return:.2%}、Sharpe{ens10.sharpe:.3f}，独立新版Top10为{new10.annualized_return:.2%}；共同股票池等权为{benchmark.annualized_return:.2%}。最终51周，Ensemble Top10降至{final10.annualized_return:.2%}，Top5为{final5.annualized_return:.2%}。完整期结果不能证明稳定优胜。\n\n'
        f'**完整历史与公平比较分别报告。** 集成体系保留2019年8月30日至2026年8月28日的366周；六模型比较使用相同8,354个股票周、210周。15种策略、两种对照、1万/10万资金和0/10/25bps均以整数股重新模拟。原两版独立模型的结果保留。')
    prose('ensemble-setup','## Ensemble如何构成，哪些文件已补齐',
        '子模型1采用156周训练窗口、五因子；子模型2采用52周、经营盈利能力和债务资产比；子模型3采用52周、五因子并使用更强正则化。五因子为收入增长、经营盈利能力、现金流/资产、负债/资产、资产增长。全部每26周更新；每个子模型先在当周外部股票池内将原始分数转成百分位，再取三者等权均值排序。\n\n'
        '**45个保存模型已按各自历史生效区间重新加载，原始分数、百分位和Ensemble排名与交付文件完全一致，最大原始分数误差为0。** 未用最后一期权重倒推过去，也没有重训或改变集成权重。补充包保留45个JSON、完整配置、预测CSV、原机器学习评估、源码、因子定义、训练窗口和价格关联审计。\n\n'
        '完整历史每周可用27–40只股票，共同210周为38–40只。所有预测均按日期与股票一对一接到同一价格文件，标签核对通过，没有丢掉2019–2022的预测。两种时间口径的年化不直接混在一起比较。','ensemble_audit')
    prose('ensemble-common-finding','## 共同210周：比较相同股票、日期和执行规则',
        f'下面固定比较等权Top5。Ensemble年化{ens5.annualized_return:.2%}、Sharpe{ens5.sharpe:.3f}、最大回撤幅度{-ens5.max_drawdown:.2%}；独立新版年化{new5.annualized_return:.2%}。图中股票池等权是同资金、同成本的共同对照。所有窗口从现金、净值1独立开始，不把较早积累的收益带进共同区间。')
    chart('ensemble-common-nav','共同210周Top5净值：Ensemble与独立模型','ens_common_nav',curve('Common210','FullHistory','Top5',['Ensemble','Ranker150_New','Ranker50_Old']))
    md.append('![共同210周Top5](charts/EnsembleSupplement/Common210/FullHistory_Top5.png)')
    prose('ensemble-common-table-note', '## 六模型的同一Top5策略', '下表增加三个子模型作为拆解对照，股票池等权仅保留一行。模型排序与资金权重属于不同步骤：相同模型改用Top10或排名加权后，收益和风险都会变化，不能由Top5推断所有策略的结果。')
    top=headline[headline.scope.eq('Common210')&headline.window.eq('FullHistory')&headline.strategy.eq('Top5')].copy();base_row=benchmark.copy();base_row['model']='Benchmark';top=pd.concat([top,pd.DataFrame([base_row])],ignore_index=True);top['model_label']=top.model.map(sys_labels)
    table('ensemble-model-table','共同210周、10万、10bps：各模型Top5','ens_models',top,[('model_label','模型',None),('annualized_return','年化收益','percent'),('sharpe','Sharpe',None),('max_drawdown','最大回撤','percent'),('final_capital','期末资金',None)])
    prose('ensemble-strategy-finding','## 策略会改变模型比较的结论',
        f'共同210周中，Ensemble Top10的年化为{ens10.annualized_return:.2%}，高于其Top5的{ens5.annualized_return:.2%}；Top10使用更多股票，改变了集中度与持仓路径。下面按预先已有的Top5、Top10和排名加权Top5比较三套主要输出，没有按新结果更换规则。')
    bar=headline[headline.scope.eq('Common210')&headline.window.eq('FullHistory')&headline.model.isin(['Ensemble','Ranker150_New','Ranker50_Old'])&headline.strategy.isin(['Top5','Top10','Top5_RankWeighted'])].copy();bar['version']=bar.model.map(sys_labels);bar['strategy_label']=bar.strategy.replace({'Top5':'等权Top5','Top10':'等权Top10','Top5_RankWeighted':'排名加权Top5'})
    chart('ensemble-common-bar','共同210周代表策略年化：集成与独立模型','ens_common_bar',bar,kind='bar',x='strategy_label',y='annualized_return',series='version')
    md.append('![共同210周年化](EnsembleSupplement_Common210_FullHistory_annualized_return.png)')
    prose('ensemble-final-finding','## 最终51周：Ensemble也出现明显亏损',
        f'最终期仍采用2025年9月5日至2026年8月21日的51周。Ensemble Top5年化{final5.annualized_return:.2%}、Sharpe{final5.sharpe:.3f}；Top10年化{final10.annualized_return:.2%}、Sharpe{final10.sharpe:.3f}。这段结果说明，完整期较好的策略不能直接作为稳定性的证据。该区间已经查看，不能再当作新的未见测试。')
    chart('ensemble-final-nav','最终51周Top10净值：Ensemble与独立模型','ens_final_nav',curve('Common210','FinalTest','Top10',['Ensemble','Ranker150_New','Ranker50_Old']))
    md.append('![最终期Top10](charts/EnsembleSupplement/Common210/FinalTest_Top10.png)')
    prose('ensemble-pair-note','## 15种策略的成对结果',
        '下表完整保留Ensemble与独立新版在共同完整期和最终期的15种主策略，差值为集成年化减去独立新版年化，单位是百分点。正分数过滤对Ensemble等同于不筛选，因为百分位均值为正；它不是剔除未来亏损。过去4/13周亏损过滤、26周波动与趋势仍只用当时可知的价格。全部其他窗口、资金和成本见补充CSV。')
    pairs=pd.read_csv(OUT/'Ensemble_vs_Ranker150_common210.csv');pairs=pairs[pairs.window.isin(['FullHistory','FinalTest'])&pairs.capital.eq(100000)&pairs.cost_bps.eq(10)&~pairs.strategy.isin(['UniverseEqualWeight','Top5_WeeklyRoundTrip'])].copy();pairs['annualized_delta_pp']=pairs.annualized_return_ensemble_minus_ranker150*100
    table('ensemble-pair-table','Ensemble与独立新版：15策略×2窗口','ens_pairs',pairs,[('window','窗口',None),('strategy','策略',None),('annualized_return_ensemble','集成年化','percent'),('annualized_return_ranker150','独立新版年化','percent'),('annualized_delta_pp','差值（百分点）',None)])
    prose('ensemble-native-finding','## 2019年开始的366周完整历史单独保留',
        f'使用全部13,517条预测，Ensemble Top5年化{native5.annualized_return:.2%}、Sharpe{native5.sharpe:.3f}，Top10年化{native10.annualized_return:.2%}、Sharpe{native10.sharpe:.3f}。下面只比较同样拥有366周预测的Ensemble和三个子模型；不把独立模型尚未产生预测的训练期填成投资收益。早期较好的收益可能改变整体结果，因此必须同时查看上面的共同期和最终期。')
    chart('ensemble-native-nav','366周Top5净值：Ensemble及三个子模型','ens_native_nav',curve('Native366','FullHistory','Top5',['Ensemble','Model1','Model2','Model3']))
    md.append('![366周完整历史](charts/EnsembleSupplement/Native366/FullHistory_Top5.png)')
    prose('ensemble-native-table-note','## 集成体系完整历史指标', '这张表只覆盖2019年开始的366周、10万资金、单边10bps等权Top5。它与210周表的历史长度不同；期末资金以及年化差异不能全部归因于集成或独立模型结构。')
    nt=headline[headline.scope.eq('Native366')&headline.window.eq('FullHistory')&headline.strategy.eq('Top5')].copy();nb=row('Ensemble','Native366','FullHistory','UniverseEqualWeight').copy();nb['model']='Benchmark';nt=pd.concat([nt,pd.DataFrame([nb])],ignore_index=True);nt['model_label']=nt.model.map(sys_labels)
    table('ensemble-native-table','集成体系366周、10万、10bps：Top5','ens_native_models',nt,[('model_label','模型',None),('weeks','周数',None),('annualized_return','年化收益','percent'),('sharpe','Sharpe',None),('max_drawdown','最大回撤','percent')])
    prose('ensemble-prediction-note','## 排序评估与交易回报分别解读',
        '下面使用相同210周及最终51周的target1标签计算每周Rank IC，再对周取均值；ICIR是不年化的周IC均值除以样本标准差。交易回报来自买卖价格、整数股和现金，不能用IC替代年化收益。所有六模型的补充NDCG使用同一指数增益定义；原交接包使用sklearn线性增益，数值可能不同，原定义和原指标已保留在source目录，不能混为一个指标。','ensemble_prediction')
    pe=e[e.scope.eq('Common210')&e.window.isin(['FullHistory','FinalTest'])].copy();pe['model_label']=pe.model.map(sys_labels)
    table('ensemble-prediction-table','六模型在共同样本的排序质量','ens_prediction',pe,[('model_label','模型',None),('window','窗口',None),('mean_rank_ic','平均Rank IC',None),('rank_icir','ICIR',None),('positive_rank_ic_fraction','正IC周比例','percent')],source='ensemble_prediction')
    prose('ensemble-verification-note','## 补充回测已核验，原独立模型结果保留',
        f'新增Ensemble及三个子模型的两种时间口径，共{verification["added_cases"]:,}个情景，加上原两版2,856个情景，总计{len(s):,}个；其中共同样本8,568个、集成体系完整历史6,936个。调仓相位敏感性合计1,080组。它们包含重叠窗口，并非独立重复实验。\n\n'
        f'新增{verification["trade_orders"]:,}笔10bps交易和{verification["holdings"]:,}条持仓已经逐笔核对，并从现金流与股数重建开盘、收盘资金；全部指标独立复算，48组周末清仓参考与交付模拟一致。股数都是整数，现金不透支，新增最大金额算术误差约{verification["maximum_absolute_error"]:.3g}。原两版结果文件保持不变。\n\n'
        '限制仍然适用：价格是交付开收盘代理，没有独立验证复权、公司行动、实际成交、滑点与因子披露时点。下面保留原两版独立模型的完整分析、策略表及窗口结果，作为补充对照。')
    def source(id,label,table,filename,definitions):return dict(id=id,label=label,path='report_sources.sqlite',files=[filename],query=dict(engine='sqlite',language='sql',sql=f'SELECT * FROM {table}',tables_used=[table],description='共同210周与集成体系完整366周分别存储；图表初始资金100000、单边10bps；各窗口独立重跑',metric_definitions=definitions))
    sources=[source('ensemble_summary','六模型整数股结果','ensemble_strategy_comparison','ensemble_extension/results/all_models_strategy_comparison.csv',['年化=(末资金/初资金)^(52/周数)-1','Sharpe=周净收益均值/样本标准差×sqrt(52)，rf=0','scope Common210公平比较六模型；Native366比较集成体系完整历史']),source('ensemble_weekly','集成补充逐周资金','ensemble_weekly_chart','ensemble_extension/results/plot_weekly_100k10bps.csv.gz',['净值=期末资金/初始资金；首信号前7日的1为初始资金标记']),source('ensemble_prediction','六模型标签排序评估','ensemble_prediction_evaluation','ensemble_extension/results/all_models_prediction_evaluation.csv',['Rank IC为周内Spearman，周均值不按股票数加权','ICIR不年化；NDCG为指数增益，与原交接线性增益分别存储']),source('ensemble_audit','45个保存模型重放记录','ensemble_saved_model_audit','ensemble_extension/prepared/saved_model_replay_audit.csv',['每个保存模型只对其历史生效区间重放；原始分数误差0；三百分位均值构成Ensemble'])]
    oldblocks=m['blocks'][1:]
    for b in oldblocks:
        if b['id']=='summary':b['body']=b['body'].replace('## 评估结论','## 原独立两版比较（保留）').replace('本次已完成你','原部分已完成你')
        if b['id']=='robustness':b['body']=b['body'].replace('## 敏感性与可复核范围','## 原独立两版的敏感性与核验（保留）')
    m.update(title=title,blocks=[dict(id='title',type='markdown',body='# '+title)]+blocks+oldblocks,charts=charts+m['charts'],tables=tables+m['tables'],sources=sources+m['sources'],sourceBindings={'ensemble_summary':'ens_all','ensemble_weekly':'ens_common_nav','ensemble_prediction':'ens_prediction','ensemble_audit':'ens_audit','summary':'all_cases','prediction':'prediction'})
    datasets['ens_all']=records(s);datasets['ens_audit']=records(audit)
    base['package_info'].update(ensembleComplete=True,modelCount=6,datasetSources={'ens_all':'ensemble_summary','ens_audit':'ensemble_audit'})
    basefile.write_text(json.dumps(base,ensure_ascii=False,separators=(',',':')))
    tail=original_md.read_text();tail=tail[tail.find('\n\n')+2:];tail=tail.replace('## 评估结论','## 原独立两版比较（保留）',1)
    (BASE/'results/整数股回测报告.md').write_text('# '+title+'\n\n'+'\n\n'.join(md)+'\n\n'+tail)
    (OUT/'Ensemble补充评估回测报告.md').write_text('# Ensemble及三个子模型补充评估回测\n\n'+'\n\n'.join(md))
    (OUT/'report_source_notes.json').write_text(json.dumps(dict(artifact_id='preserved existing local report ID',source_audit='prepared/source_audit.json',verification=verification,comparison_scope='Common210 versus Native366 kept separate',ndcg_convention='exponential gain in supplemental six-model table; original linear-gain metrics retained',original_two_model_report='prepared/original_two_model_report.md',added_figures=len(list((OUT/'charts').rglob('*.png')))),ensure_ascii=False,indent=2))
    print('Extended existing report; scope six models; cases',len(s))
if __name__=='__main__':main()
