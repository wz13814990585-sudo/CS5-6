"""Source-backed new/old comparison report and portable Markdown companion."""
from pathlib import Path
import json,sqlite3
import pandas as pd

HERE=Path(__file__).resolve().parent;OUT=HERE/'results'
LABELS={'Top5':'等权Top5','Top10':'等权Top10','Top5_RankWeighted':'排名加权Top5','Top5_LowVol26w':'低波动Top5','Top5_RankRisk26w':'排名风险Top5','Top5_Buffer10':'前10保留缓冲','Top5_Rebalance2w':'2周调仓Top5','Top5_Rebalance4w':'4周调仓Top5','Top5_Trend26w':'趋势过滤Top5','Top5_NoLoss4w':'Top5过去4周非亏损','Top10_NoLoss4w':'Top10过去4周非亏损','Top5_NoLoss13w':'Top5过去13周非亏损','Top10_NoLoss13w':'Top10过去13周非亏损','Top5_PositiveScore':'正分数Top5','Top10_PositiveScore':'正分数Top10','UniverseEqualWeight':'股票池等权对照','Top5_WeeklyRoundTrip':'每周清仓Top5对照'}
VERSIONS={'Ranker150_New':'新版150树','Ranker50_Old':'旧版50树'}
def data(df):return json.loads(df.to_json(orient='records',date_format='iso',double_precision=12))
def main():
    c=sqlite3.connect(OUT/'report_sources.sqlite')
    for file,table in [('strategy_comparison.csv','strategy_comparison'),('weekly_nav.csv.gz','weekly_nav'),('phase_sensitivity.csv','phase_sensitivity'),('prediction_evaluation.csv','prediction_evaluation'),('new_vs_old_comparison.csv','new_vs_old_comparison')]:
        pd.read_csv(OUT/file).to_sql(table,c,if_exists='replace',index=False)
    s=pd.read_sql_query('SELECT * FROM strategy_comparison',c)
    w=pd.read_sql_query('SELECT * FROM weekly_nav WHERE capital=100000 AND cost_bps=10',c,parse_dates=['date'])
    e=pd.read_sql_query('SELECT * FROM prediction_evaluation',c)
    v=json.loads((OUT/'verification.json').read_text())
    assert v['status']=='passed' and v['both_models_evaluated']
    title='新旧版XGBRanker：整数股回测与模型评估'
    blocks=[];charts=[];tables=[];md=[];datasets={}
    def text(id,heading,body,source=None):
        value=(heading+'\n\n'+body) if heading else body
        b=dict(id=id,type='markdown',body=value)
        if source:b['sourceId']=source
        blocks.append(b);md.append(value)
    def table(id,title,dataset,frame,cols,sort='annualized_return',source='summary'):
        datasets[dataset]=data(frame)
        tables.append(dict(id=id,title=title,dataset=dataset,sourceId=source,layout='full',defaultSort=dict(field=sort,direction='desc'),columns=[dict(field=f,label=l,**({'format':fmt} if fmt else {})) for f,l,fmt in cols]))
        blocks.append(dict(id=id+'-block',type='table',tableId=id))
        def fmt(x,f):return f'{x:.2%}' if f=='percent' else f'{x:.3f}' if isinstance(x,float) else str(x)
        md.append('### '+title+'\n\n| '+' | '.join(l for _,l,_ in cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(fmt(row[f],form) for f,_,form in cols)+' |' for _,row in frame.iterrows()))
    def chart(id,title,dataset,frame,x,y,source='weekly',kind='line',group=None):
        datasets[dataset]=data(frame)
        z=dict(id=id,title=title,dataset=dataset,sourceId=source,type=kind,layout='full',question=title,encodings=dict(x=dict(field=x,type='temporal' if x=='date' else 'nominal'),y=dict(field=y,type='quantitative')))
        if y=='annualized_return':z['valueFormat']='percent';z['encodings']['y']['format']='percent'
        if group:z['encodings']['color']=dict(field=group,type='nominal');z['palette']=dict(kind='categorical')
        charts.append(z);blocks.append(dict(id=id+'-block',type='chart',chartId=id))
    def curve(window,strategy):
        z=w[w.window.eq(window)&(w.strategy.eq(strategy)|(w.strategy.eq('UniverseEqualWeight')&w.model.eq('Ranker150_New')))].copy()
        z['nav']=z.end_capital/z.capital
        z['label']=[('股票池等权对照' if st=='UniverseEqualWeight' else VERSIONS[m]) for m,st in zip(z.model,z.strategy)]
        # Include the initial unit NAV explicitly, preserving the initial loss.
        initial=[]
        for label,g in z.groupby('label'):
            row=g.sort_values('date').iloc[0].copy();row['date']-=pd.Timedelta(days=7);row['nav']=1.;row['end_capital']=row['capital'];row['net_return']=0.;row['fees']=0.;row['cash_ratio']=1.;row['holdings']=0;row['shares']=0;initial.append(row)
        z=pd.concat([z,pd.DataFrame(initial)],ignore_index=True).sort_values(['label','date'])
        return z[['date','model','strategy','label','capital','cost_bps','nav','end_capital','net_return','cash_ratio','holdings','shares','fees']]
    def source(id,label,table,sql,defs):return dict(id=id,label=label,path='report_sources.sqlite',query=dict(engine='sqlite',language='sql',sql=sql,tables_used=[table],description=label,metric_definitions=defs))
    sources=[source('summary','两版全部整数股回测结果','strategy_comparison','SELECT * FROM strategy_comparison',['年化收益=(期末资金/初始资金)^(52/周数)-1','Sharpe=周净收益均值/样本标准差×sqrt(52)，无风险利率0','最大回撤包含初始资金，窗口末全部清仓计费']),source('weekly','10万资金、单边10bps逐周资金路径','weekly_nav','SELECT * FROM weekly_nav WHERE capital=100000 AND cost_bps=10',['净值=期末资金/初始资金；图中首个点为首信号前7日的初始净值标记，非已验证成交日期']),source('prediction','使用target1标签的排序质量','prediction_evaluation','SELECT * FROM prediction_evaluation',['Rank IC=每周预测与target1的Spearman相关再取均值','ICIR=周Rank IC均值/样本标准差，不年化','NDCG@5使用每周真实收益0至4档相关性；与实际交易盈亏分别处理'])]
    main=s[s.capital.eq(100000)&s.cost_bps.eq(10)].copy();main['version']=main.model.map(VERSIONS);main['strategy_label']=main.strategy.map(LABELS);main['label']=main.version+' · '+main.strategy_label
    full=main[main.window.eq('FullHistory')].copy();final=main[main.window.eq('FinalTest')].copy()
    commoncols=[('version','版本',None),('strategy_label','策略',None),('annualized_return','年化收益','percent'),('sharpe','Sharpe',None),('max_drawdown','最大回撤','percent')]
    text('title',None,'# '+title)
    text('summary','## 评估结论',
        '**本次已完成新旧两版对比。** 最新model_only交接包为150棵树，之前独立模型为50棵树；两版均为五因子XGBRanker。两版使用相同40只外部股票、8,354条预测和210个信号周（2022年8月26日至2026年8月28日）。\n\n'
        '**新版没有表现出全面改进。** 初始资金100,000、单边10bps时，完整期等权Top5：新版年化−6.26%、Sharpe−0.10，旧版年化2.82%、Sharpe0.24。共同股票池等权对照年化7.70%，两版Top5都落后于对照。\n\n'
        '**最后51周两版15种主策略均为负年化。** 新版Top10年化−1.58%，较旧版−7.18%损失小；新版排名加权Top5年化−41.88%，旧版−36.59%。增加树数并未在所有策略、时间窗口中产生一致改善，不据此认定新版稳定优于旧版。','summary')
    text('models','## 版本、样本与预测评估',
        '新旧模型都使用收入增长、经营盈利能力、现金流/资产、负债/资产、资产增长五因子，输入先按每周横截面转换为百分位排名。训练股票池共66只，与外部40只不重叠；使用312周训练窗口，每26周更新一次。两版深度均为2，最小子节点权重均为5；新版150树，旧版50树。\n\n'
        '新版直接加载9个已保存模型，重放排名与交付结果完全一致，最大分数差约5.71×10⁻⁹。旧版按冻结50树参数重跑9次滚动拟合，8,354条分数与上次冻结预测逐条完全一致；未重新选参。日期与股票键逐条一致，价格取同一份输入。\n\n'
        '原始外部数据从2015年9月开始，但它不等于有预测的交易区间。312周训练历史及交付模型的首个更新日期决定本次只能从2022年8月26日回测；没有把训练期补成样本外投资收益。\n\n'
        '模型排序质量使用target1下一周收盘到收盘对数收益标签；交易收益使用另列buy_price/sell_price，两者分别评估。完整期平均Rank IC：新版0.0062，旧版0.0199；最后51周分别0.0267、0.0504。数值为逐周Spearman相关的均值，靠近0表示整体排序关系较弱；不能直接解释为收益率。','prediction')
    ep=e[e.window.isin(['FullHistory','FinalTest'])].copy();ep['version']=ep.model.map(VERSIONS)
    table('prediction-table','两版排序质量：完整期与最终期','prediction',ep,[('version','版本',None),('window','窗口',None),('weeks','周数',None),('mean_rank_ic','平均Rank IC',None),('rank_icir','ICIR',None),('positive_rank_ic_fraction','正IC周比例','percent'),('mean_ndcg_at5','NDCG@5',None)],sort='mean_rank_ic',source='prediction')
    text('method','## 整数股执行与指标口径',
        '每个窗口从全现金独立重跑。主情景100,000，另做10,000敏感性分析；资金单位与股票报价相同，不做外汇换算，也不标为AUD。每笔交易取整股数，现金保留，不融资、不购买小数股。\n\n'
        '目标股数=floor(目标权重×开盘资产÷[买价×(1+买入费率)])。先卖出超出目标的股数，再依固定排名顺序买入；现金不足继续向下取整，余额不重新分配。分配2,000、股价300时买6股，零费用剩200；10bps买入后剩198.20，若原价卖出，最终1,996.40。\n\n'
        '使用下一周首交易日开盘价代理调仓、下一周末收盘价代理估值，连续持股包含跨周价格变化。不调仓周保留实际股数，窗口末全部卖出计费。买卖双方按实际成交额各收费；0/10/25bps均重新模拟，费用会改变可买股数。\n\n'
        '年化收益=(期末/期初)^(52/周数)−1；年化波动=周净收益样本标准差×√52；Sharpe=周净收益均值/样本标准差×√52，无风险利率0；最大回撤从初始资金开始计算。负复利年化与微正算术Sharpe可能同时出现。')
    text('full-finding','## 完整210周：旧版Top5的结果较好',
        '新版Top5期末资金77,011.69，最大回撤55.27%；旧版111,873.67，最大回撤37.69%。下图固定比较同一Top5策略，第三条线是相同整数股及成本规则的股票池等权。各线从净值1开始，首个日期点是初始资金标记，横轴主体为信号周。完整期更好并不意味着旧版能够在未来持续获利。','summary')
    chart('full-nav','新旧版Top5完整期净值：10万、单边10bps','full_nav',curve('FullHistory','Top5'),'date','nav',group='label')
    md.append('![新旧版Top5完整期净值](charts/ModelComparison/FullHistory_Top5.png)')
    text('full-table-note',None,'下表保留两版全部15种主策略和2种对照。股票池等权在两版行中完全相同，它是共同基准，不是第三个学习模型。','summary')
    table('full-table','完整期各版本、各策略指标','full',full,commoncols)
    text('final-finding','## 最后51周：改善取决于策略',
        '最终期采用2025年9月5日至2026年8月21日，共51个信号周。Top5新版年化−14.29%、旧版−12.32%，两版均亏损。下面的Top10曲线用于展示策略差异：新版−1.58%、旧版−7.18%，共同对照−7.32%；这并不能抵消完整期Top5的退步。','summary')
    chart('final-nav','新旧版Top10最终期净值：10万、单边10bps','final_nav',curve('FinalTest','Top10'),'date','nav',group='label')
    md.append('![新旧版Top10最终期净值](charts/ModelComparison/FinalTest_Top10.png)')
    text('bar-note',None,'下面按固定的等权Top5、等权Top10和排名加权Top5比较最终期年化。三组均包含负值；排名加权将更多资金集中在前列股票，本次最终期使两版损失扩大，不能把排名高当作确定收益高。','summary')
    bar=final[final.strategy.isin(['Top5','Top10','Top5_RankWeighted'])]
    chart('final-returns','最终期代表策略年化收益：新旧版','final_bar',bar,'strategy_label','annualized_return',source='summary',kind='bar',group='version')
    md.append('![最终期各策略年化收益](FinalTest_annualized_return.png)')
    text('final-table-note',None,'完整表中两版15种主策略均为负年化。正分数过滤与Top5/Top10在这些样本中相同；Ranker正分数不等于预期回报为正，不能把该规则解释为提前识别未来亏损。','summary')
    table('final-table','最终期各版本、各策略指标','final',final,commoncols)
    text('strategies','## 策略规则与不同窗口',
        '15种主策略为：等权Top5/Top10、正分数Top5/Top10、过去4周非亏损Top5/Top10、过去13周非亏损Top5/Top10、排名加权Top5、低波动Top5、排名风险Top5、前10保留缓冲、每2周调仓、每4周调仓、26周趋势过滤。另有股票池等权和原脚本每周清仓Top5两种对照。\n\n'
        '排名加权按5:4:3:2:1分配；低波动按过去26周波动率倒数分配，排名风险再乘排名权重，两类风险加权单股上限35%。亏损过滤只看过去4/13周已知价格变化；趋势过滤在过去26周等权指数高于其均线时参与。缺少合格股票的预算保留现金。缓冲策略保留仍在前10的持仓，再补足5只，按周调整目标股数。\n\n'
        '2/4周策略在非调仓周保留实际股数，包含跨周跳空；每个窗口重新初始化计时。原交付模拟则每周开盘买、周末全卖，周末持现金，两类执行暴露不同，因此分开展示。两版共12组资金/费用的每周清仓路径均与交付模拟函数一致。\n\n'
        '14个窗口包含完整期、最近13/26/52/104/156周、2022至2026各自然年、Development、Validation和Final Test。自然年首末可能不完整，最近窗口彼此重叠；不能把这些结果当成独立重复验证。','summary')
    cases=main[main.strategy.eq('Top5')].copy()
    table('windows-table','两版Top5各窗口指标：10万、10bps','windows',cases,[('version','版本',None),('window','窗口',None),('weeks','周数',None),('annualized_return','年化收益','percent'),('sharpe','Sharpe',None),('max_drawdown','最大回撤','percent')],sort='weeks')
    text('robustness','## 敏感性与可复核范围',
        '共完成2版×17规则×14窗口×2资金×3费用=2,856组情景，其中主策略2,520组、两种对照336组。另有2/4周调仓在完整期、验证期和最终期的216组相位情景；主结果采用固定相位0，没有挑最优起点。\n\n'
        f'按订单独立重建全部10bps资金路径，并核查所有情景的年化收益、Sharpe和回撤。{v["checks"]:,}项数值核对通过，最大资金算术误差约{v["maximum_absolute_error"]:.3g}；股数全部为整数，现金不透支。加入旧版后，新版原有1,428组结果保持不变。386张PNG包含两版各窗口分组策略图、逐策略新旧对比及回撤图；完整逐周数据可自行重新绘图。\n\n'
        '10,000资金不能简单由100,000结果缩放，因为整股约束改变持仓。两版在每个资金与费用情景分别重算，共同股票池对照的资金路径完全一致。','summary')
    text('limits','## 结论边界与后续验证',
        '这些是基于交付数据的历史模拟。买卖价为文件定义的开收盘代理，尚未独立确认复权、分红拆股、成交可得性和最后一行的实际交易日期；费用情景不涵盖真实滑点、冲击成本与容量。每周可用38–40只外部股票，股票池选择与存活偏差仍可能影响解释。\n\n'
        '历史标签收益与实际价差存在定义差异，本报告没有混用。所有过滤只使用信号时已知的前序价格；但是否满足真实披露时点，还取决于原五因子数据的发布时间定义。Final Test结果已被查看，只作为固定历史区间，不能继续称为未见测试。\n\n'
        '**当前证据支持保留两版对照并继续验证，不能认定新版普遍更优。** 下一步应先确认代理价格与公司行动，再冻结模型及策略，在未查看的新时间段做前推模拟；重点观察Top5/Top10的基准超额、回撤及费用敏感性，避免根据本次结果反复调整参数后仍称样本外。')
    payload=dict(surface='report',manifest=dict(version=1,surface='report',title=title,generatedAt='2026-10-22T00:00:00+11:00',sources=sources,blocks=blocks,charts=charts,tables=tables),snapshot=dict(version=1,status='ready',generatedAt='2026-10-22T00:00:00+11:00',datasets=datasets),package_info=dict(bothModelsComplete=True,newModel='150 trees, saved models',oldModel='50 trees, previous frozen predictions',integerShares=True))
    (OUT/'artifact.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
    (OUT/'整数股回测报告.md').write_text('\n\n'.join(md),encoding='utf-8')
    top=w[w.window.eq('FullHistory')&w.strategy.eq('Top5')];top.to_csv(OUT/'Top5_逐周资金.csv',index=False)
    trades=pd.read_csv(OUT/'trade_ledger_10bps.csv.gz',parse_dates=['date'])
    trades[trades.window.eq('FullHistory')&trades.strategy.eq('Top5')&trades.capital.eq(100000)].to_csv(OUT/'Top5_逐笔整数股交易.csv',index=False)
    pd.DataFrame([dict(budget=2000,price=300,cost_bps=0,shares=6,buy_amount=1800,buy_fee=0,cash_after_buy=200),dict(budget=2000,price=300,cost_bps=10,shares=6,buy_amount=1800,buy_fee=1.8,cash_after_buy=198.2)]).to_csv(OUT/'整数股示例.csv',index=False)
    notes=dict(surface='mcp-app plus requested PNG line-chart files and portable Markdown',audience='technical',scope='both standalone versions',version_mapping=VERSIONS,source_model_assumption='latest model_only package is new, prior standalone handoff is old, as clarified by user',chart_map=[dict(segment='完整期',family='line',fields=['signal week','NAV','version'],claim='Top5 comparison'),dict(segment='最终期',family='line',fields=['signal week','NAV','version'],claim='Top10 strategy contrast'),dict(segment='最终期',family='grouped bar',fields=['strategy','CAGR','version'],claim='strategy-specific changes')],static_chart_renderer='R PNG via Quartz',line_repetition='用户明确要求不同窗口和策略折线图',confidence='share with stated proxy-price and historical-selection caveats',open_questions=['代理价格复权与成交含义','因子真实披露时点','新的未见前推区间'],verification=v)
    (OUT/'report_source_notes.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2))
    key=main[['version','window','strategy_label','weeks','first_signal','last_signal','capital','cost_bps','annualized_return','sharpe','max_drawdown','total_return','volatility','total_fees','final_capital','mean_cash_ratio']].copy()
    for field in ['annualized_return','max_drawdown','total_return','volatility','mean_cash_ratio']:
        key[field]=key[field].map(lambda x:f'{x:.4%}')
    key.columns=['模型版本','窗口','策略','周数','首信号日','末信号日','初始资金_报价同币种','单边费用bps','年化收益','Sharpe','最大回撤_有符号','累计收益','年化波动','总手续费','期末资金','平均现金比例']
    key.to_csv(OUT/'重点指标_10万10bps.csv',index=False,encoding='utf-8-sig',float_format='%.8g')
    print('Report ready',len(json.dumps(payload,ensure_ascii=False)),{k:len(a) for k,a in datasets.items()})
if __name__=='__main__':main()
