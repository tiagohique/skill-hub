import assert from "node:assert/strict";
import { test } from "node:test";
import { domainsOf, filterSkills } from "../src/skills.ts";

const SKILLS = [
  { name: "fastapi-endpoint", domain: "backend", owner: "a", stable: "1.0.0", beta: null, status: "stable" as const },
  { name: "html-landing-page", domain: "frontend", owner: "b", stable: "1.0.0", beta: "1.1.0", status: "stable" as const },
  { name: "Small-Team-Delegation", domain: "geral", owner: "c", stable: null, beta: null, status: "deprecated" as const },
  { name: "api-gateway", domain: "backend", owner: "d", stable: null, beta: "0.1.0", status: "beta" as const },
];

test("domainsOf: únicos e ordenados", () => {
  assert.deepEqual(domainsOf(SKILLS), ["backend", "frontend", "geral"]);
});

test("domainsOf: lista vazia", () => {
  assert.deepEqual(domainsOf([]), []);
});

test("filterSkills: 'todos' e busca vazia não filtram", () => {
  assert.equal(filterSkills(SKILLS, "", "todos").length, 4);
});

test("filterSkills: busca parcial sem diferenciar maiúsculas", () => {
  assert.deepEqual(
    filterSkills(SKILLS, "DELEGATION", "todos").map((s) => s.name),
    ["Small-Team-Delegation"],
  );
  assert.deepEqual(
    filterSkills(SKILLS, "api", "todos").map((s) => s.name),
    ["fastapi-endpoint", "api-gateway"],
  );
});

test("filterSkills: por domínio", () => {
  assert.deepEqual(
    filterSkills(SKILLS, "", "backend").map((s) => s.name),
    ["fastapi-endpoint", "api-gateway"],
  );
});

test("filterSkills: busca e domínio combinados", () => {
  assert.deepEqual(
    filterSkills(SKILLS, "gateway", "backend").map((s) => s.name),
    ["api-gateway"],
  );
  assert.deepEqual(filterSkills(SKILLS, "gateway", "frontend"), []);
});

test("filterSkills: espaços nas pontas são ignorados; só espaços não filtra", () => {
  assert.equal(filterSkills(SKILLS, "  html  ", "todos").length, 1);
  assert.equal(filterSkills(SKILLS, "   ", "todos").length, 4);
});

test("filterSkills: sem resultado", () => {
  assert.deepEqual(filterSkills(SKILLS, "zzz", "todos"), []);
});

test("filterSkills: por status", () => {
  const names = (status: string) => filterSkills(SKILLS, "", "todos", status).map((s) => s.name);
  assert.deepEqual(names("stable"), ["fastapi-endpoint", "html-landing-page"]);
  assert.deepEqual(names("beta"), ["api-gateway"]);
  assert.deepEqual(names("deprecated"), ["Small-Team-Delegation"]);
  assert.equal(names("todos").length, 4);
});

test("filterSkills: status sem argumento não filtra e combina com busca e domínio", () => {
  assert.equal(filterSkills(SKILLS, "", "todos").length, 4);
  assert.deepEqual(
    filterSkills(SKILLS, "api", "backend", "beta").map((s) => s.name),
    ["api-gateway"],
  );
  assert.deepEqual(filterSkills(SKILLS, "api", "backend", "deprecated"), []);
});
