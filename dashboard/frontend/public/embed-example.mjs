const storageKey = "safecapital.language";
let saved;
try {
  saved = localStorage.getItem(storageKey);
} catch {}
const queryLanguage = new URLSearchParams(location.search).get("lang");
let language = ["zh", "en"].includes(queryLanguage)
  ? queryLanguage
  : saved === "en"
    ? "en"
    : "zh";
function renderLanguage(value, initial = false) {
  language = value;
  const english = value === "en";
  document.documentElement.lang = english ? "en" : "zh-CN";
  document.title = english
    ? "Client website · SafeCapital embedding example"
    : "客户网站 · SafeCapital 嵌入示例";
  document.getElementById("site-label").textContent = english
    ? "Client website · Demo shell"
    : "客户网站 · 演示外壳";
  document.getElementById("back-link").textContent = english
    ? "Back to standalone Dashboard"
    : "返回独立 Dashboard";
  document.getElementById("back-link").href = "./?lang=" + value;
  document.getElementById("module-title").textContent = english
    ? "Investment research module"
    : "投资研究模块";
  document.getElementById("module-description").textContent = english
    ? "This is the SafeCapital Dashboard embedded in an iframe. This example shares the Dashboard's origin; configure the client origin for cross-origin integration. Scroll, filter dates and download results inside the frame."
    : "下面是真正通过 iframe 嵌入的 SafeCapital 页面。此示例与 Dashboard 同源；跨域接入时请配置客户域名白名单。框内可以独立滚动、筛选日期和下载结果。";
  const frame = document.getElementById("dashboard-frame");
  frame.title = english
    ? "SafeCapital historical strategy research"
    : "SafeCapital 历史策略研究";
  if (initial) frame.src = "./?embed=1&lang=" + value;
  const url = new URL(location.href);
  url.searchParams.set("lang", value);
  history.replaceState(history.state, "", url.href);
}
renderLanguage(language, true);
// Same-origin iframe language changes update the shell without reloading the frame.
window.addEventListener("storage", (event) => {
  if (event.key === storageKey && ["zh", "en"].includes(event.newValue))
    renderLanguage(event.newValue);
});
