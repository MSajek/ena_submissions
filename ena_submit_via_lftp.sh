#!/usr/bin/env bash

# =======================
# ENA FTP Upload Script
# =======================

# Default parameters
DEFAULT_THREADS=4
DEFAULT_EXTS="*.fq.gz *.fastq.gz"

show_usage() {
    echo "Usage: $0 <directory> [parallel_transfers] [file_extensions]"
    echo
    echo "Uploads sequencing files to ENA Webin staging via FTP."
    echo
    echo "Parameters:"
    echo "  directory            Required. Local directory containing files to upload."
    echo "  parallel_transfers   Optional. Number of parallel uploads (default: $DEFAULT_THREADS)."
    echo "  file_extensions      Optional. Space-separated glob patterns in quotes."
    echo "                       Default: \"$DEFAULT_EXTS\""
    echo
    echo "Examples:"
    echo "  $0 /path/to/data"
    echo "  $0 /path/to/data 6"
    echo "  $0 /path/to/data 8 \"*.fq.gz *.fastq.gz *.bam\""
    exit 1
}

# Show usage if no arguments or -h/--help
if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" ]]; then
    show_usage
fi

# =======================
# User input
# =======================
LOCAL_DIR="$1"
THREADS="${2:-$DEFAULT_THREADS}"
EXTS="${3:-$DEFAULT_EXTS}"

# Check directory
if [[ ! -d "$LOCAL_DIR" ]]; then
    echo "Error: Directory '$LOCAL_DIR' does not exist."
    exit 1
fi

# Webin credentials
read -p "Enter Webin username (e.g., Webin-XXXXX): " WEBIN_USER
read -s -p "Enter Webin password: " WEBIN_PASS
echo

# Check lftp installation
if ! command -v lftp &> /dev/null; then
    echo "Error: lftp is not installed. Install it with: sudo apt install lftp"
    exit 1
fi

# =======================
# Upload via lftp
# =======================
echo "Starting FTP upload..."
echo "Directory: $LOCAL_DIR"
echo "Parallel transfers: $THREADS"
echo "File extensions: $EXTS"
echo

lftp -u "$WEBIN_USER","$WEBIN_PASS" webin.ebi.ac.uk <<EOF
set ftp:ssl-allow no
set net:max-retries 2
set net:timeout 20
set net:reconnect-interval-base 5
set net:reconnect-interval-max 20
set mirror:parallel-transfer-count $THREADS
set xfer:clobber on
set xfer:use-temp-name no

cd .
mirror --reverse \
       --verbose \
       --parallel=$THREADS \
       --use-pget-n=$THREADS \
       --only-newer \
       --ignore-time \
$(for ext in $EXTS; do echo "       --include-glob $ext \\"; done) \
       "$LOCAL_DIR" .
bye
EOF

echo "Upload complete. Verify with:"
echo "  ftp webin.ebi.ac.uk"
