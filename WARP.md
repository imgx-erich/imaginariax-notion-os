# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is the **ImaginariaX Notion OS Meta Package** - an automated setup system that creates a comprehensive Notion workspace for creative production management. It establishes interconnected databases for clients, projects, tasks, assets, budgets, talent, and project participants with proper relations between them.

The system consists of three main components:
1. **Database Creation**: Automated setup of Notion databases via the Notion API
2. **CSV Import**: Bulk import of initial data from structured CSV files  
3. **Relation Linking**: Automatic establishment of relational connections between database entries

## Key Architecture

### Core Scripts
- `setup_notion_os.sh` - Main orchestration script that creates databases and imports initial data
- `import_csv_to_notion.py` - Handles CSV-to-Notion data import with proper type mapping
- `link_relations.py` - Converts text references into proper Notion database relations

### Database Schema
The system creates 8 interconnected Notion databases:
- **Clients** (title: Name, contact info, client type)
- **Projects** (title: Project Name, linked to clients, timeline, status)  
- **Tasks** (title: Task, linked to projects, assignees, due dates, priorities)
- **Assets Library** (title: Asset Name, linked to projects, storage links, types)
- **Budgets** (title: Project, budget amounts, status)
- **Talent & Contractors** (title: Name, contact info, roles)
- **Roles** (title: Role, used for project participant assignments)
- **Project Participants** (links projects, people/orgs, and roles together)

### Data Flow
1. Initial databases created with text-based foreign key fields (e.g., "Client (text)")
2. CSV data imported with text values in these fields
3. Relations script converts text references to proper database relations
4. Template pages provide structured project documentation formats

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (only requests is required)
pip install requests
```

### Running the Full Setup
```bash
# Set required environment variables
export NOTION_API_KEY="secret_your_notion_integration_key"
export PARENT_PAGE_ID="your_notion_page_id_where_dbs_will_be_created"

# Run complete setup (creates DBs, imports CSVs, links relations)
bash setup_notion_os.sh

# Optional: Link relations after initial setup
export NOTION_API_KEY="secret_your_key"
python3 link_relations.py
```

### Development Workflows

#### CSV Import Only
```bash
# Import CSVs to existing databases
python3 import_csv_to_notion.py \
  --notion-key "$NOTION_API_KEY" \
  --notion-version "2022-06-28" \
  --db-map ".notion_state/db_ids.json" \
  --csv-dir "_csvs"
```

#### Relations Linking Only  
```bash
# Link text references to proper relations (requires NOTION_API_KEY env var)
python3 link_relations.py
```

#### Testing Individual Components
```bash
# Validate CSV structure
head -5 _csvs/*.csv

# Check database creation response
cat .notion_state/db_ids.json

# Verify current state of relations
python3 -c "
import json
from link_relations import *
with open('.notion_state/db_ids.json') as f:
    print('Database IDs:', json.load(f))
"
```

## File Structure

```
ImaginariaX_Notion_OS_Meta_Package_v5/
├── setup_notion_os.sh           # Main setup orchestrator
├── import_csv_to_notion.py      # CSV import utility
├── link_relations.py            # Relations linking utility
├── _csvs/                       # Initial data (created by setup script)
│   ├── Clients.csv
│   ├── Projects.csv
│   ├── Tasks.csv
│   └── ...
├── _imaginariax_pkg/            # Template package content
│   └── templates/               # Markdown page templates
├── .notion_state/               # Notion API state tracking
│   ├── db_ids.json             # Database ID mappings
│   └── *.create.json           # Database creation responses
└── .venv/                      # Python virtual environment
```

## Property Type Mapping

The CSV importer handles automatic type conversion:
- **Title properties**: Project names, client names, asset names
- **Rich text**: Notes, descriptions, text-based foreign keys
- **Dates**: ISO format dates (YYYY-MM-DD)
- **Numbers**: Budget amounts, numeric values
- **Select options**: Status, priority, types (predefined options)
- **Email/Phone/URL**: Validated contact information

## Relations Architecture

The system uses a two-phase approach for database relations:
1. **Phase 1**: Import with text-based references (e.g., "Client (text)" field)
2. **Phase 2**: Convert text references to proper Notion relations

Key relation mappings:
- Projects → Clients (via client name lookup)
- Tasks → Projects (via project name lookup) 
- Assets → Projects (via project name lookup)
- Budgets → Projects (via project name lookup)
- Project Participants → Projects, Talent, Roles (via name lookups)

## Environment Variables

Required:
- `NOTION_API_KEY` - Notion integration secret token
- `PARENT_PAGE_ID` - UUID of Notion page where databases will be created

Optional:
- `NOTION_VERSION` - API version (defaults to "2022-06-28")
- `DB_IDS_PATH` - Path to database IDs file (defaults to ".notion_state/db_ids.json")

## MCP Integration Notes

This repository can be used with Notion MCP tools for:
- Querying created databases (`API-post-database-query`)
- Creating additional pages (`API-post-page`)  
- Updating database properties (`API-update-a-database`)
- Retrieving database schemas (`API-retrieve-a-database`)

The `db_ids.json` file contains the database IDs needed for MCP operations.

## Common Troubleshooting

- **Database creation fails**: Verify NOTION_API_KEY has database creation permissions
- **CSV import fails**: Check CSV column names match property schema in setup script
- **Relations linking fails**: Ensure text values in source fields exactly match target titles
- **Rate limiting**: Scripts include sleep delays but may need adjustment for large datasets
