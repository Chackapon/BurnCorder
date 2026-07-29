from pathlib import Path

import yaml

if __name__ == "__main__":

    current_dir = Path.cwd()
    default_cfg = {
        "VOLUME_DIR": "Volumes",
        "TEMP_DIR": str(current_dir / "temp"),
        "DISC_INSTANCES_DIR": str(current_dir / "discs"),
        "PROJECTS_DIR": str(current_dir / "projects")
    }

    if not (current_dir / "config.yaml").exists():
        with open(str(current_dir / "config.yaml"), "w") as f:
            yaml.dump(default_cfg, f, default_flow_style=False)
        print(f"created default user config file at {current_dir}/config.yaml")
    else:
        print("config.yaml already exists")