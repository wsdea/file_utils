#!/bin/bash

# Script to remove duplicate files based on their SHA-256 hashes.
# By default, it just show which files it's going to remove.
# Use --go flag to actually remove the files.
# Usage: ./remove_duplicates.sh <directory> [--go]
#   <directory> : The directory to scan for duplicates.
#   --go        : Optional flag to actually remove the duplicate files.
#   -h          : Display this help message.

# Checking for help flag
if [[ "$1" == "-h" ]]; then
  echo "Usage: $0 <directory> [--go]"
  echo "  <directory> : The directory to scan for duplicates."
  echo "  --go        : Optional flag to actually remove the duplicate files."
  echo "  -h          : Display this help message."
  exit 0
fi

# Specifying the base directory
BASE_DIR="$1"
GO_FLAG="$2"

# Checking if directory is provided
if [[ -z "$BASE_DIR" ]]; then
  echo "Error: No directory specified."
  echo "Usage: $0 <directory> [--go]"
  exit 1
fi

# Finding all directories and processing them from the deepest level
find "$BASE_DIR" -type d | sort -r | while IFS= read -r dir; do
  echo "Processing directory: $dir"

  # Associative array to store hashes and corresponding file paths
  declare -A file_hashes

  # Finding files in the current directory
  find "$dir" -maxdepth 1 -type f | while IFS= read -r file; do
    # Computing hash
    hash=$(sha256sum "$file" | awk '{print $1}')

    # If hash already exists, it's a duplicate
    if [[ -n "${file_hashes[$hash]}" ]]; then
      echo "Would remove: $file"
      if [[ "$GO_FLAG" == "--go" ]]; then
        rm -v "$file"
      fi
    else
      file_hashes["$hash"]="$file"
    fi
  done
done
