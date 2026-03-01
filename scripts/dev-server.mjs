import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const port = Number(process.env.PORT || 8080);
const backendOrigin = process.env.BACKEND_ORIGIN || "http://127.0.0.1:8000";
const backendUrl = new URL(backendOrigin);

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".m3u8": "application/vnd.apple.mpegurl",
  ".ts": "video/mp2t",
  ".mp3": "audio/mpeg"
};

function sanitizePath(urlPath) {
  const pathname = decodeURIComponent(urlPath.split("?")[0]);
  const resolved = path.normalize(path.join(root, pathname));
  if (!resolved.startsWith(root)) {
    return null;
  }
  return resolved;
}

const server = http.createServer((req, res) => {
  if ((req.url || "").startsWith("/api/")) {
    const upstreamPath = req.url || "/";
    const options = {
      protocol: backendUrl.protocol,
      hostname: backendUrl.hostname,
      port: backendUrl.port || (backendUrl.protocol === "https:" ? 443 : 80),
      path: upstreamPath,
      method: req.method,
      headers: req.headers
    };

    const client = backendUrl.protocol === "https:" ? https : http;
    const proxyReq = client.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
      proxyRes.pipe(res);
    });

    proxyReq.on("error", () => {
      res.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
      res.end(
        JSON.stringify({
          error: "backend_unreachable",
          message: `Could not reach backend at ${backendOrigin}`
        })
      );
    });

    req.pipe(proxyReq);
    return;
  }

  const requestPath = req.url === "/" ? "/public/index.html" : req.url;
  const filePath = sanitizePath(requestPath || "/");
  if (!filePath) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    res.writeHead(404);
    res.end("Not Found");
    return;
  }

  const ext = path.extname(filePath);
  const contentType = contentTypes[ext] || "application/octet-stream";
  res.writeHead(200, { "Content-Type": contentType });
  fs.createReadStream(filePath).pipe(res);
});

server.listen(port, () => {
  console.log(`Ferric dev server running on http://localhost:${port}/public/index.html`);
});
