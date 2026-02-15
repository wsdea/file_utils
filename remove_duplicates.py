#!/usr/bin/env python3

"""
Script for removing duplicate files based on partial SHA-256 hashes.
Keeping the file with the shortest basename when duplicates are found.
Showing which files would be removed by default.
Using --go flag for actually removing the files.
Caching hashes in a JSON file for memoizing previous computations.
Computing hash using only the first 1 MB of each file.
Using tqdm for showing progress.

Usage: remove_duplicates.py <directory> [--go]
  <directory> : The directory for scanning duplicates.
  --go        : Actually removing the duplicate files.
"""

import argparse
import glob
import hashlib
import json
import os

from tqdm import tqdm

CACHE_FILENAME = ".remove_duplicates_cache.json"
HASH_READ_SIZE = 1024 * 1024  # 1 MB


def load_cache(cache_path):
    """Loading cache from file."""
    if not os.path.exists(cache_path):
        return {}
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache_path, cache_data):
    """Saving cache to file."""
    try:
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Warning: Cannot save cache: {e}")


def compute_sha256_partial(file_path):
    """Computing SHA-256 hash using only first 1 MB of file."""
    hash_func = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read(HASH_READ_SIZE)
        hash_func.update(data)
    return hash_func.hexdigest()


def should_replace(existing_path, candidate_path):
    """Determining if replacing existing file based on shorter basename."""
    existing_name = os.path.basename(existing_path)
    candidate_name = os.path.basename(candidate_path)

    if len(candidate_name) < len(existing_name):
        return True
    if len(candidate_name) == len(existing_name):
        return candidate_name < existing_name
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Script for removing duplicate files using cached partial SHA-256 hashes."
    )
    parser.add_argument("directory", help="The directory for scanning duplicates.")
    parser.add_argument(
        "--go", action="store_true", help="Actually removing the duplicate files."
    )
    args = parser.parse_args()

    base_dir = args.directory
    go_flag = args.go

    print(f"Processing directory: {base_dir}")

    cache_path = os.path.join(base_dir, CACHE_FILENAME)
    cache = load_cache(cache_path)

    global_hashes = {}

    files = [
        p
        for p in glob.glob(os.path.join(base_dir, "**", "*"), recursive=True)
        if os.path.isfile(p)
    ]

    for file_path in tqdm(files, desc="Scanning files"):
        try:
            stat = os.stat(file_path)
            mtime = stat.st_mtime
            size = stat.st_size

            cache_entry = cache.get(file_path)

            if (
                cache_entry
                and cache_entry.get("mtime") == mtime
                and cache_entry.get("size") == size
            ):
                file_hash = cache_entry["hash"]
            else:
                file_hash = compute_sha256_partial(file_path)
                cache[file_path] = {
                    "mtime": mtime,
                    "size": size,
                    "hash": file_hash,
                }

        except Exception as e:
            print(f"Warning: Cannot hash file {file_path}: {e}")
            continue

        if file_hash in global_hashes:
            existing = global_hashes[file_hash]

            if should_replace(existing, file_path):
                remove_path = existing
                global_hashes[file_hash] = file_path
            else:
                remove_path = file_path

            print(f"Would remove: {remove_path}")

            if go_flag:
                try:
                    os.remove(remove_path)
                    print(f"removed '{remove_path}'")
                except OSError as e:
                    print(f"Error: Cannot remove file {remove_path}: {e}")
        else:
            global_hashes[file_hash] = file_path

    save_cache(cache_path, cache)


if __name__ == "__main__":
    main()
