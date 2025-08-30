#!/usr/bin/env bash
set -euo pipefail

# ===== ImaginariaX Notion OS – Automated Setup =====
# Requirements:
#   - NOTION_API_KEY (env var)
#   - PARENT_PAGE_ID (env var)  -> the Notion page under which DBs will be created
#   - curl, python3 available
#
# Usage:
#   export NOTION_API_KEY="secret_xxx"
#   export PARENT_PAGE_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#   bash setup_notion_os.sh
#
# This script will:
#   1) Unzip template package and starter CSVs
#   2) Create Notion databases (Clients, Projects, Tasks, Assets, Budgets, Talent & Contractors, Roles, Project Participants)
#   3) Import CSV rows into each database via the Notion API
#
# Notes:
#   - After DB creation, you may still want to import the Markdown page templates by dragging them into Notion.
#   - Relations cannot be established by raw CSV text; we create properties and seed rows first.
#     You can then convert/attach relations in the Notion UI or extend the importer to resolve IDs by name.

NOTION_VERSION="2022-06-28"

if [[ -z "${NOTION_API_KEY:-}" || -z "${PARENT_PAGE_ID:-}" ]]; then
  echo "ERROR: Please export NOTION_API_KEY and PARENT_PAGE_ID before running."
  exit 1
fi

PKG="ImaginariaX_Notion_OS_Template_Package.zip"
STARTER_ZIP="Starter_CSVs.zip"

if [[ ! -f "$PKG" ]]; then
  echo "ERROR: $PKG not found in current directory. Place this script next to the package and run again."
  exit 1
fi

echo "Unzipping template package..."
rm -rf _imaginariax_pkg && mkdir -p _imaginariax_pkg
unzip -q "$PKG" -d _imaginariax_pkg

if [[ ! -f "_imaginariax_pkg/${STARTER_ZIP}" ]]; then
  echo "ERROR: Starter CSVs not found in package."
  exit 1
fi

echo "Unzipping starter CSVs..."
rm -rf _csvs && mkdir -p _csvs
unzip -q "_imaginariax_pkg/${STARTER_ZIP}" -d _csvs

# Create a directory to store IDs
STATE_DIR=".notion_state"
mkdir -p "$STATE_DIR"

api_create_db () {
  local title="$1"
  local properties_json="$2"
  echo "Creating database: ${title}"
  curl -sS -X POST "https://api.notion.com/v1/databases"     -H "Authorization: Bearer ${NOTION_API_KEY}"     -H "Content-Type: application/json"     -H "Notion-Version: ${NOTION_VERSION}"     -d "{
      \"parent\": { \"type\": \"page_id\", \"page_id\": \"${PARENT_PAGE_ID}\" },
      \"title\": [{ \"type\": \"text\", \"text\": { \"content\": \"${title}\" } }],
      \"properties\": ${properties_json}
    }" | tee "${STATE_DIR}/${title}.create.json" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
}

