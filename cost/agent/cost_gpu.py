"""Cost add-on: GPU watts split by who uses the GPU (by the CT of each GPU process), and a CPU-load estimate
for the whole server. Sampled every 10 s, summed in memory, flushed to sqlite once a minute."""
import re, subprocess, time
from pathlib import Path

from dash_sdk import ct, on_start

from cost_db import LOCK, day_of, db, num

EVERY = 10
STATE = {"last": None, "watts": None, "cls": None}
_acc = {"gpu": {}, "server": {}}  # day -> {cls: Wh} / day -> Wh


def _smi(*args):
    r = subprocess.run(["nvidia-smi", *args, "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else ""


def _ct_of_pid(pid):
    try:
        m = re.search(r"/lxc/(\d+)/", Path(f"/proc/{pid}/cgroup").read_text())
        return int(m[1]) if m else None
    except OSError:
        return None


def _class_of(pid, name):
    c = _ct_of_pid(pid)
    if c and c == ct("ai"):
        return "ollama" if "ollama" in name.lower() else "speech"
    if c and c == ct("games"):
        return "games"
    return "other"


def classify(watts, apps, gfx=(), idle_w=14.0):
    """watts, [(pid, process name, MiB, sm % or None)] (+ graphics-only pids [(pid, name, MiB, sm %)]) ->
    {class: share 0..1 of the watts}. Power up to the idle baseline is 'idle'; only the excess is split by class,
    weighted by each process' SM % when nvidia-smi reports it, else by GPU memory."""
    procs = list(apps) + [g for g in gfx if g[0] not in {a[0] for a in apps}]
    if watts <= 0 or not procs:
        return {"idle": 1.0}
    base = min(watts, max(idle_w, 0.0))
    excess = watts - base
    use = {}
    if any((p[3] or 0) > 0 for p in procs):
        for pid, name, mib, sm in procs:
            if sm:
                cls = _class_of(pid, name)
                use[cls] = use.get(cls, 0) + sm
    else:
        for pid, name, mib, sm in procs:
            cls = _class_of(pid, name)
            use[cls] = use.get(cls, 0) + max(mib, 1)
    tot = sum(use.values())
    out = {"idle": base / watts} if base else {}
    if excess > 0 and tot:
        for k, v in use.items():
            out[k] = out.get(k, 0.0) + excess / watts * v / tot
    return out or {"idle": 1.0}


def _pmon():
    """{pid: (type C/G, sm %)} from `nvidia-smi pmon`: lists graphics (Wolf/games) processes that --query-compute-apps misses"""
    try:
        r = subprocess.run(["nvidia-smi", "pmon", "-c", "1", "-s", "u"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return {}
    out = {}
    for line in r.stdout.splitlines() if r.returncode == 0 else []:
        f = line.split()
        if len(f) < 5 or line.startswith("#") or not f[1].isdigit():
            continue
        out[int(f[1])] = (f[2], int(f[3]) if f[3].isdigit() else None, f[-1])
    return out


def sample():
    """(watts, {class: share}) or None when there is no GPU / nvidia-smi fails"""
    p = _smi("--query-gpu=power.draw")
    try:
        watts = float(p.splitlines()[0])
    except (IndexError, ValueError):
        return None
    mem = {}
    for line in _smi("--query-compute-apps=pid,process_name,used_memory").splitlines():
        try:
            pid, name, mib = [x.strip() for x in line.split(",")]
            mem[int(pid)] = (name, int(mib))
        except ValueError:
            continue
    mon = _pmon()
    apps, gfx = [], []
    for pid, (kind, sm, name) in mon.items():
        if pid in mem:
            apps.append((pid, mem[pid][0], mem[pid][1], sm))
        elif _ct_of_pid(pid) == ct("games"):  # graphics procs of the games CT; others (host desktop) are not ours
            gfx.append((pid, name, 1, sm))
    apps += [(pid, n, m, None) for pid, (n, m) in mem.items() if pid not in mon]
    return watts, classify(watts, apps, gfx, num("gpu_idle_w", 14))


def _cpu_times():
    f = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
    v = [int(x) for x in f]
    return sum(v) - v[3] - v[4], sum(v)  # busy (without idle + iowait), total


def server_watts(frac):
    idle, mx = num("idle_w", 45), num("max_w", 65)
    return idle + (mx - idle) * max(0.0, min(1.0, frac))


def flush():
    with LOCK:
        gpu, srv = _acc["gpu"], _acc["server"]
        _acc["gpu"], _acc["server"] = {}, {}
    if not gpu and not srv:
        return
    c = db()
    with LOCK, c:
        for day, d in gpu.items():
            for cls, wh in d.items():
                c.execute("INSERT INTO gpu_wh VALUES (?,?,?) ON CONFLICT(day,cls) DO UPDATE SET wh = wh + excluded.wh", (day, cls, wh))
        for day, wh in srv.items():
            c.execute("INSERT INTO server_wh VALUES (?,?) ON CONFLICT(day) DO UPDATE SET wh = wh + excluded.wh", (day, wh))
    c.close()


def tick(dt, gpu, frac):
    """add dt seconds of use: gpu = (watts, shares) or None, frac = CPU busy fraction"""
    day = day_of(time.time())
    with LOCK:
        if gpu:
            d = _acc["gpu"].setdefault(day, {})
            for cls, share in gpu[1].items():
                d[cls] = d.get(cls, 0.0) + gpu[0] * share * dt / 3600
        _acc["server"][day] = _acc["server"].get(day, 0.0) + server_watts(frac) * dt / 3600


@on_start
def power_loop():
    prev, last_t, last_flush = None, time.time(), time.time()
    try:
        prev = _cpu_times()
    except OSError:
        pass
    while True:
        time.sleep(EVERY)
        try:
            now = time.time()
            dt, last_t = min(now - last_t, 60), now  # a stalled box must not book minutes of watts in one go
            frac = 0.0
            try:
                cur = _cpu_times()
                if prev and cur[1] > prev[1]:
                    frac = (cur[0] - prev[0]) / (cur[1] - prev[1])
                prev = cur
            except OSError:
                pass
            g = sample()
            STATE.update(last=now, watts=g[0] if g else None, cls=g[1] if g else None)
            tick(dt, g, frac)
            if now - last_flush >= 60:
                flush()
                last_flush = now
        except Exception as e:  # the sampler keeps going whatever one round hits
            STATE["error"] = str(e)[:200]
