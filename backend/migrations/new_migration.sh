#!/bin/sh
# Creates an empty, correctly-named migration file.
# Usage: backend/migrations/new_migration.sh add_totp_to_profiles
set -e
if [ -z "$1" ]; then
  echo "Usage: $0 <description>" >&2
  exit 1
fi
dir="$(dirname "$0")"
file="$dir/$(date -u +%Y%m%d%H%M%S)_$1.sql"
touch "$file"
echo "Created $file"
