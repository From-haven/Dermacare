#!/usr/bin/env bash
set -euo pipefail

# restore.sh — DermaCare Agent Restore Script
# Restores database and encrypted storage from backup archive

if [ $# -lt 1 ]; then
    echo "Usage: $0 <path_to_backup.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file ${BACKUP_FILE} does not exist."
    exit 1
fi

echo "Restoring from ${BACKUP_FILE}..."
tar -xzf "${BACKUP_FILE}"

echo "Restore completed successfully."
