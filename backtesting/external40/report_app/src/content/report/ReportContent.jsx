import React from "react";
import {DataComponent,DataTable,EvidenceChart,ReportSection,RichNarrative,useDataApp} from "../../data-app-public.jsx";
import story from "./report-story.json";
const charts=Object.fromEntries(story.charts.map(c=>[c.id,c]));
const tables=Object.fromEntries(story.tables.map(t=>[t.id,t]));
function formatValue(value,percent){
  if(value===null||value===undefined)return "—";
  if(typeof value!=="number")return String(value);
  return percent?`${(value*100).toFixed(2)}%`:Number.isInteger(value)?String(value):value.toFixed(3);
}
export function ReportContent(){
  const {reviewedRows,visible,appTitle,setAppTitle,canEdit,mode}=useDataApp();
  function block(b){
    if(b.id==="title")return null;
    if(b.type==="markdown"){
      const q=story.sourceBindings?.[b.sourceId] ?? (b.sourceId==="prediction"?"prediction":b.sourceId==="summary"?"all_cases":null);
      const prose=<RichNarrative id={`${b.id}:body`} value={b.body} label="编辑报告正文"/>;
      return q?<ReportSection key={b.id} id={b.id} queryId={q} title={b.body.split("\n")[0].replace(/^#+ /,"")} sourceRows={reviewedRows(q)} showHeading={false}>{prose}</ReportSection>:<section key={b.id}>{prose}</section>;
    }
    if(b.type==="chart"){
      const c=charts[b.chartId];const sourceRows=reviewedRows(c.dataset);
      const isPercent=c.encodings.y.field==="annualized_return";
      const rows=isPercent?sourceRows.map(r=>({...r,"年化收益 (%)":r.annualized_return*100})):sourceRows;
      const spec={type:c.type,x:c.encodings.x.field,y:isPercent?"年化收益 (%)":c.encodings.y.field,series:c.encodings.color?.field,stackable:false,startAtZero:c.type==="bar",valueDecimals:3};
      return <EvidenceChart key={c.id} id={c.id} queryId={c.dataset} title={c.title} rows={rows} sourceRows={sourceRows} spec={spec} height={360}/>;
    }
    const t=tables[b.tableId];const rows=reviewedRows(t.dataset);
    const columns=t.columns.map(col=>({...col,renderCell:value=>formatValue(value,col.format==="percent")}));
    return visible(t.id)&&<DataComponent key={t.id} id={t.id} title={t.title} queryId={t.dataset} kind="table" sourceRows={rows} displayRows={rows}>
      <DataTable rows={rows} columns={columns} compactNumbers={false} searchable={rows.length>8} caption={t.title}/>
    </DataComponent>;
  }
  return <article className="report-content" aria-label="新旧模型整数股回测报告">
    <header className="report-hero"><h1 data-data-app-title contentEditable={canEdit&&mode==="edit"} suppressContentEditableWarning onBlur={canEdit&&mode==="edit"?e=>setAppTitle(e.currentTarget.textContent.trim()||appTitle):undefined}>{appTitle}</h1></header>
    {story.blocks.map(block)}
  </article>;
}
