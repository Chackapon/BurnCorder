import json
from pathlib import Path

import yaml
config = yaml.safe_load(open("/Users/mati/PycharmProjects/ConcertRecordBurner/config.yaml"))

project_dir = Path(config["PROJECTS_DIR"])
disc_dir = Path(config["DISC_INSTANCES_DIR"])

fileformats = json.load(open("/Users/mati/PycharmProjects/ConcertRecordBurner/lib/misc/file_formats.json"))


