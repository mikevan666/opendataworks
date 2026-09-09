import test from "node:test";
import assert from "node:assert/strict";
import {
  resolveProviderProfile,
  resolveModel,
  ProviderNotSupportedError,
} from "../src/providers/stream-fn-resolver.js";

test("resolveProviderProfile resolves built-in providers including anyrouter", () => {
  const supported = [
    "anthropic",
    "anthropic_compatible",
    "anyrouter",
    "openai",
    "openai_compatible",
  ];
  for (const providerId of supported) {
    const profile = resolveProviderProfile(providerId);
    assert.ok(profile, `expected profile for ${providerId}`);
    assert.ok(profile.api, `expected api for ${providerId}`);
  }
});

test("resolveProviderProfile rejects unsupported provider", () => {
  assert.throws(
    () => resolveProviderProfile("unsupported_xyz"),
    (err: unknown) => {
      assert.ok(err instanceof ProviderNotSupportedError);
      assert.match(err.message, /unsupported_xyz/);
      assert.match(err.message, /anyrouter/);
      return true;
    }
  );
});

test("resolveModel builds model for anyrouter", () => {
  const anyrouterModel = resolveModel("anyrouter", "claude-opus-4-6");
  assert.equal(anyrouterModel.id, "claude-opus-4-6");
  assert.equal(anyrouterModel.provider, "anyrouter");
  assert.equal(anyrouterModel.api, "anthropic-messages");
});

// openrouter is deliberately absent: it needs Authorization: Bearer, which this
// resolver cannot express (it passes the token as apiKey -> x-api-key), and no
// authenticated end-to-end run has verified it. Register it only alongside a
// transport-level auth fix.
test("resolveProviderProfile rejects openrouter until Bearer auth is supported", () => {
  assert.throws(() => resolveProviderProfile("openrouter"), ProviderNotSupportedError);
});
