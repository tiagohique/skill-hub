import assert from "node:assert/strict";
import { test } from "node:test";
import { otherTheme } from "../src/theme.ts";

test("otherTheme alterna entre claro e escuro", () => {
  assert.equal(otherTheme("dark"), "light");
  assert.equal(otherTheme("light"), "dark");
});
