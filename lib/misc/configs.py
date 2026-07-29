import json
from pathlib import Path

import yaml
config = yaml.safe_load(open("/Users/mati/PycharmProjects/ConcertRecordBurner/config.yaml"))

project_dir = Path(config["PROJECTS_DIR"])
disc_dir = Path(config["DISC_INSTANCES_DIR"])

app_metadata = json.load(open("/Users/mati/PycharmProjects/ConcertRecordBurner/lib/misc/app_metadata.json"))
fileformats = app_metadata["file_formats"]

app_version = app_metadata["version"]
parsed_version = f"v{app_version[0]}.{app_version[1]}.{app_version[2]}"
if len(app_version) > 3:
    parsed_version += f" {app_version[3]}"

