# `ingestion/loader.py`

3 jobs: 
- **validate** a GitHub URL (SSRF-safe), 
- **clone** it shallowly to a temp dir, and 
- **walk + filter** the files. 
No repo code is ever executed — files are only read.

---
## Repo URL SSRF Protection
`ingestion/loader.py` `validate_repo_url(raw_url)`

```python
if (ip.is_private or  ip.is_loopback or 
        ip.is_link_local or ip.is_reserved or 
        ip.is_multicast or  ip.is_unspecified):
```
- Loopback (127.0.0.1 or ::1): Prevents the app from talking to itself. 
- Private/Local (10.x.x.x, 192.168.x.x, 172.16.x.x): Prevents access to internal company networks or routers (like 192.168.1.1).
- Link-local (169.254.x.x): Prevents access to cloud metadata services (like AWS metadata at 169.254.169.254, a common SSRF target).
- reserved: IP addresses set aside by the Internet Assigned Numbers Authority (IANA) for future protocols, experimental testing, etc. (240.0.0.0/4 range) these are not officially routable
- multicast: used to send a single data packet to multiple destinations simultaneously (one-to-many communication), rather than to a single specific computer (unicast). 
Denial of Service (DoS): If an attacker forces application to send requests to a multicast address, it can flood local or network segments with traffic.
(from `224.0.0.0` to `239.255.255.255`). IPv6: Addresses starting with ff00::/8.
- unspecified: What it means: A placeholder address ==> "all zeros" or "no address specified." Tells a network stack to listen on all available network interfaces or
that the source/destination is currently unknown.
It can cause the application to bind incorrectly, crash, or loop back to default local interfaces unintentionally.
```
IPv4: 0.0.0.0
IPv6: ::
```
## method: `_create_indexing_codebase`
Insert a new codebase row and move it pending -> indexing.
Why: In the current synchronous code there's no reason, and setting INDEXING directly is simpler. \
The two-step (pending → indexing) only earns its keep in an asynchronous design:
```python
codebase = Codebase(
        source=CodebaseSource.GITHUB, location=url, status=CodebaseStatus.PENDING
    )
    session.add(codebase)
    session.flush()
    codebase.status = CodebaseStatus.INDEXING
    session.commit()
    return codebase
```
- The request inserts the row as pending and commits immediately → "I've accepted this repo, it's queued."
- A background worker later picks it up and flips it to indexing when it actually starts cloning.
So pending is never durably stored; it lives for a few microseconds inside one uncommitted transaction. 
That means the two-step buys nothing here
    
  
---

MAX_FILE_BYTES: minified JS bundles, generated lockfile blobs, big JSON/CSV data, vendored libraries, sample datasets, 
model weights that slipped the extension filter; skip those oversized single files.

---

## Debugging each step in the CLI

Run everything **inside the container** (git binary + deps present):

```bash
docker compose exec api python
```

Then, at the Python prompt:

### 1. URL validation

```python
from app.ingestion.loader import validate_repo_url, RepoValidationError

validate_repo_url("https://github.com/octocat/Hello-World")   # -> the URL
try:
    validate_repo_url("http://localhost/x")
except RepoValidationError as e:
    print("rejected:", e)
```

See what a host resolves to (why SSRF check passes/fails):

```python
import socket, ipaddress
for i in socket.getaddrinfo("github.com", None):
    ip = i[4][0]
    print(ip, "private" if ipaddress.ip_address(ip).is_private else "public")
```

### 2. File-name filter

```python
from app.ingestion.loader import _is_ignored_file
for n in ["main.py", ".env", "logo.png", "key.pem", "package-lock.json"]:
    print(n, "->", _is_ignored_file(n))
```

### 3. Clone + collect (the whole thing)

```python
from app.ingestion.loader import clone_and_collect
tmp, files = clone_and_collect("https://github.com/octocat/Hello-World")
print("temp dir:", tmp)
print("kept files:", len(files))
for f in files[:20]:
    print(f.size, f.path)

import shutil; shutil.rmtree(tmp)   # clean up when done
```

### 4. Filter a directory already have (no network)

```python
from pathlib import Path
from app.ingestion.loader import _collect_files
files = _collect_files(Path("/app"))     # e.g. filter the app itself
print(len(files), "files")
```

### One-liners (no REPL)

```bash
# validate a URL
docker compose exec api python -c "from app.ingestion.loader import validate_repo_url as v; print(v('https://github.com/octocat/Hello-World'))"

# clone + count kept files, then remove temp dir
docker compose exec api python -c "from app.ingestion.loader import clone_and_collect as c; import shutil; t,f=c('https://github.com/octocat/Hello-World'); print(len(f),'files in',t); [print(x.path) for x in f]; shutil.rmtree(t)"
```

### Inspect what git actually did

```bash
# clone by hand to see git's own output/timing
docker compose exec api sh -c "git clone --depth 1 --single-branch https://github.com/octocat/Hello-World /tmp/peek && ls -la /tmp/peek && rm -rf /tmp/peek"
```

### Watch it via the API + logs

```bash
docker compose logs -f api          # tail app logs while hit /api/ingest
curl -s -X POST http://localhost:8000/api/ingest -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/octocat/Hello-World"}'
```

> change limits at runtime to force a `RepoLimitError` without a big repo —
> set e.g. `MAX_FILES=1` in `.env` and restart the container, then ingest any repo.
