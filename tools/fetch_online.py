"""Fetch a preselected online sample through the official authenticated API.

Keys come from the official CLI's local auth store and are never printed.
The signed replay redirect is downloaded WITHOUT an Authorization header.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

from unswbc import auth

BASE = "https://game.battlecode.au/api/v1"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self):
        self.key = auth.key()
        if not self.key:
            raise RuntimeError("No local Battlecode API key. Configure official CLI authentication first.")
        self.opener = urllib.request.build_opener(NoRedirect)
        self.requests = deque()

    def request(self, path, binary=False):
        while self.requests and time.monotonic() - self.requests[0] >= 60:
            self.requests.popleft()
        if len(self.requests) >= 100:
            time.sleep(max(0, 60 - (time.monotonic() - self.requests[0])))
            return self.request(path, binary)
        self.requests.append(time.monotonic())
        req = urllib.request.Request(BASE + path, headers={
            "Authorization": "Bearer " + self.key,
            "User-Agent": "battlecode-evidence-audit/1.0",
            "Accept": "application/octet-stream" if binary else "application/json",
        })
        try:
            response = self.opener.open(req, timeout=45)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                pause = min(60, max(1, int(error.headers.get("Retry-After", "10"))))
                time.sleep(pause)
                return self.request(path, binary)
            if binary and error.code in (301, 302, 303, 307, 308):
                location = error.headers.get("Location")
                if not location or urllib.parse.urlparse(location).scheme != "https":
                    raise RuntimeError("Replay redirect was missing a secure download URL.") from None
                # A NEW request: do not forward the API key to the signed host.
                anonymous = urllib.request.Request(location, headers={"User-Agent": "battlecode-evidence-audit/1.0"})
                with urllib.request.urlopen(anonymous, timeout=60) as signed:
                    return signed.read()
            raise RuntimeError(f"Official API returned HTTP {error.code} for {path}.") from None
        with response:
            data = response.read()
        return data if binary else json.loads(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--directory", type=Path, default=Path("test-results/online100"))
    parser.add_argument("--inspect", action="store_true", help="Read submission and battle metadata only")
    args = parser.parse_args()
    client = Client()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.inspect:
        for name, path in (("submissions", "/submissions"), ("battles", "/battles?limit=200")):
            data = client.request(path)
            (args.directory / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Saved {name} metadata", flush=True)
        return
    if not args.selection:
        parser.error("--selection is required unless --inspect is used")
    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    manifest = []
    for row in selection["rows"]:
        url = next(link["href"] for link in row["links"] if link["text"] == "Watch")
        match_id = int(url.rsplit("/", 1)[-1])
        metadata_file = args.directory / f"{match_id}.json"
        replay_file = args.directory / f"{match_id}.replay"
        item = {"match_id": match_id, "url": url, "table": row["cells"]}
        try:
            if not metadata_file.exists():
                data = client.request(f"/battles/{match_id}")
                metadata_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            if not replay_file.exists():
                replay_file.write_bytes(client.request(f"/battles/{match_id}/replay", binary=True))
            blob = replay_file.read_bytes()
            if not blob:
                raise RuntimeError("Downloaded replay was empty")
            item.update(status="downloaded", bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest(),
                        metadata=str(metadata_file.resolve()), replay=str(replay_file.resolve()))
        except (RuntimeError, OSError) as error:
            item.update(status="unavailable", error=str(error))
        manifest.append(item)
        manifest_document = {"source": BASE, "selection": str(args.selection.resolve()),
                             "downloaded_at": datetime.now(timezone.utc).isoformat(), "matches": manifest}
        (args.directory / "fetch-manifest.json").write_text(json.dumps(manifest_document, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{len(manifest)}/{len(selection['rows'])}: match {match_id} {item['status']}", flush=True)
    good = sum(item["status"] == "downloaded" for item in manifest)
    print(f"Complete: {good}/{len(manifest)} full replays. Unavailable entries are retained.")


if __name__ == "__main__":
    main()
