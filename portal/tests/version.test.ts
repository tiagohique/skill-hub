import assert from "node:assert/strict";
import { test } from "node:test";
import { explainVersion } from "../src/version.ts";

test("versões válidas", () => {
  for (const v of ["1.0.0", "0.1.0-beta.1", "1.2.3+b.5"]) {
    assert.deepEqual(explainVersion(v), { valid: true }, v);
  }
});

test("ponto final: explica e sugere sem o ponto", () => {
  const r = explainVersion("1.0.0.");
  assert.equal(r.valid, false);
  if (!r.valid) {
    assert.match(r.message, /ponto final/);
    assert.equal(r.suggestion, "1.0.0");
  }
});

test("prefixo v: sugere sem o v", () => {
  const r = explainVersion("v1.0.0");
  assert.equal(r.valid, false);
  if (!r.valid) {
    assert.match(r.message, /"v"/);
    assert.equal(r.suggestion, "1.0.0");
  }
});

test("faltou o patch: sugere completar", () => {
  const r = explainVersion("1.0");
  assert.equal(r.valid, false);
  if (!r.valid) {
    assert.match(r.message, /patch/);
    assert.equal(r.suggestion, "1.0.0");
  }
});

test("sem sugestão quando não há correção simples", () => {
  for (const v of ["01.0.0", "1.0.0.0", "", "abc"]) {
    const r = explainVersion(v);
    assert.equal(r.valid, false, v);
    if (!r.valid) {
      assert.ok(r.message.length > 0, v);
      assert.equal(r.suggestion, undefined, v);
    }
  }
});
