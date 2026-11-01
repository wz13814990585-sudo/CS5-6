import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import ts from "typescript";
import { chooseLanguage, languageURL, translate } from "../src/i18n-core.ts";
import { english } from "../src/messages.ts";

test("URL overrides saved preference; unsupported values fall back safely", () => {
  assert.equal(chooseLanguage("?embed=1&lang=en", "zh"), "en");
  assert.equal(chooseLanguage("?lang=zh", "en"), "zh");
  assert.equal(chooseLanguage("?lang=fr", "en"), "en");
  assert.equal(chooseLanguage("", null), "zh");
  assert.equal(chooseLanguage("?lang=bad", "bad"), "zh");
});
test("language links retain embed mode, unrelated parameters and anchors", () => {
  const url = new URL(
    languageURL("https://research.example/?embed=1&x=2&lang=zh#inputs", "en"),
  );
  assert.equal(url.searchParams.get("lang"), "en");
  assert.equal(url.searchParams.get("embed"), "1");
  assert.equal(url.searchParams.get("x"), "2");
  assert.equal(url.hash, "#inputs");
});
test("formatted messages preserve counts, zero values and data identifiers", () => {
  assert.equal(
    translate("en", "共 {count} 条匹配输入 · 每页 10 条", { count: 0 }),
    "0 matching inputs · 10 per page",
  );
  assert.equal(
    translate("zh", "信号日期 {date}", { date: "2026-08-28" }),
    "信号日期 2026-08-28",
  );
  assert.equal(translate("en", "ANF"), "ANF");
  assert.equal(translate("en", "revenue_growth_yoy"), "revenue_growth_yoy");
});
test("translations retain all placeholders and contain no untranslated Chinese", () => {
  const placeholders = (s: string) =>
    [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
  for (const [key, value] of Object.entries(english)) {
    assert.deepEqual(placeholders(value), placeholders(key), key);
    assert.ok(value.length > 0, key);
    if (key !== "语言 / Language")
      assert.ok(!/\p{Script=Han}/u.test(value), key);
  }
});
test("all Chinese copy in the React screens has an English catalog entry", () => {
  for (const filename of ["main.tsx", "InputsPanel.tsx"]) {
    const source = fs.readFileSync(
      new URL(`../src/${filename}`, import.meta.url),
      "utf8",
    );
    const tree = ts.createSourceFile(
      filename,
      source,
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    );
    const visit = (node: ts.Node) => {
      if (ts.isStringLiteral(node) && /\p{Script=Han}/u.test(node.text))
        assert.ok(english[node.text], `${filename}: ${node.text}`);
      if (ts.isJsxText(node))
        assert.ok(
          !/\p{Script=Han}/u.test(node.text),
          `${filename}: unlocalized JSX`,
        );
      ts.forEachChild(node, visit);
    };
    visit(tree);
  }
});
test("backend labels, unavailable inputs and network failures render in either language", () => {
  assert.equal(translate("en", "本地历史回放"), "Local historical replay");
  assert.equal(translate("en", "模型因子输入"), "Model factor inputs");
  const message =
    "缺少与本次运行一致的输入文件，或输入校验未通过；输出仍可独立查看。";
  assert.match(
    translate("en", message),
    /Verified outputs are still available/,
  );
  assert.equal(translate("zh", message), message);
  assert.match(
    translate("en", "Failed to fetch"),
    /Check that the Dashboard service/,
  );
});
