import glob
import os
import shutil
import zipfile, json
from abc import abstractmethod, ABC
from os import makedirs
from pathlib import Path
from typing import Self

from lib.misc.configs import config, fileformats, project_dir, disc_dir

# TODO where should the UI object be created?
import lib.ui.uilib as uilib
ui = uilib.UI( uilib.UIMode.GUI )


class BaseProjectFile(ABC):
    extension: str
    cextension: str
    template_metadata: dict


    project_path: Path
    is_compressed: bool
    original_path: Path

    metadata: dict

    # TODO do i need this actually?
    def __init__(self, project_path: Path | None = None ) -> None:
        if not project_path is None: self.load(project_path)

    def __del__(self):
        try:
            if self.is_compressed: shutil.rmtree(self.project_path)
        except AttributeError: pass # this attribute is absent if it's an object without an initialized path so also no need to clean up after it

    @classmethod
    def get_extension(cls, compressed: bool) -> str:
        if compressed:
            return cls.cextension
        else:
            return cls.extension

    @classmethod
    def format_filename(cls, filename: str | None, is_compressed: bool) -> str:
        extension = cls.get_extension(is_compressed)
        if filename is None:
            filename = "Untitled"
        if not filename.endswith(extension): # extension must include dot!
            filename += extension
        return filename

    @classmethod
    def file_overwrite_handle(cls, dir_path: Path, overwrite: bool) -> Path:
        # TODO consider moving out of the class as cls is unused
        """
        Handle file request with duplicate name. If there's no file with the same name returns dir_path. If there are duplicates, function either
        properly overwrites the old file (removes the old version and returns unchanged dir_path) or creates a unique file name
        :param dir_path: Path of the file to be created
        :param overwrite: When set to true, file is automatically overwritten. If false, user is prompted to choose
        :return: Path object with a unique version of requested filename
        """
        # File overwrite handling, return unique filename based on temp filename
        if dir_path.exists():
            # TODO replace with argument for overwrite function
            if overwrite or ui.ask_overwrite():
                # TODO consider making a separate function
                if fileformats[dir_path.suffix]['is_compressed']:
                    os.remove(dir_path)
                else:
                    shutil.rmtree(dir_path)
            else:
                n = len(glob.glob(f"{dir_path.parent}/{dir_path.stem}*{dir_path.suffix}"))
                filename = f"{dir_path.stem} ({n}){dir_path.suffix}"
                dir_path = dir_path.parent / filename
        return dir_path

    @classmethod
    def new(cls, dir_path: Path, *, overwrite=False, is_compressed: bool | None = None) -> Path:

        # Deduce compression type if not explicitly given
        if is_compressed is None:
            match dir_path.suffix:
                case cls.extension:
                    is_compressed = False
                case cls.cextension:
                    is_compressed = True
                case _:
                    # TODO custom error
                    raise RuntimeError(f"Couldn't deduce if compression is desired (Invalid extension)")

        # Doing this so the type checker leaves me alone
        is_compressed = bool(is_compressed)

        # Select file extension
        extension = cls.get_extension(is_compressed)

        # If no filename was given,
        print("dir_path", dir_path)
        print(dir_path.is_dir())
        if dir_path.is_dir() and dir_path.suffix != cls.extension:
            dir_path = dir_path / "Untitled"

        # Temp filename variable, add extension if none was provded
        # TODO consider extracting method for future save popup with file selection type
        filename = dir_path.name
        if not filename.endswith(extension): filename += extension

        # Handle duplicate file, get a unique file name
        unique_path = cls.file_overwrite_handle(dir_path.parent / filename, overwrite)

        # Create the desired file
        if is_compressed:
            with zipfile.ZipFile(unique_path, 'w') as zip_file:
                zip_file.mkdir("assets")
                zip_file.writestr("project_metadata.json", json.dumps(cls.template_metadata, indent=4))
        else:
            makedirs(unique_path / "assets", exist_ok=True)
            with open(unique_path / "project_metadata.json", "w") as metadata_file:
                metadata_file.write(json.dumps(cls.template_metadata, indent=4))

        return unique_path



    @classmethod
    def newf(cls, dir_path: Path, *, overwrite=False, is_compressed=None) -> Self:
        new_file_path = cls.new(dir_path, overwrite=overwrite, is_compressed=is_compressed)
        print( new_file_path )
        return cls( new_file_path )

    def save(self, export_path: Path | None = None, *, overwrite = False, compressionlevel: int = 0) -> Path:

        # FORMAT SPECIFIC
        self._export_metadata()

        # Update json metadata file
        with open(self.project_path / "project_metadata.json", "w") as metadata_file:
            metadata_file.write(json.dumps(self.metadata, indent=4))

        if export_path is None:
            # Save mode
            if self.is_compressed:
                export_path = self.original_path # TODO have this path separation done more elegantly
            else:
                export_path = self.project_path
        else:
            # Save as mode
            export_path = self.file_overwrite_handle(export_path, overwrite)

        # Identify if file is to be saved as compressed or not
        is_export_compressed = fileformats[export_path.suffix]['is_compressed']

        # Save project contents to export destination
        if is_export_compressed:
            with zipfile.ZipFile(
                    export_path,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=compressionlevel
            ) as zip_file:
                for file in self.project_path.rglob('*'):
                    zip_file.write(file, file.relative_to(self.project_path))

        else:
            makedirs(export_path, exist_ok=True)
            for file in self.project_path.rglob('*'):
                if file.is_file():
                    try:
                        shutil.copy2(file, export_path / file.relative_to(self.project_path), )
                    except shutil.SameFileError:
                        pass

        return export_path


    def savef(self, export_path: Path | None = None, *, overwrite = False, compressionlevel: int = 0):
        # TODO what is the return type??
        return type(self)( self.save(export_path, overwrite=overwrite, compressionlevel=compressionlevel) )

    # TODO update to current disc file structure
    def load(self, import_path: Path) -> None:

        if not import_path.exists():
            raise RuntimeError(f"Trying to load file that doesn't exist: {import_path.name}")

        try:
            self.is_compressed = fileformats[import_path.suffix]['is_compressed']
        except KeyError:
            raise RuntimeError(f"Unknown file format: {import_path.suffix}; could not determine compression")

        if self.is_compressed:
            self.original_path = import_path
            self.project_path = Path(config['TEMP_DIR']) / "active/disc" / import_path.stem
            os.makedirs(self.project_path, exist_ok=True)
            with zipfile.ZipFile(import_path, 'r') as zip_file:
                # zip_file.printdir()
                zip_file.extractall(self.project_path)
        else:
            self.project_path = import_path

        print(f"> Loading {fileformats[import_path.suffix]['description']} file '{import_path.name}' at path {self.project_path.resolve()}")
        # TODO original path only exists for compressed format, is that good?
        # print(self.project_path, self.original_path, self.is_compressed)

        self.metadata = json.load(open(str(self.project_path.resolve() / "project_metadata.json"), 'r'))

        # FORMAT SPECIFIC
        self._import_metadata()

    @abstractmethod
    def _import_metadata(self):
        pass

    @abstractmethod
    def _export_metadata(self):
        pass



if __name__ == "__main__":
    pass
    # cd = DiscInstance.new( disc_dir / "Test.disc" )
    # print(cd.tracklist, cd.is_compressed)
    # cd.set_tracklist(["Meow", "Artysya"])
    # cd.save()
    # DiscInstance(disc_dir / "Test.disc").save( disc_dir/"Test2.cdisc" )