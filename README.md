# ImaginariaX Notion OS Meta Package

An automated setup system that creates a comprehensive Notion workspace for creative production management. Establishes interconnected databases for clients, projects, tasks, assets, budgets, talent, and project participants with proper relations between them.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Notion API integration token
- Notion page where databases will be created

### Setup
1. Clone this repository
2. Set up your environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install requests
   ```

3. Configure environment variables:
   ```bash
   export NOTION_API_KEY="secret_your_notion_integration_key"
   export PARENT_PAGE_ID="your_notion_page_id_where_dbs_will_be_created"
   ```

4. Run the complete setup:
   ```bash
   bash setup_notion_os.sh
   ```

## 🏗️ System Architecture

The system creates **8 interconnected Notion databases**:

- **Clients** - Contact info, client types, notes
- **Projects** - Project details, timelines, status, linked to clients
- **Tasks** - Task management, assignees, due dates, priorities
- **Assets Library** - Asset storage, project links, types
- **Budgets** - Project budgets, financial tracking
- **Talent & Contractors** - People and organizations
- **Roles** - Role definitions for project assignments
- **Project Participants** - Links projects, people, and roles

## 📋 Features

- **Automated Database Creation** - Creates all databases with proper schema via Notion API
- **CSV Data Import** - Bulk imports initial data with type-aware property mapping
- **Relation Linking** - Converts text references to proper Notion database relations
- **Project Templates** - Ready-to-use templates for different project types
- **Production Management** - Complete workflow for creative production tracking

## 🔧 Development Workflows

### CSV Import Only
```bash
python3 import_csv_to_notion.py \
  --notion-key "$NOTION_API_KEY" \
  --notion-version "2022-06-28" \
  --db-map ".notion_state/db_ids.json" \
  --csv-dir "_csvs"
```

### Relations Linking Only
```bash
python3 link_relations.py
```

### Testing Components
```bash
# Validate CSV structure
head -5 _csvs/*.csv

# Check database IDs
cat .notion_state/db_ids.json
```

## 📁 Project Structure

```
ImaginariaX_Notion_OS_Meta_Package_v5/
├── setup_notion_os.sh           # Main setup orchestrator
├── import_csv_to_notion.py      # CSV import utility
├── link_relations.py            # Relations linking utility
├── _csvs/                       # Initial data CSVs
├── _imaginariax_pkg/templates/  # Project templates
├── WARP.md                      # Warp AI development guide
└── README.md                    # This file
```

## 🔗 MCP Integration

This repository works with Notion MCP tools:
- Query databases (`API-post-database-query`)
- Create pages (`API-post-page`)
- Update properties (`API-update-a-database`)
- Retrieve schemas (`API-retrieve-a-database`)

## 🛠️ Environment Variables

**Required:**
- `NOTION_API_KEY` - Notion integration secret token
- `PARENT_PAGE_ID` - UUID of Notion page where databases will be created

**Optional:**
- `NOTION_VERSION` - API version (defaults to "2022-06-28")
- `DB_IDS_PATH` - Path to database IDs file (defaults to ".notion_state/db_ids.json")

## 🚨 Troubleshooting

- **Database creation fails**: Verify NOTION_API_KEY has database creation permissions
- **CSV import fails**: Check CSV column names match property schema in setup script
- **Relations linking fails**: Ensure text values in source fields exactly match target titles
- **Rate limiting**: Scripts include sleep delays but may need adjustment for large datasets

## 📄 License

This project is open source. Feel free to use, modify, and distribute as needed for your creative production workflows.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Created by ImaginariaX for streamlined creative production management in Notion.**
