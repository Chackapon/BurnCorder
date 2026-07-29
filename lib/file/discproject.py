import shutil
from pathlib import Path

from lib.disc.burner import burn_iteration
from lib.misc.configs import project_dir, disc_dir, parsed_version
from lib.file.discinstance import DiscInstance
from lib.file.baseproject import BaseProjectFile


class DiscProject(BaseProjectFile):
    # Class attributes
    extension = ".dproject"
    cextension = ".cdproject"
    template_metadata = {
        "app_version": parsed_version,
        "disc_instances": []
    }

    # Instance attributes
    discs_dir: Path
    disc_list: list[dict]
    disc_instances: list[DiscInstance]

    # === OVERRIDES ===
    def __init__(self, project_path: Path | None = None):
        # Properties specific to the file type
        self.disc_list = []
        super().__init__(project_path)
        discs_dir = self.project_path / "assets" / "discs"

    def _import_metadata(self):
        self.disc_list = self.metadata['disc_instances']

    def _export_metadata(self):
        self.metadata['disc_instances'] = self.disc_list

    # === NEW METHODS ===
    def add_disc(self, disc: DiscInstance, is_linked: bool = False):

        if is_linked:
            disc_path = str(disc.project_path.as_uri())

        else:
            shutil.copytree(disc.project_path, self.discs_dir / disc.project_path.name)
            disc_path = str(disc.project_path.name)

        new_disc_metadata = {
            "is_linked": is_linked,
            "path": disc_path
        }
        self.disc_list.append(new_disc_metadata)

    def initiate_discs(self):
        for disc in self.disc_list:
            if disc['is_linked']:
                self.disc_instances.append(DiscInstance(disc['path']))
            else:
                self.disc_instances.append(DiscInstance(self.discs_dir / disc['path']))

    # TODO combine with lib.burner somehow, should it even be a DiscProject method?
    def burn(self, series: int):
        for i in range(series):
            for disc in self.disc_instances:
                disc.burn_cd()



if __name__ == "__main__":
    project = DiscProject.newf(project_dir / "ZmianyDeluxe", overwrite=True, is_compressed=False)
    project.add_disc(DiscInstance(disc_dir / "ZmianyBonusCD.disc"), is_linked=True)
    project.save()