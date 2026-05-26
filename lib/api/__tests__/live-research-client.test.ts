/**
 * Block 10E — `postLiveCompanyResearch` client unit tests.
 *
 * Run with the project's existing Node-test pattern:
 *   node --experimental-strip-types --test lib/api/__tests__/live-research-client.test.ts
 *
 * No real backend or Exa request is ever issued — `fetchImpl` is
 * injected so the request/response shapes can be asserted directly.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { ApiError, postLiveCompanyResearch } from "../client.ts";
import type {
  LiveResearchRequest,
  LiveResearchResponse,
} from "../types.ts";

function fakeOkResponse(): LiveResearchResponse {
  return {
    provider: "exa",
    run_mode: "live_research",
    enabled: true,
    status: "ok",
    company_name: "Acme Corp",
    query_used: "Acme Corp SaaS Sweden company sales revenue operations",
    evidence_cards: [
      {
        title: "Acme Corp expands EMEA sales",
        url: "https://news.example.com/acme",
        source_domain: "news.example.com",
        snippet:
          "Acme Corp announced an EMEA expansion this quarter, " +
          "doubling its sales headcount across France and Germany.",
        source_type: "live_web",
        confidence: "High",
        why_it_matters:
          "Public web result for Acme Corp in SaaS (Sweden) — review the source before relying on it.",
      },
    ],
    information_risks: [],
    confidence: "High",
    sources: [
      {
        url: "https://news.example.com/acme",
        domain: "news.example.com",
        title: "Acme Corp expands EMEA sales",
      },
    ],
    fetched_at: "2026-05-26T21:00:00.000Z",
    warnings: [],
    estimated_request_count: 1,
    user_message: "Found 1 public-web result(s).",
  };
}

describe("postLiveCompanyResearch", () => {
  it("posts the request body to /api/research/live-company", async () => {
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

    const request: LiveResearchRequest = {
      company_name: "Acme Corp",
      industry: "SaaS",
      country: "Sweden",
    };

    const response = await postLiveCompanyResearch(request, {
      baseUrl: "https://api.test",
      fetchImpl: fakeFetch,
    });

    assert.equal(capturedUrl, "https://api.test/api/research/live-company");
    assert.equal(capturedInit?.method, "POST");
    assert.equal(response.status, "ok");
    assert.equal(response.run_mode, "live_research");
    assert.equal(response.evidence_cards.length, 1);
  });

  it("parses disabled / unavailable responses without throwing", async () => {
    const disabledBody: LiveResearchResponse = {
      ...fakeOkResponse(),
      enabled: false,
      status: "disabled",
      provider: "none",
      evidence_cards: [],
      sources: [],
      warnings: ["ENABLE_LIVE_RESEARCH is not enabled on this backend."],
      user_message: "Live research is currently disabled for the public demo.",
    };

    const fakeFetch = (async () =>
      new Response(JSON.stringify(disabledBody), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })) as unknown as typeof fetch;

    const response = await postLiveCompanyResearch(
      { company_name: "Acme Corp" },
      { baseUrl: "https://api.test", fetchImpl: fakeFetch },
    );

    assert.equal(response.status, "disabled");
    assert.equal(response.enabled, false);
    assert.equal(response.evidence_cards.length, 0);
  });

  it("throws ApiError on non-2xx HTTP responses", async () => {
    const fakeFetch = (async () =>
      new Response("server fail", {
        status: 500,
        headers: { "Content-Type": "text/plain" },
      })) as unknown as typeof fetch;

    await assert.rejects(
      () =>
        postLiveCompanyResearch(
          { company_name: "Acme Corp" },
          { baseUrl: "https://api.test", fetchImpl: fakeFetch },
        ),
      (err: unknown) =>
        err instanceof ApiError &&
        err.status === 500 &&
        err.url.includes("/api/research/live-company"),
    );
  });
});
