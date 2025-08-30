#!/usr/bin/env python3
import os, json, time
import requests

NOTION_VERSION = os.environ.get("NOTION_VERSION", "2022-06-28")
NOTION_KEY = os.environ["NOTION_API_KEY"]
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

DB_IDS_PATH = os.environ.get("DB_IDS_PATH", ".notion_state/db_ids.json")

def notion(method, path, **kwargs):
    url = f"https://api.notion.com{path}"
    resp = requests.request(method, url, headers=HEADERS, **kwargs)
    if resp.status_code >= 300:
        raise RuntimeError(f"Notion API error {resp.status_code}: {resp.text}")
    return resp.json()

def get_db(db_id):
    return notion("GET", f"/v1/databases/{db_id}")

def update_db_add_relation(db_id, prop_name, target_db_id):
    body = {
        "properties": {
            prop_name: {
                "relation": {
                    "database_id": target_db_id,
                    "single_property": {}
                }
            }
        }
    }
    return notion("PATCH", f"/v1/databases/{db_id}", data=json.dumps(body))

def query_db(db_id, start_cursor=None, page_size=100):
    body = {"page_size": page_size}
    if start_cursor:
        body["start_cursor"] = start_cursor
    return notion("POST", f"/v1/databases/{db_id}/query", data=json.dumps(body))

def find_by_title(db_id, title_prop, value):
    body = {
        "filter": {
            "property": title_prop,
            "title": {"equals": value}
        },
        "page_size": 1
    }
    out = notion("POST", f"/v1/databases/{db_id}/query", data=json.dumps(body))
    results = out.get("results", [])
    return results[0]["id"] if results else None

def update_page_relation(page_id, prop_name, related_page_id):
    body = {
        "properties": {
            prop_name: {
                "relation": [{"id": related_page_id}]
            }
        }
    }
    return notion("PATCH", f"/v1/pages/{page_id}", data=json.dumps(body))


def extract_plain_text(prop_value):
    t = prop_value.get("type")
    if t == "rich_text":
        parts = prop_value.get("rich_text", [])
        return "".join(p.get("plain_text", "") for p in parts).strip()
    if t == "title":
        parts = prop_value.get("title", [])
        return "".join(p.get("plain_text", "") for p in parts).strip()
    return ""


def ensure_relations_and_link(db_ids):
    # Mappings: source DB -> list of conversions
    mappings = [
        {
            "db": "Projects",
            "from_prop": "Client (text)",
            "from_type": "rich_text",
            "to_prop": "Client",
            "target_db": "Clients",
            "target_title": "Name",
        },
        {
            "db": "Tasks",
            "from_prop": "Project (text)",
            "from_type": "rich_text",
            "to_prop": "Project",
            "target_db": "Projects",
            "target_title": "Project Name",
        },
        {
            "db": "Assets Library",
            "from_prop": "Project (text)",
            "from_type": "rich_text",
            "to_prop": "Project",
            "target_db": "Projects",
            "target_title": "Project Name",
        },
        {
            "db": "Budgets",
            "from_prop": "Project (text)",
            "from_type": "title",
            "to_prop": "Project",
            "target_db": "Projects",
            "target_title": "Project Name",
        },
        {
            "db": "Project Participants",
            "from_prop": "Project (text)",
            "from_type": "title",
            "to_prop": "Project",
            "target_db": "Projects",
            "target_title": "Project Name",
        },
        {
            "db": "Project Participants",
            "from_prop": "Person/Org (text)",
            "from_type": "rich_text",
            "to_prop": "Person/Org",
            "target_db": "Talent & Contractors",
            "target_title": "Name",
        },
        {
            "db": "Project Participants",
            "from_prop": "Role",
            "from_type": "rich_text",
            "to_prop": "Role (relation)",
            "target_db": "Roles",
            "target_title": "Role",
        },
    ]

    # Add relation properties if missing
    for m in mappings:
        src_db_id = db_ids[m["db"]]
        tgt_db_id = db_ids[m["target_db"]]
        db_info = get_db(src_db_id)
        if m["to_prop"] not in db_info.get("properties", {}):
            update_db_add_relation(src_db_id, m["to_prop"], tgt_db_id)
            time.sleep(0.2)

    # Link rows
    linked = {k: 0 for k in db_ids.keys()}
    for m in mappings:
        src_db_id = db_ids[m["db"]]
        tgt_db_id = db_ids[m["target_db"]]
        to_prop = m["to_prop"]
        src_prop = m["from_prop"]
        target_title = m["target_title"]

        cursor = None
        while True:
            res = query_db(src_db_id, start_cursor=cursor, page_size=50)
            for page in res.get("results", []):
                props = page.get("properties", {})
                if src_prop not in props:
                    continue
                name = extract_plain_text(props[src_prop]).strip()
                if not name:
                    continue
                # find target by title
                target_id = find_by_title(tgt_db_id, target_title, name)
                if not target_id:
                    continue
                update_page_relation(page["id"], to_prop, target_id)
                linked[m["db"]] += 1
                time.sleep(0.15)
            if not res.get("has_more"):
                break
            cursor = res.get("next_cursor")
            time.sleep(0.15)
    return linked


def main():
    with open(DB_IDS_PATH) as f:
        db_ids = json.load(f)
    linked_counts = ensure_relations_and_link(db_ids)
    print(json.dumps({"linked": linked_counts}, indent=2))

if __name__ == "__main__":
    main()

