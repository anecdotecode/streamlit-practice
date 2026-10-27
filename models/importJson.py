import json
from pathlib import Path

def impjson():
    json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)