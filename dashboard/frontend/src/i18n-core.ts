import { english } from "./messages.ts";

export type Language = "zh" | "en";
export const LANGUAGE_KEY = "cs5_6_equity.language";
export function isLanguage(value: unknown): value is Language {
  return value === "zh" || value === "en";
}
export function chooseLanguage(search: string, saved: string | null): Language {
  const requested = new URLSearchParams(search).get("lang");
  return isLanguage(requested) ? requested : isLanguage(saved) ? saved : "zh";
}
export function translate(
  language: Language,
  text: string,
  values: Record<string, string | number> = {},
): string {
  // Browser network messages vary; render a consistent actionable UI message.
  const key = [
    "Failed to fetch",
    "Load failed",
    "NetworkError when attempting to fetch resource.",
  ].includes(text)
    ? "无法读取结果，请确认 Dashboard 服务正在运行。"
    : text;
  const template =
    language === "en" && Object.hasOwn(english, key) ? english[key] : key;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    Object.hasOwn(values, name) ? String(values[name]) : match,
  );
}
export function languageURL(url: string, language: Language): string {
  const result = new URL(url);
  result.searchParams.set("lang", language);
  return result.href;
}
