import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  chooseLanguage,
  LANGUAGE_KEY,
  languageURL,
  translate,
  type Language,
} from "./i18n-core";

type LanguageContext = {
  language: Language;
  setLanguage: (value: Language) => void;
};
const Context = createContext<LanguageContext | null>(null);
function initialLanguage(): Language {
  let saved = null;
  try {
    saved = localStorage.getItem(LANGUAGE_KEY);
  } catch {
    /* Storage may be blocked in an iframe. */
  }
  return chooseLanguage(window.location.search, saved);
}
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setValue] = useState<Language>(initialLanguage);
  useEffect(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    document.title = translate(language, "SafeCapital · 策略研究工作台");
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute(
        "content",
        translate(
          language,
          "SafeCapital 历史策略研究：真实模型排名、资金曲线与验证记录。",
        ),
      );
    try {
      localStorage.setItem(LANGUAGE_KEY, language);
    } catch {
      /* Switching still works without storage. */
    }
  }, [language]);
  const setLanguage = (value: Language) => {
    setValue(value);
    // Keep the selected language in shareable URLs without navigating or losing filters.
    window.history.replaceState(
      window.history.state,
      "",
      languageURL(window.location.href, value),
    );
  };
  return (
    <Context.Provider value={{ language, setLanguage }}>
      {children}
    </Context.Provider>
  );
}
export function useLanguage() {
  const context = useContext(Context);
  if (!context) throw new Error("LanguageProvider is required");
  return {
    ...context,
    t: (text: string, values?: Record<string, string | number>) =>
      translate(context.language, text, values),
  };
}
export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <div
      className="language-switch"
      role="group"
      aria-label={t("语言 / Language")}
    >
      <button
        lang="zh-CN"
        aria-pressed={language === "zh"}
        onClick={() => setLanguage("zh")}
      >
        中文
      </button>
      <button
        lang="en"
        aria-pressed={language === "en"}
        onClick={() => setLanguage("en")}
      >
        English
      </button>
    </div>
  );
}
