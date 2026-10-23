args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[1] else "evaluation_backtest/integer_model_comparison_20261022"
out <- file.path(root, "results")
charts <- file.path(out, "charts")
dir.create(charts, showWarnings=FALSE)
weekly <- read.csv(gzfile(file.path(out,"weekly_nav.csv.gz")), stringsAsFactors=FALSE)
weekly$date <- as.Date(weekly$date)
main <- weekly[weekly$capital==100000 & weekly$cost_bps==10,]
groups <- list(
  Selection=c("Top5","Top10","Top5_RankWeighted","UniverseEqualWeight"),
  RiskTrend=c("Top5","Top5_LowVol26w","Top5_RankRisk26w","Top5_Trend26w","UniverseEqualWeight"),
  Rebalance=c("Top5","Top5_Buffer10","Top5_Rebalance2w","Top5_Rebalance4w","UniverseEqualWeight"),
  LossFilter=c("Top5","Top5_NoLoss4w","Top5_NoLoss13w","Top10_NoLoss4w","Top10_NoLoss13w"),
  ScoreFilter=c("Top5","Top10","Top5_PositiveScore","Top10_PositiveScore","UniverseEqualWeight")
)
labels <- c(Top5="Equal Top5",Top10="Equal Top10",Top5_RankWeighted="Rank-weight Top5",UniverseEqualWeight="Pool equal-weight",
            Top5_LowVol26w="Inverse-vol Top5",Top5_RankRisk26w="Rank-risk Top5",Top5_Trend26w="Trend26w Top5",
            Top5_Buffer10="Buffer10 Top5",Top5_Rebalance2w="Rebalance 2w",Top5_Rebalance4w="Rebalance 4w",
            Top5_NoLoss4w="Top5 no loss 4w",Top5_NoLoss13w="Top5 no loss 13w",Top10_NoLoss4w="Top10 no loss 4w",Top10_NoLoss13w="Top10 no loss 13w",
            Top5_PositiveScore="Positive-score Top5",Top10_PositiveScore="Positive-score Top10",Top5_WeeklyRoundTrip="Weekly closed Top5")
