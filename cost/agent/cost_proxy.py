"""Cost add-on: a pass-through proxy in front of Ollama that counts tokens per call and caller. Clients point at
http://<host>:11435 instead of the AI CT's 11434; bodies stream through untouched, logging never breaks a call.
Runs as its own service (dash-cost-proxy.service: python3 -I cost_proxy.py), so agent restarts never cut Ollama.
GET /_cost/health answers {"ok": true, "since": ..., "error": ...} for the agent's /cost/health."""
import http.client, ipaddress, json, os, queue, re, select, socket, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parents[2] / "agent")):  # -I drops the script dir; config.py lives in the core agent
    if _p not in sys.path:
        sys.path.insert(0, _p)

from config import CFG, HOST_IP, ip  # noqa: E402  (no dash_sdk: that would load the whole agent)

from cost_db import LOCK, day_of, db  # noqa: E402

PORT = int(os.environ.get("DASH_COST_PROXY_PORT") or 11435)
TRACKED = ("/api/chat", "/api/generate", "/api/embed", "/api/embeddings")
STATE = {"ok": False, "since": None, "error": None}
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "proxy-authenticate",
       "proxy-authorization", "content-length", "host"}
KEEP = 8 << 20  # bytes of a response kept to read its totals from


_own = {"at": 0.0, "ips": set()}


def allowed(addr):
    """only this host (loopback + its own addresses) and the CTs of config.json may use the proxy"""
    try:
        a = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if a.is_loopback:
        return True
    if time.time() - _own["at"] > 60:
        try:
            out = subprocess.run(["ip", "-o", "-4", "addr"], capture_output=True, text=True, timeout=5).stdout
            _own["ips"] = set(re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", out))
        except (OSError, subprocess.SubprocessError):
            pass
        _own["at"] = time.time()
    ok = _own["ips"] | {HOST_IP} | {v.get("ip") for v in (CFG.get("cts") or {}).values() if isinstance(v, dict)}
    return addr in ok


def source_of(addr):
    for name, v in (CFG.get("cts") or {}).items():
        if v.get("ip") == addr:
            return name
    return "other"


def final_object(raw):
    """the object holding the token counts: the whole body, or the last NDJSON line that has them"""
    for blob in [raw] + list(reversed(raw.splitlines())):
        try:
            d = json.loads(blob)
        except ValueError:
            continue
        if isinstance(d, dict) and ("prompt_eval_count" in d or "eval_count" in d or d.get("done")):
            return d
    return None


def record(job, source, path, status, raw):
    d = final_object(raw) or {}
    now = time.time()
    c = db()
    with LOCK, c:
        c.execute("INSERT INTO calls (t,day,job,source,model,path,status,t_in,t_out,eval_ns,load_ns) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (now, day_of(now), job, source, d.get("model") or "", path, status, d.get("prompt_eval_count") or 0,
                   d.get("eval_count") or 0, d.get("eval_duration") or 0, d.get("load_duration") or 0))
    c.close()


_log = queue.Queue(maxsize=1000)


def _log_worker():
    while True:
        args = _log.get()
        try:
            record(*args)
        except Exception as e:
            STATE["error"] = f"log: {str(e)[:150]}"  # never fails a call


def _watch(conn, up, done):
    """close the upstream connection when the client hangs up, so Ollama stops generating for nobody"""
    while not done.wait(0.5):
        try:
            if select.select([conn], [], [], 0)[0] and conn.recv(1, socket.MSG_PEEK) == b"":
                if up.sock:
                    up.sock.shutdown(socket.SHUT_RDWR)
                return
        except (OSError, ValueError):
            return


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # bodies end with the connection, so streams need no chunk framing

    def log_message(self, *a):
        pass

    def _body(self):
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            out = b""
            while True:
                n = int(self.rfile.readline().split(b";")[0].strip() or b"0", 16)
                if not n:
                    self.rfile.readline()
                    return out
                out += self.rfile.read(n)
                self.rfile.readline()
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else None

    def _proxy(self):
        if self.path.split("?")[0] == "/_cost/health" and self.command == "GET":
            out = json.dumps({"ok": True, **STATE}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        if not allowed(self.client_address[0]):
            self.send_error(403, "not allowed")
            return
        path = self.path.split("?")[0]
        source = source_of(self.client_address[0])
        job = (self.headers.get("X-Job") or "").strip()[:40] or (source if source != "other" else "other")
        keep, status, up, done = bytearray(), 502, None, threading.Event()
        try:
            body = self._body()
            up = http.client.HTTPConnection(ip("ai"), 11434, timeout=900)
            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP and k.lower() != "x-job"}
            up.request(self.command, self.path, body=body, headers=headers)
            threading.Thread(target=_watch, args=(self.connection, up, done), daemon=True).start()
            r = up.getresponse()
            status = r.status
            self.send_response(r.status, r.reason)
            for k, v in r.getheaders():
                if k.lower() not in HOP or k.lower() == "content-length":
                    self.send_header(k, v)
            self.end_headers()
            track = self.command == "POST" and path in TRACKED
            while True:
                chunk = r.read1(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
                if track:
                    keep += chunk
                    if len(keep) > KEEP:
                        del keep[:len(keep) - 65536]  # long stream: only the tail (the totals) matters
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            if not keep and status == 502:
                try:
                    self.send_error(502, "upstream unreachable")
                except Exception:
                    pass
        finally:
            done.set()
            if up:
                up.close()
        try:  # the client has its whole answer: end it before anything is logged
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        if self.command == "POST" and path in TRACKED:
            try:
                _log.put_nowait((job, source, path, status, bytes(keep).decode("utf-8", "replace")))
            except queue.Full:
                STATE["error"] = "log: queue full"

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_PATCH = _proxy


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve():
    threading.Thread(target=_log_worker, daemon=True).start()
    while True:
        try:
            srv = Server(("0.0.0.0", PORT), Handler)
        except OSError as e:
            STATE.update(ok=False, error=f"bind: {e}")
            time.sleep(60)
            continue
        STATE.update(ok=True, since=int(time.time()), error=None)
        srv.serve_forever()


if __name__ == "__main__":
    serve()
