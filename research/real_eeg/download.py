"""Download only declared runs, checking official SHA-256 before atomic rename."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shutil
import urllib.request

from .data import BASE_URL, CHECKSUM_SHA256, file_inventory, load_config, read_checksums, sha256, write_json


def fetch_verified(url, target, expected, retries=3):
    target = Path(target)
    if target.is_file() and sha256(target) == expected:
        return "cached"
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "NeuroWeave/2.0 research downloader"})
            with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as handle:
                shutil.copyfileobj(response, handle, 1024 * 1024)
            if sha256(partial) != expected:
                raise ValueError(f"SHA-256 mismatch: {url}")
            partial.replace(target)
            return "downloaded"
        except Exception:
            partial.unlink(missing_ok=True)
            if attempt == retries - 1:
                raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/physionet-pilot.json")
    parser.add_argument("--data-dir", default="data/physionet")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        parser.error("Use between 1 and 8 download workers")
    config, root = load_config(args.config), Path(args.data_dir)
    checksum_path = root / "SHA256SUMS.txt"
    fetch_verified(BASE_URL + "SHA256SUMS.txt", checksum_path, CHECKSUM_SHA256)
    checksums = read_checksums(checksum_path)
    paths = file_inventory(config)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_verified, BASE_URL + path, root / path, checksums[path]): path
                   for path in paths}
        for done, future in enumerate(as_completed(futures), 1):
            status = future.result()  # Failure stops the benchmark; never substitutes synthetic data.
            print(f"{done}/{len(paths)} {futures[future]} {status}", flush=True)
    write_json(root / "download-manifest.json", {
        "dataset": config["dataset"], "checksum_index_sha256": CHECKSUM_SHA256,
        "license": "ODC-By-1.0", "source": "https://physionet.org/content/eegmmidb/1.0.0/",
        "files": [{"path": path, "sha256": checksums[path], "bytes": (root/path).stat().st_size}
                  for path in paths]})


if __name__ == "__main__":
    main()