# Define property schemas (minimal but aligned with CSVs)
PROPS_CLIENTS='{
  "Name": {"title": {}},
  "Client Type": {"select":{"options":[{"name":"Individual"},{"name":"Organization"}]}},
  "Primary Contact":{"rich_text":{}},
  "Email":{"email":{}},
  "Phone":{"phone_number":{}},
  "Website":{"url":{}},
  "Notes":{"rich_text":{}}
}'
PROPS_PROJECTS='{
  "Project Name":{"title":{}},
  "Type":{"select":{"options":[{"name":"Film / Episodic"},{"name":"Game Development"},{"name":"Immersive Installation"}]}},
  "Status":{"select":{"options":[{"name":"Active"},{"name":"Proposal"},{"name":"R&D"},{"name":"On Hold"},{"name":"Complete"}]}},
  "Client (text)":{"rich_text":{}},
  "Start":{"date":{}},
  "End":{"date":{}},
  "Summary":{"rich_text":{}}
}'
PROPS_TASKS='{
  "Task":{"title":{}},
  "Project (text)":{"rich_text":{}},
  "Assignee (text)":{"rich_text":{}},
  "Due":{"date":{}},
  "Status":{"select":{"options":[{"name":"Planned"},{"name":"In Progress"},{"name":"Blocked"},{"name":"Done"}]}},
  "Priority":{"select":{"options":[{"name":"Low"},{"name":"Medium"},{"name":"High"}]}} 
}'
PROPS_ASSETS='{
  "Asset Name":{"title":{}},
  "Project (text)":{"rich_text":{}},
  "Type":{"select":{"options":[{"name":"Artwork"},{"name":"Video"},{"name":"Executable"},{"name":"Document"}]}},
  "Storage Link":{"url":{}},
  "Notes":{"rich_text":{}}
}'
PROPS_BUDGETS='{
  "Project (text)":{"title":{}},
  "Budget (USD)":{"number":{"format":"number"}},
  "Status":{"select":{"options":[{"name":"Allocated"},{"name":"Pending"},{"name":"Early"}]}} 
}'
PROPS_TALENT='{
  "Name":{"title":{}},
  "Entity Type":{"select":{"options":[{"name":"Individual"},{"name":"Organization"}]}},
  "Primary Role":{"rich_text":{}},
  "Email":{"email":{}},
  "Phone":{"phone_number":{}},
  "Company":{"rich_text":{}},
  "Notes":{"rich_text":{}}
}'
PROPS_ROLES='{
  "Role":{"title":{}}
}'
PROPS_PARTICIPANTS='{
  "Project (text)":{"title":{}},
  "Person/Org (text)":{"rich_text":{}},
  "Role":{"rich_text":{}},
  "Start":{"date":{}},
  "End":{"date":{}}
}'

# Create databases and capture IDs
DB_CLIENTS_ID=$(api_create_db "Clients" "$PROPS_CLIENTS")
DB_PROJECTS_ID=$(api_create_db "Projects" "$PROPS_PROJECTS")
DB_TASKS_ID=$(api_create_db "Tasks" "$PROPS_TASKS")
DB_ASSETS_ID=$(api_create_db "Assets Library" "$PROPS_ASSETS")
DB_BUDGETS_ID=$(api_create_db "Budgets" "$PROPS_BUDGETS")
DB_TALENT_ID=$(api_create_db "Talent & Contractors" "$PROPS_TALENT")
DB_ROLES_ID=$(api_create_db "Roles" "$PROPS_ROLES")
DB_PARTICIPANTS_ID=$(api_create_db "Project Participants" "$PROPS_PARTICIPANTS")

echo "{}" > "${STATE_DIR}/db_ids.json"
python3 - <<PY
import json, os
state = {
  "Clients": os.environ["DB_CLIENTS_ID"],
  "Projects": os.environ["DB_PROJECTS_ID"],
  "Tasks": os.environ["DB_TASKS_ID"],
  "Assets Library": os.environ["DB_ASSETS_ID"],
  "Budgets": os.environ["DB_BUDGETS_ID"],
  "Talent & Contractors": os.environ["DB_TALENT_ID"],
  "Roles": os.environ["DB_ROLES_ID"],
  "Project Participants": os.environ["DB_PARTICIPANTS_ID"],
}
open("${STATE_DIR}/db_ids.json","w").write(json.dumps(state, indent=2))
PY

echo "Database IDs stored in ${STATE_DIR}/db_ids.json"

# Import CSVs into each database via helper Python script
python3 import_csv_to_notion.py   --notion-key "${NOTION_API_KEY}"   --notion-version "${NOTION_VERSION}"   --db-map "${STATE_DIR}/db_ids.json"   --csv-dir "_csvs"

echo "=== Setup complete ==="
echo "Next steps:"
echo "  1) In Notion, convert '(text)' columns to Relations where needed."
echo "  2) Drag Markdown templates into Notion (from templates/ in the package)."
echo "  3) Optionally create a 'Home Dashboard' page using the provided markdown."
