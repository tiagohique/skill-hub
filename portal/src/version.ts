// Mesma regra do hub (semver 2.0.0, expressão oficial de semver.org).
export const SEMVER =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

export type VersionCheck =
  | { valid: true }
  | { valid: false; message: string; suggestion?: string };

/**
 * Valida a versão e, se estiver errada, diz o que corrigir. Nunca corrige sozinha:
 * a `suggestion` é só uma oferta, e só existe se o texto corrigido for semver válido.
 */
export function explainVersion(value: string): VersionCheck {
  if (SEMVER.test(value)) return { valid: true };

  // Correção simples: tira "v" do começo e pontos do fim; completa "maior.menor" com ".0".
  let candidate = value.replace(/^[vV]/, "").replace(/\.+$/, "");
  if (/^\d+\.\d+$/.test(candidate)) candidate += ".0";
  const suggestion = candidate !== value && SEMVER.test(candidate) ? candidate : undefined;

  let message: string;
  if (value === "") {
    message = "Informe a versão, por exemplo 1.0.0.";
  } else if (value.endsWith(".")) {
    message = "Remova o ponto final: a versão não termina com ponto.";
  } else if (/^[vV]/.test(value)) {
    message = 'Remova o "v" do começo: a versão começa direto pelo número.';
  } else if (/^\d+\.\d+$/.test(value)) {
    message = "Faltou o número do patch (o terceiro número), por exemplo 1.0.0.";
  } else {
    message = "Versão inválida. Use o formato maior.menor.patch, por exemplo 1.0.0.";
  }
  return suggestion ? { valid: false, message, suggestion } : { valid: false, message };
}
