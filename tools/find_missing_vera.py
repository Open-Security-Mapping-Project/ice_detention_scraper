#!/usr/bin/env python3

import json
import os
import pprint
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def _find_files(directory: str) -> os.DirEntry[str]:
    results = []
    with os.scandir(directory) as d:
        for f in d:
            if f.name.startswith("ice_detention_facilities") and f.name.endswith(".json"):
                results.append(f)
    final = results[0]
    for f in results:
        if f.stat().st_mtime > final.stat().st_mtime:
            final = f
    return final


def main() -> None:
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    root_dir = [f for f in res.stdout.decode("utf-8").split("\n")][0]
    newest_file = _find_files(root_dir)
    with open(newest_file.path, "r") as f_in:
        data = json.load(f_in)
    missing_vera = {k: v for k, v in data["facilities"].items() if not v.get("vera_id", "")}
    pprint.pprint(missing_vera, indent=1, compact=True)
    print(f"Found {len(missing_vera.keys())} facilities with a missing vera.org ID")


if __name__ == "__main__":
    main()
