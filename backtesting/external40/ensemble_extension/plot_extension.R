args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else "evaluation_backtest/integer_model_comparison_20261022/ensemble_extension"
out <- file.path(root,"results"); charts <- file.path(out,"charts");dir.create(charts,showWarnings=FALSE)
w <- read.csv(gzfile(file.path(out,"plot_weekly_100k10bps.csv.gz")),stringsAsFactors=FALSE);w$date<-as.Date(w$date)
label <- c(Ensemble="Ensemble",Ranker150_New="Standalone new 150",Ranker50_Old="Standalone old 50",Model1="Component1: 156w / 5f",Model2="Component2: 52w / 2f",Model3="Component3: 52w / 5f",Benchmark="Pool equal-weight")
colors <- c(Ensemble="#4264AE",Ranker150_New="#CD9220",Ranker50_Old="#B5658E",Model1="#D47548",Model2="#8C924F",Model3="#71777F",Benchmark="#496874")
draw <- function(scope,window,strategy,models,file,dd=FALSE) {
  z <- w[w$scope==scope & w$window==window,]
  sets <- lapply(models,function(m) {if(m=="Benchmark") z[z$model=="Ensemble" & z$strategy=="UniverseEqualWeight",] else z[z$model==m & z$strategy==strategy,]})
  sets <- lapply(sets,function(g) g[order(g$date),]);stopifnot(all(sapply(sets,nrow)>0))
  n <- nrow(sets[[1]]); stopifnot(all(sapply(sets,nrow)==n))
  values <- lapply(sets,function(g) {nav<-c(1,g$end_capital/g$capital);if(dd) nav/cummax(nav)-1 else nav})
  png(file,width=1500,height=900,res=130,type="quartz")
  par(mar=c(7.6,4.5,4,1.2),mgp=c(2.7,.7,0),las=1,cex=.95)
  limits <- range(unlist(values),if(dd) 0 else 1);if(diff(limits)==0)limits<-limits+c(-.01,.01);limits<-limits+c(-1,1)*max(diff(limits)*.07,.01)
  plot(c(0,n),limits,type="n",xaxt="n",xlab="Signal week (initial value at step 0)",ylab=if(dd)"Drawdown" else "NAV (initial=1)",main=paste(scope,"|",window,"|",strategy,if(dd)"| Drawdown" else ""),bty="l",col.main="#202735")
  abline(h=pretty(limits),col="#E8EAF0",lwd=.7)
  ticks<-unique(round(seq(1,n,length.out=min(6,n))));axis(1,at=c(0,ticks),labels=c("Start",format(sets[[1]]$date[ticks],"%Y-%m-%d")),cex.axis=.8)
  for(i in seq_along(values))lines(0:n,values[[i]],col=colors[models[i]],lty=i,lwd=2)
  legend("bottomleft",inset=c(0,-.29),legend=unname(label[models]),col=colors[models],lty=seq_along(models),lwd=2,bty="n",ncol=3,cex=.82,xpd=NA)
  mtext("Capital 100000; 10bps each side; integer shares; supplied open/close proxies",side=3,line=.3,cex=.75,col="#5F6674")
  dev.off()
}
strategies<-setdiff(unique(w$strategy),"UniverseEqualWeight")
for(scope in c("Common210","Native366")) {
  folder<-file.path(charts,scope);dir.create(folder,showWarnings=FALSE)
  models<-if(scope=="Common210")c("Ensemble","Ranker150_New","Ranker50_Old","Benchmark")else c("Ensemble","Model1","Model2","Model3","Benchmark")
  for(window in unique(w$window[w$scope==scope]))for(strategy in strategies) {
    stem<-file.path(folder,paste0(window,"_",strategy))
    draw(scope,window,strategy,models,paste0(stem,".png"))
    if(window %in% c("FullHistory","FinalTest") && strategy %in% c("Top5","Top10","Top5_RankWeighted"))draw(scope,window,strategy,models,paste0(stem,"_drawdown.png"),dd=TRUE)
  }
}
for(window in c("FullHistory","FinalTest"))draw("Common210",window,"Top5",c("Ensemble","Model1","Model2","Model3","Benchmark"),file.path(charts,paste0("Common210_",window,"_components_Top5.png")))
s<-read.csv(file.path(out,"common210_strategy_comparison.csv"),stringsAsFactors=FALSE)
for(window in c("FullHistory","FinalTest")) {
  z<-s[s$window==window & s$capital==100000 & s$cost_bps==10,];models<-c("Ensemble","Ranker150_New","Ranker50_Old");selected<-c("Top5","Top10","Top5_RankWeighted")
  values<-sapply(selected,function(st)sapply(models,function(m)z$annualized_return[z$model==m & z$strategy==st]*100))
  baseline<-z$annualized_return[z$model=="Ensemble" & z$strategy=="UniverseEqualWeight"]*100
  png(file.path(out,paste0("Common210_",window,"_annualized_return.png")),width=1500,height=900,res=130,type="quartz");par(mar=c(6.5,5,5,1.5),las=1)
  limits<-range(c(values,baseline,0));limits<-limits+c(-1,1)*max(diff(limits)*.18,3)
  bars<-barplot(values,beside=TRUE,col=colors[models],border=NA,names.arg=c("Equal Top5","Equal Top10","Rank-weight Top5"),ylim=limits,ylab="Annualized net return (%)",main=paste("Common210 |",window,"| 100000 | 10bps"))
  abline(h=0,col="#5F6674");abline(h=baseline,col=colors["Benchmark"],lty=2,lwd=1.5)
  text(bars,values+ifelse(values>=0,1.5,-1.5),labels=paste0(formatC(values,format="f",digits=2),"%"),cex=.8)
  legend("bottomleft",inset=c(0,-.22),legend=label[models],fill=colors[models],bty="n",horiz=TRUE,xpd=NA)
  mtext(paste0("Dashed line: same-cost pool benchmark ",formatC(baseline,format="f",digits=2),"%"),side=3,line=.3,cex=.8)
  dev.off()
}
cat("Ensemble supplement line/drawdown figures:",length(list.files(charts,pattern=".png$",recursive=TRUE)),"\n")
