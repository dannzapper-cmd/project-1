/**
 * Block 10B — intake error classification tests.
 *
 * Run with:
 *   node --experimental-strip-types --test lib/intake/__tests__/intake-errors.test.ts
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { ApiError } from "../../api/client.ts";
import {
  describeIntakePreviewError,
  isBackendUnavailableError,
} from "../intake-errors.ts";

describe("isBackendUnavailableError", () => {
  it("treats TypeError as backend unavailable", () => {
    assert.equal(isBackendUnavailableError(new TypeError("Failed to fetch")), true);
  });

  it("treats 503 ApiError as backend unavailable", () => {
    const err = new ApiError("down", { status: 503, url: "http://x", body: "" });
    assert.equal(isBackendUnavailableError(err), true);
  });

  it("does not treat 422 ApiError as backend unavailable", () => {
    const err = new ApiError("bad", {
      status: 422,
      url: "http://x",
      body: "missing company_name",
    });
    assert.equal(isBackendUnavailableError(err), false);
  });
});

describe("describeIntakePreviewError", () => {
  it("returns backend-unavailable copy for network failures", () => {
    const message = describeIntakePreviewError(new TypeError("Failed to fetch"));
    assert.match(message, /Could not reach the LeadForge backend/);
    assert.match(message, /NEXT_PUBLIC_API_URL/);
  });

  it("preserves validation error detail for 422", () => {
    const err = new ApiError("bad", {
      status: 422,
      url: "http://x",
      body: "company_name is required",
    });
    const message = describeIntakePreviewError(err);
    assert.match(message, /422/);
    assert.match(message, /company_name is required/);
  });
});
