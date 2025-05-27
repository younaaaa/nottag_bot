#!/bin/bash

BACKUP_DIR="db_backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/backup_$DATE.sql"

docker exec musicbot_db pg_dump -U postgres musicbot > $FILE
gzip $FILE