/** 临时：把 holo_pet 面板按它原本的假设服务起来（静态 + /api 反代到 8765），用于真渲染验证。 */
import { createServer, request as httpRequest } from 'node:http'
import { readFileSync, statSync } from 'node:fs'
import { join, extname, normalize } from 'node:path'

const WS = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const PORT = 8788
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.woff2': 'font/woff2',
}

createServer((req, res) => {
  const url = String(req.url || '/')
  const cut = url.indexOf('?')
  const pathOnly = cut < 0 ? url : url.slice(0, cut)
  if (pathOnly.startsWith('/api/')) {
    const up = httpRequest({ host: '127.0.0.1', port: 8765, path: pathOnly + (cut < 0 ? '' : url.slice(cut)), method: req.method, headers: { accept: '*/*' } },
      (r) => { res.writeHead(r.statusCode || 502, { 'content-type': String(r.headers['content-type'] || 'application/json') }); r.pipe(res) })
    up.on('error', () => {
      if (res.headersSent || res.writableEnded) { try { res.destroy() } catch (e) { /* 只能断开 */ } return }
      res.writeHead(503, { 'content-type': 'application/json' })
      res.end('{"ok":false,"error":"8765 未起"}')
    })
    req.pipe(up)
    return
  }
  const rel = normalize(decodeURIComponent(pathOnly)).replace(/^[\\/]+/, '')
  const file = join(WS, rel)
  try {
    const st = statSync(file)
    if (!st.isFile()) throw new Error('not a file')
    const body = readFileSync(file)
    res.writeHead(200, { 'content-type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream', 'content-length': String(body.length), 'cache-control': 'no-store' })
    res.end(body)
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' })
    res.end('404 ' + rel)
  }
}).listen(PORT, '127.0.0.1', () => console.log('holo serve on http://127.0.0.1:' + PORT))
