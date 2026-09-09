import test from "node:test";
import assert from "node:assert/strict";
import {
  resolveProviderProfile,
  resolveModel,
  ProviderNotSupportedError,
} from "../src/providers/stream-fn-resolver.js";

test("resolveProviderProfile resolves built-in providers including anyrouter and openrouter", () => {
  const supported = [
    "anthropic",
    "anthropic_compatible",
    "anyrouter",
    "openrouter",
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
      assert.match(err.message, /openrouter/);
      return true;
    }
  );
});

test("resolveModel builds model for anyrouter and openrouter", () => {
  const anyrouterModel = resolveModel("anyrouter", "claude-opus-4-6");
  assert.equal(anyrouterModel.id, "claude-opus-4-6");
  assert.equal(anyrouterModel.provider, "anyrouter");
  assert.equal(anyrouterModel.api, "anthropic-messages");

  const openrouterModel = resolveModel("openrouter", "anthropic/claude-sonnet-4.5");
  assert.equal(openrouterModel.id, "anthropic/claude-sonnet-4.5");
  assert.equal(openrouterModel.provider, "openrouter");
  assert.equal(openrouterModel.api, "anthropic-messages");
});
