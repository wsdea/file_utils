# File Manipulation Scripts

A collection of useful scripts designed to efficiently manipulate large quantities of files.

## remove_duplicates

This script identifies and removes duplicate files based on their SHA-256 hashes.

### Features
- **Duplicate Detection**: By default, the script scans a specified directory and displays which files are considered duplicates without removing them.
- **Safe Removal**: Use the `--go` flag to permanently delete duplicate files after reviewing the list.

### Usage
```bash
./remove_duplicates.sh <directory> [--go]
```

### Parameters
- `<directory>`: The path to the directory that will be scanned for duplicate files.
- `--go`: Optional flag that triggers the script to actually remove the identified duplicate files.
- `-h`: Displays a help message with usage instructions.

### Example
To scan for duplicates without removing them:
```bash
./remove_duplicates.sh /path/to/your/folder
```

To scan and remove duplicates:
```bash
./remove_duplicates.sh /path/to/your/folder --go
```

### Notes
- **Caution**: Ensure you review the output before using the `--go` flag, as it will permanently delete files.