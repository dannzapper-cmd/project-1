/**
 * Block 10G — `postAssistantLeadQuestion` client unit tests.
 *
 * Run with the project's existing Node-test pattern:
 *   node --experimental-strip-types --test lib/api/__tests__/assistant-client.test.ts
 *
 * No real backend or Groq request is ever issued — `fetchImpl` is
 * injected so the request/response shapes can be asserted directly.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { ApiError, postAssistantLeadQuestion } from "../client.ts";
import type {
  AssistantRequest,
  AssistantResponse,
} from "../types.ts";

function fakeOkResponse(): AssistantResponse {
  return {
    status: "ok",
    mode: "live_llm",
    answer:
      "Acme Corp is high priority because of EMEA expansion and aligned sales angle.",
    grounding_summary:
      "Grounded in: company_name, fit_score, priority, fit_reasons.",
    used_context_fields: [
      "company_name",
      "fit_score",
      "priority",
      "fit_reasons",
    ],
    unsupported_claims_blocked: false,
    context_truncated: false,
    warnings: [],
    provider: "groq",
    model: "llama-3.1-8b-instant",
    estimated_tokens: 240,
    estimated_cost_usd: 0.0001,
    user_message: "Answer grounded in this lead's available context.",
  };
}

function exampleRequest(): AssistantRequest {
  return {
    question: "Why is this lead high priority?",
    lead: {
      company_name: "Acme Corp",
      fit_score: 78,
      priority: "High",
      fit_reasons: ["EMEA expansion announced"],
    },
  };
}

describe("postAssistantLeadQuestion", () => {
  it("posts the request body to /api/assistant/lead-question", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;

    const fakeFetch = (async (url: string, init?: RequestInit) => {
      capturedUrl = url;
      capturedInit = init;
      return new Response(JSON.stringify(fakeOkResponse()), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }) as unknown as typeof fetch;

    const response = await postAssistantLeadQuestion(exampleRequest(), {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(capturedUrl, "https://api.test/api/assistant/lead-question");
    assert.equal(capturedInit?.method, "POST");
    assert.equal(response.status, "ok");
    assert.equal(response.mode, "live_llm");
    assert.equal(response.used_context_fields.length, 4);
  });

  it("parses disabled / rate-limited responses without throwing", async () => {
    const disabledBody: AssistantResponse = {
      ...fakeOkResponse(),
      status: "disabled",
      mode: "off",
      answer:
        "The live assistant is currently off. Use the guided review questions for grounded answers from this lead's context.",
      provider: null,
      model: null,
      estimated_tokens: null,
      estimated_cost_usd: null,
      warnings: ["ENABLE_LLM_ASSISTANT is not enabled on this backend."],
      user_message:
        "Live assistant is disabled. You can still use the guided review questions.",
    };

    const fakeFetch = (async () =>
      new Response(JSON.stringify(disabledBody), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })) as unknown as typeof fetch;

    const response = await postAssistantLeadQuestion(exampleRequest(), {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(response.status, "disabled");
    assert.equal(response.mode, "off");
    assert.equal(response.provider, null);
    assert.equal(response.estimated_tokens, null);
  });

  it("throws ApiError on non-2xx HTTP responses", async () => {
    const fakeFetch = (async () =>
      new Response("server fail", {
        status: 500,
        headers: { "Content-Type": "text/plain" },
      })) as unknown as typeof fetch;

    await assert.rejects(
      () =>
        postAssistantLeadQuestion(exampleRequest(), {
          baseUrl: "https://api.test",
          fetchImpl: fakeFetch,
        }),
      (err: unknown) =>
        err instanceof ApiError &&
        err.status === 500 &&
        err.url.includes("/api/assistant/lead-question"),
    );
  });
});
