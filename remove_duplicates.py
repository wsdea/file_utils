#!/usr/bin/env python3

"""
Script to remove duplicate files based on their SHA-256 hashes.
By default, it just shows which files it would remove.
Use --go flag to actually remove the files.
Usage: remove_duplicates.py <directory> [--go]
  <directory> : The directory to scan for duplicates.
  --go        : Optional flag to actually remove the duplicate files.
"""

import argparse
import glob
import hashlib
import os


def compute_sha256(file_path, block_size=65536):
    hash_func = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hash_func.update(block)
    return hash_func.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Script to remove duplicate files based on their SHA-256 hashes."
    )
    parser.add_argument("directory", help="The directory to scan for duplicates.")
    parser.add_argument(
        "--go", action="store_true", help="Actually remove the duplicate files."
    )
    args = parser.parse_args()

    base_dir = args.directory
    go_flag = args.go

    print(f"Processing directory: {base_dir}")
    global_hashes = {}
    files = [
        p
        for p in glob.glob(os.path.join(base_dir, "**", "*"), recursive=True)
        if os.path.isfile(p)
    ]
    files = sorted(files, key=lambda p: ("_copy" in os.path.basename(p), p))
    for file_path in files:
        try:
            file_hash = compute_sha256(file_path)
        except Exception as e:
            print(f"Warning: Cannot hash file {file_path}: {e}")
            continue
        if file_hash in global_hashes:
            existing = global_hashes[file_hash]
            remove_path = file_path
            if "_copy" in os.path.basename(
                existing
            ) and "_copy" not in os.path.basename(file_path):
                remove_path = existing
                global_hashes[file_hash] = file_path
            print(f"Would remove: {remove_path}")
            if go_flag:
                try:
                    os.remove(remove_path)
                    print(f"removed '{remove_path}'")
                except OSError as e:
                    print(f"Error: Cannot remove file {remove_path}: {e}")
        else:
            global_hashes[file_hash] = file_path


if __name__ == "__main__":
    main()
