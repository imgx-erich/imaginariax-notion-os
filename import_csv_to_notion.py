#!/usr/bin/env python3
import os, csv, json, argparse, time
import requests

def create_page(notion_key, notion_version, db_id, prop_map, row):
    headers = {
        "Authorization": f"Bearer {notion_key}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version
    }
    # Build properties payload: map each CSV column to appropriate Notion property type
    props = {}
    for col, val in row.items():
        if val is None:
            val = ""
        # Priority: explicit type hints override generic "(text)" handling
        if col in prop_map.get("title_props", []):
            props[col] = {"title":[{"type":"text","text":{"content": val or ""}}]}
        elif col in prop_map.get("email_props", []):
            props[col] = {"email": val or None}
        elif col in prop_map.get("url_props", []):
            props[col] = {"url": val or None}
        elif col in prop_map.get("phone_props", []):
            props[col] = {"phone_number": val or None}
        elif col in prop_map.get("date_props", []):
            props[col] = {"date": {"start": val}} if val else {"date": None}
        elif col in prop_map.get("number_props", []):
            try:
                num = float(val) if val else None
            except:
                num = None
            props[col] = {"number": num}
        elif col in prop_map.get("select_props", []):
            props[col] = {"select": {"name": val}} if val else {"select": None}
        elif col.lower().endswith("(text)"):
            # Keep the original column/property name (including "(text)") so it matches the DB schema
            props[col] = {"rich_text":[{"type":"text","text":{"content": val}}]} if val else {"rich_text":[]}
        else:
            # default to rich_text
            props[col] = {"rich_text":[{"type":"text","text":{"content": val}}]} if val else {"rich_text":[]}

    payload = {"parent": {"database_id": db_id}, "properties": props}
    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(payload))
    if resp.status_code >= 300:
        raise RuntimeError(f"Failed to create page in DB {db_id}: {resp.status_code} {resp.text}")
    return resp.json()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notion-key", required=True)
    ap.add_argument("--notion-version", default="2022-06-28")
    ap.add_argument("--db-map", required=True, help="JSON file with database names to IDs")
    ap.add_argument("--csv-dir", required=True, help="Folder containing CSVs")
    args = ap.parse_args()

    with open(args.db_map) as f:
        db_ids = json.load(f)

    # Define property type hints for importer (helps map CSV columns)
    prop_hints = {
        "Clients": {
            "title_props": ["Name"],
            "email_props": ["Email"],
            "url_props": ["Website"],
            "phone_props": ["Phone"],
            "select_props": ["Client Type"]
        },
        "Projects": {
            "title_props": ["Project Name"],
            "date_props": ["Start", "End"],
            "select_props": ["Type", "Status"]
        },
        "Tasks": {
            "title_props": ["Task"],
            "date_props": ["Due"],
            "select_props": ["Status", "Priority"]
        },
        "Assets Library": {
            "title_props": ["Asset Name"],
            "url_props": ["Storage Link"],
            "select_props": ["Type"]
        },
        "Budgets": {
            "title_props": ["Project (text)"],
            "number_props": ["Budget (USD)"],
            "select_props": ["Status"]
        },
        "Talent & Contractors": {
            "title_props": ["Name"],
            "email_props": ["Email"],
            "phone_props": ["Phone"],
            "select_props": ["Entity Type"]
        },
        "Roles": {
            "title_props": ["Role"]
        },
        "Project Participants": {
            "title_props": ["Project (text)"],
            "date_props": ["Start","End"]
        }
    }

    # Map CSV filenames to DB names
    file_map = {
        "Clients.csv": "Clients",
        "Projects.csv": "Projects",
        "Tasks.csv": "Tasks",
        "Assets_Library.csv": "Assets Library",
        "Budgets.csv": "Budgets",
        "Talent_Contractors.csv": "Talent & Contractors",
        "Roles.csv": "Roles",
        "Project_Participants.csv": "Project Participants"
    }

    for csv_name, db_name in file_map.items():
        path = os.path.join(args.csv_dir, csv_name)
        if not os.path.exists(path):
            print(f"[WARN] Missing CSV: {csv_name}, skipping…")
            continue
        print(f"Importing {csv_name} → {db_name}")
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                create_page(args.notion_key, args.notion_version, db_ids[db_name], prop_hints[db_name], row)
        time.sleep(0.3)  # friendly pacing

if __name__ == "__main__":
    main()
