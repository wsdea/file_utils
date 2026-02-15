#!/usr/bin/env python3

"""
Script for removing duplicate files using staged hashing.

Process:
1. Computing SHA-256 of first 1 MB.
2. If matching, verifying file size equality.
3. If sizes matching, computing SHA-256 of last 10 MB.
4. Removing only if all checks matching.

Keeping the file with the shortest basename.
Caching first and last hashes in a JSON file.
Using tqdm for showing progress.

Usage: remove_duplicates.py <directory> [--go]
"""

import argparse
import glob
import hashlib
import json
import os

from tqdm import tqdm

CACHE_FILENAME = ".remove_duplicates_cache.json"
FIRST_CHUNK_SIZE = 1024 * 1024  # 1 MB
LAST_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB


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


def compute_first_hash(file_path):
    """Computing SHA-256 using first 1 MB of file."""
    hash_func = hashlib.sha256()
    with open(file_path, "rb") as f:
        data = f.read(FIRST_CHUNK_SIZE)
        hash_func.update(data)
    return hash_func.hexdigest()


def compute_last_hash(file_path, size):
    """Computing SHA-256 using last 10 MB of file."""
    hash_func = hashlib.sha256()
    with open(file_path, "rb") as f:
        if size > LAST_CHUNK_SIZE:
            f.seek(size - LAST_CHUNK_SIZE)
        data = f.read(LAST_CHUNK_SIZE)
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
        description="Script for removing duplicate files using staged hashing."
    )
    parser.add_argument("directory", help="Directory for scanning duplicates.")
    parser.add_argument("--go", action="store_true", help="Actually removing files.")
    args = parser.parse_args()

    base_dir = args.directory
    go_flag = args.go

    print(f"Processing directory: {base_dir}")

    cache_path = os.path.join(base_dir, CACHE_FILENAME)
    cache = load_cache(cache_path)

    # Mapping: (size, first_hash) -> list of file paths
    candidates = {}

    files = [
        p
        for p in glob.glob(os.path.join(base_dir, "**", "*"), recursive=True)
        if os.path.isfile(p)
    ]

    for file_path in tqdm(files, desc="Scanning files"):
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            mtime = stat.st_mtime

            cache_entry = cache.get(file_path)

            if (
                cache_entry
                and cache_entry.get("mtime") == mtime
                and cache_entry.get("size") == size
            ):
                first_hash = cache_entry["first_hash"]
            else:
                first_hash = compute_first_hash(file_path)
                cache[file_path] = {
                    "mtime": mtime,
                    "size": size,
                    "first_hash": first_hash,
                    "last_hash": None,
                }

        except Exception as e:
            print(f"Warning: Cannot process file {file_path}: {e}")
            continue

        key = (size, first_hash)
        candidates.setdefault(key, []).append(file_path)

    # Processing potential duplicates
    for (size, first_hash), paths in candidates.items():
        if len(paths) < 2:
            continue

        last_hash_map = {}

        for file_path in paths:
            cache_entry = cache[file_path]

            if cache_entry.get("last_hash"):
                last_hash = cache_entry["last_hash"]
            else:
                last_hash = compute_last_hash(file_path, size)
                cache_entry["last_hash"] = last_hash

            last_hash_map.setdefault(last_hash, []).append(file_path)

        for last_hash, dup_paths in last_hash_map.items():
            if len(dup_paths) < 2:
                continue

            # Sorting to keep shortest basename
            dup_paths_sorted = sorted(
                dup_paths, key=lambda p: (len(os.path.basename(p)), os.path.basename(p))
            )

            keep = dup_paths_sorted[0]
            to_remove = dup_paths_sorted[1:]

            for remove_path in to_remove:
                print(f"Would remove: {remove_path}")
                if go_flag:
                    try:
                        os.remove(remove_path)
                        print(f"removed '{remove_path}'")
                    except OSError as e:
                        print(f"Error: Cannot remove file {remove_path}: {e}")

    save_cache(cache_path, cache)


if __name__ == "__main__":
    main()
