const storageKey = "cs5_6_equity.language";
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
let opened = false;
const copy = {
  en: {
    title: "CS5-6 · Integration preview",
    site: "CS5-6 INTEGRATION PREVIEW",
    back: "Standalone Dashboard ↗",
    heading: "A dedicated space for model-based research.",
    placement:
      "Proposed placement: add the entry below the Strategy Lab introduction, alongside the existing strategy options. This local preview demonstrates only the CS5-6 module.",
    module: "Model-Based Stock Strategies",
    description:
      "Explore model-selected stock portfolios and inspect their historical performance and risk.",
    open: "Explore strategies →",
    close: "Close module ↑",
    isolation:
      "The portfolio has its own stock universe. It does not use or modify a website-wide single-asset selector.",
    delivery:
      "This is a local integration example, not the client's live website. Authentication, global navigation and other strategies remain the responsibility of the core team. A client staging review is required before release.",
    frame: "CS5-6 historical stock research",
  },
  zh: {
    title: "CS5-6 · 接入预览",
    site: "CS5-6 接入预览",
    back: "独立 Dashboard ↗",
    heading: "为模型股票研究，提供独立入口。",
    placement:
      "建议在 Strategy Lab 介绍下方、现有策略选项旁新增此入口。本地示例只演示 CS5-6 模块。",
    module: "模型股票策略",
    description: "探索模型选出的股票组合，查看其历史表现与风险。",
    open: "查看策略 →",
    close: "收起模块 ↑",
    isolation: "组合使用独立股票池，不读取或修改网站全局的单资产选择器。",
    delivery:
      "这是本地接入示例，并非客户线上网站。登录认证、全局导航和其他策略由客户核心团队维护；上线前需要在客户测试环境中审核。",
    frame: "CS5-6 历史股票研究",
  },
};
function renderLanguage(value) {
  language = value;
  const c = copy[value];
  document.documentElement.lang = value === "en" ? "en" : "zh-CN";
  document.title = c.title;
  for (const [id, key] of Object.entries({
    "site-label": "site",
    "back-link": "back",
    "page-title": "heading",
    "placement-note": "placement",
    "module-title": "module",
    "module-description": "description",
    "isolation-note": "isolation",
    "delivery-note": "delivery",
  }))
    document.getElementById(id).textContent = c[key];
  document.getElementById("back-link").href = "./?lang=" + value;
  document.getElementById("open-module").textContent =
    c[opened ? "close" : "open"];
  document.getElementById("dashboard-frame").title = c.frame;
  const url = new URL(location.href);
  url.searchParams.set("lang", value);
  history.replaceState(history.state, "", url.href);
}
document.getElementById("open-module").addEventListener("click", () => {
  opened = !opened;
  document.getElementById("module-container").hidden = !opened;
  document
    .getElementById("open-module")
    .setAttribute("aria-expanded", String(opened));
  const frame = document.getElementById("dashboard-frame");
  if (opened && !frame.getAttribute("src"))
    frame.src = "./?embed=1&lang=" + language;
  renderLanguage(language);
});
renderLanguage(language);
// Same-origin language changes update the preview shell, without touching host-wide storage.
window.addEventListener("storage", (event) => {
  if (event.key === storageKey && ["zh", "en"].includes(event.newValue))
    renderLanguage(event.newValue);
});
