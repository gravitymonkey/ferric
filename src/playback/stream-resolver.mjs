export function assertStreamResolver(streamResolver) {
  if (!streamResolver || typeof streamResolver.resolve !== "function") {
    throw new Error("streamResolver must provide resolve(track)");
  }
}

export class StaticStreamResolver {
  async resolve(track) {
    if (!track?.id || !track?.stream?.url) {
      throw new Error("resolve requires track.id and track.stream.url");
    }

    return {
      track_id: track.id,
      stream: {
        protocol: track.stream.protocol ?? "hls",
        url: track.stream.url,
        fallback_url: track.stream.fallback_url ?? null,
        requires_auth: false
      }
    };
  }
}

export class ApiStreamResolver {
  constructor(options = {}) {
    const { fetchFn = (...args) => fetch(...args), baseUrl = "/api/v1" } = options;
    this.fetchFn = fetchFn;
    this.baseUrl = baseUrl;
  }

  async resolve(track, client = { platform: "web", app_version: "0.1.0" }) {
    if (!track?.id) {
      throw new Error("resolve requires track.id");
    }

    const response = await this.fetchFn(`${this.baseUrl}/playback/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        track_id: track.id,
        client
      })
    });

    if (!response.ok) {
      throw new Error(`stream resolve failed: ${response.status}`);
    }

    return response.json();
  }
}
