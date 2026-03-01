export class StaticCatalogSource {
  constructor(options = {}) {
    const { fetchFn = (...args) => fetch(...args), url = "/public/catalog.json" } = options;
    this.fetchFn = fetchFn;
    this.url = url;
  }

  async fetchCatalog() {
    const response = await this.fetchFn(this.url);
    if (!response.ok) {
      throw new Error(`catalog load failed: ${response.status}`);
    }
    const catalog = await response.json();
    return catalog;
  }
}

export class ApiCatalogSource {
  constructor(options = {}) {
    const { fetchFn = (...args) => fetch(...args), baseUrl = "/api/v1" } = options;
    this.fetchFn = fetchFn;
    this.baseUrl = baseUrl;
  }

  async fetchCatalog(params = {}) {
    const useAbsolute = this.baseUrl.startsWith("http://") || this.baseUrl.startsWith("https://");
    const url = new URL(`${this.baseUrl}/catalog`, "http://local");
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }

    const requestUrl = useAbsolute ? url.toString() : url.pathname + url.search;
    const response = await this.fetchFn(requestUrl);
    if (!response.ok) {
      throw new Error(`catalog load failed: ${response.status}`);
    }
    return response.json();
  }
}
