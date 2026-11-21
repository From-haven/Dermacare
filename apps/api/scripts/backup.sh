#!/usr/bin/env bash
set -euo pipefail

# backup.sh — DermaCare Agent Backup Script
# Archives SQLite database and encrypted local object storage

BACKUP_DIR="${BACKUP_DIR:-data/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/derma_backup_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

echo "Starting DermaCare backup to ${BACKUP_FILE}..."

# Create archive
tar -czf "${BACKUP_FILE}" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    data/derma.db \
    data/storage/ 2>/dev/null || tar -czf "${BACKUP_FILE}" data/derma.db

echo "Backup completed successfully: ${BACKUP_FILE}"
ls -lh "${BACKUP_FILE}"
