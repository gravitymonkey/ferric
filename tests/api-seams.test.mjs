import assert from "node:assert/strict";
import { StaticCatalogSource, ApiCatalogSource } from "../src/data/catalog-source.mjs";
import { StaticStreamResolver, ApiStreamResolver } from "../src/playback/stream-resolver.mjs";

{
  const source = new StaticCatalogSource({
    fetchFn: async (url) => ({
      ok: true,
      json: async () => ({ schema_version: "1.0", tracks: [], loaded_from: url })
    })
  });
  const catalog = await source.fetchCatalog();
  assert.equal(catalog.loaded_from, "/public/catalog.json");
}

{
  const calls = [];
  const source = new ApiCatalogSource({
    fetchFn: async (url) => {
      calls.push(url);
      return {
        ok: true,
        json: async () => ({ tracks: [] })
      };
    }
  });
  await source.fetchCatalog({ limit: 10, offset: 5, q: "neon" });
  assert.equal(calls[0], "/api/v1/catalog?limit=10&offset=5&q=neon");
}

{
  const resolver = new StaticStreamResolver();
  const result = await resolver.resolve({
    id: "track_001",
    stream: { protocol: "hls", url: "/generated/hls/track_001/playlist.m3u8" }
  });
  assert.equal(result.track_id, "track_001");
  assert.equal(result.stream.url, "/generated/hls/track_001/playlist.m3u8");
}

{
  const calls = [];
  const resolver = new ApiStreamResolver({
    fetchFn: async (url, init) => {
      calls.push({ url, init });
      return {
        ok: true,
        json: async () => ({
          track_id: "track_001",
          stream: { protocol: "hls", url: "/api/generated/hls/tokenized.m3u8", requires_auth: false }
        })
      };
    }
  });

  const result = await resolver.resolve({ id: "track_001" });
  assert.equal(calls[0].url, "/api/v1/playback/resolve");
  const body = JSON.parse(calls[0].init.body);
  assert.equal(body.track_id, "track_001");
  assert.equal(result.stream.url, "/api/generated/hls/tokenized.m3u8");
}

console.log("PASS: catalog and stream resolver seams are wired");