palette <- c("#4264AE", "#CD9220", "#D47548", "#8C924F", "#B5658E")
draw <- function(data, strategies, title, file, dd=FALSE, png=FALSE) {
  sets <- lapply(strategies, function(s) data[data$strategy==s,])
  sets <- lapply(sets,function(g) g[order(g$date),])
  stopifnot(all(sapply(sets,nrow)>0))
  n <- nrow(sets[[1]])
  values <- lapply(sets,function(g) {nav<-c(1,g$end_capital/g$capital); if(dd) nav/cummax(nav)-1 else nav})
  png(file,width=1500,height=900,res=130,type="quartz")
  par(mar=c(7.6,4.5,4,1.2),mgp=c(2.7,.7,0),las=1,cex=.95)
  limits <- range(unlist(values),if(dd) 0 else 1)
  if(diff(limits)==0) limits <- limits+c(-.01,.01)
  limits <- limits+c(-1,1)*max(diff(limits)*.07,.01)
  plot(c(0,n),limits,type="n",xaxt="n",xlab="Signal week (initial value at step 0)",ylab=if(dd) "Drawdown" else "NAV (initial=1)",main=title,col.main="#202735",font.main=2,bty="l")
  abline(h=pretty(limits),col="#E8EAF0",lwd=.7)
  ticks <- unique(round(seq(1,n,length.out=min(6,n))))
  axis(1,at=c(0,ticks),labels=c("Start",format(sets[[1]]$date[ticks],"%Y-%m-%d")),cex.axis=.8)
  for(i in seq_along(values)) lines(0:n,values[[i]],col=palette[i],lwd=2,lty=c(1,2,3,4,5)[i])
  par(xpd=NA)
  legend("bottomleft",inset=c(0,-.28),legend=unname(labels[strategies]),col=palette[seq_along(strategies)],lty=seq_along(strategies),lwd=2,bty="n",ncol=3,cex=.82)
  mtext("Integer shares; fees both sides; next-open/close price proxies; same currency units",side=3,line=.3,cex=.75,col="#5F6674")
  dev.off()
}
for(model in c("Ranker150_New","Ranker50_Old")) {
model_charts <- if(model=="Ranker150_New") charts else file.path(charts,"Old50")
dir.create(model_charts,showWarnings=FALSE)
for(window in unique(main$window)) {
  data <- main[main$window==window & main$model==model,]
  for(group in names(groups)) {
    stem <- paste(window,group,sep="_")
    draw(data,groups[[group]],paste(model,"|",window,"| 100000 | 10bps"),file.path(model_charts,paste0(stem,".png")))
    if(window %in% c("FullHistory","FinalTest") && group %in% c("Selection","Rebalance")) {
      draw(data,groups[[group]],paste(model,"| Drawdown |",window),file.path(model_charts,paste0(stem,"_drawdown.png")),dd=TRUE)
    }
  }
}
for(window in c("FullHistory","FinalTest")) {
  for(capital in c(100000,10000)) {
    data <- weekly[weekly$window==window & weekly$capital==capital & weekly$cost_bps==10 & weekly$model==model,]
    draw(data,c("Top5","Top5_WeeklyRoundTrip","UniverseEqualWeight"),paste(model,"| Entry/exit rules |",window,"| capital",capital),file.path(model_charts,paste0(window,"_Execution_",capital,".png")))
  }
}
}
comparison <- file.path(charts,"ModelComparison")
dir.create(comparison,showWarnings=FALSE)
labels <- c(labels, New="New: 150 trees", Old="Old: 50 trees")
strategies <- unique(main$strategy)
strategies <- strategies[strategies!="UniverseEqualWeight"]
for(window in unique(main$window)) {
  for(strategy in strategies) {
    selected <- main[main$window==window & main$strategy==strategy,]
    selected$strategy <- ifelse(selected$model=="Ranker150_New","New","Old")
    baseline <- main[main$window==window & main$strategy=="UniverseEqualWeight" & main$model=="Ranker150_New",]
    d <- rbind(selected,baseline)
    stem <- paste(window,strategy,sep="_")
    draw(d,c("New","Old","UniverseEqualWeight"),paste("New vs old |",window,"|",strategy,"| 100000 | 10bps"),file.path(comparison,paste0(stem,".png")))
    if(window %in% c("FullHistory","FinalTest") & strategy %in% c("Top5","Top10","Top5_RankWeighted"))
      draw(d,c("New","Old","UniverseEqualWeight"),paste("New vs old drawdown |",window,"|",strategy),file.path(comparison,paste0(stem,"_drawdown.png")),dd=TRUE)
  }
}
cat("PNG charts:",length(list.files(charts,pattern=".png$",recursive=TRUE)),"\n")
summary <- read.csv(file.path(out,"strategy_comparison.csv"),stringsAsFactors=FALSE)
picked <- summary[summary$window=="FinalTest" & summary$capital==100000 & summary$cost_bps==10,]
selected <- c("Top5","Top10","Top5_RankWeighted")
values <- sapply(selected,function(strategy) sapply(c("Ranker150_New","Ranker50_Old"),function(model) picked$annualized_return[picked$strategy==strategy & picked$model==model]*100))
png(file.path(out,"FinalTest_annualized_return.png"),width=1500,height=900,res=130,type="quartz")
par(mar=c(6,5,5,1.5),las=1)
bars <- barplot(values,beside=TRUE,col=palette[1:2],border=NA,names.arg=unname(labels[selected]),ylim=c(min(values)*1.2,3),ylab="Annualized net return (%)",main="Final 51 weeks | new vs old | 100000 | 10bps")
abline(h=0,col="#5F6674")
text(bars,values-1.5,labels=paste0(formatC(values,format="f",digits=2),"%"),cex=.9)
legend("bottomleft",inset=c(0,-.22),legend=c("New: 150 trees","Old: 50 trees"),fill=palette[1:2],bty="n",horiz=TRUE,xpd=NA)
dev.off()
