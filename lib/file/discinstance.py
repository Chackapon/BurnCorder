import glob
import os, shutil, subprocess, json
import sys
import zipfile
from os import makedirs
from pathlib import Path
from tkinter.filedialog import asksaveasfile

import yaml

import lib.disc.drives as drives
import lib.file.toc_generator as toc_generator
import lib.disc.disclib as disclib
# from lib.ui.uilib import *
from lib.misc.cdexcept import NoAudioSource
from lib.misc.configs import disc_dir
# from filewrapper import FileWrapper
from lib.file.baseproject import BaseProjectFile
from lib.ui.uilib import Popup


# from lib import meow


# from lib.meow import config
class DiscInstance(BaseProjectFile):
    # Class attributes
    extension = ".disc"
    cextension = ".cdisc"
    template_metadata = {
        "sessions": {
            "audio": {
                "filename": None,
                "is_linked": None,
                "artist": "Artist",
                "title": "CD",
                "tracklist": [],
            }
        }
    }

    # Instance attributes
    tracklist: list
    is_multisession: bool

    # === OVERRIDES ===
    def __init__(self, project_path: Path | None = None):
        # Properties specific to the file type
        self.tracklist = []
        super().__init__(project_path)

    def _import_metadata(self):
        self.tracklist = self.metadata['sessions']['audio']['tracklist']

    def _export_metadata(self):
        self.metadata['sessions']['audio']['tracklist'] = self.tracklist

    # === NEW METHODS ===
    @property
    def is_multisession(self):
        return len(self.metadata["sessions"]) > 1

    # TODO a way to add multiple files as audio source, which are automatically merged and get track timies converted to cdframes timestamps
    def set_tracklist(self, tracklist: list):
        self.tracklist = tracklist

    def add_audio_source(self, src_path: Path, *, is_linked: bool = False):
        self.metadata['sessions']['audio']['is_linked'] = is_linked
        if is_linked:
            self.metadata['sessions']['audio']['filename'] = src_path.as_uri()

            # os.path.relpath(self.project_path / "assets/wav/", self.project_path))
        else:
            makedirs(self.project_path / "assets/wav/")
            shutil.copy2(src_path, self.project_path / "assets/wav/")
            self.metadata['sessions']['audio']['filename'] = src_path.name

            # FIXME complete the save function for both save and save as

    def add_audio_sources(self, src_dir_path):
        pass
        # TODO combine tracks into one and then put it into assets
        # TODO generatе timestamps file

    # TODO just to the setlist, or also the audio track?
    def add_track(self):
        pass

    def get_tracklist(self):
        return self.metadata["sessions"]["audio"]["tracklist"]

    # TODO consider moving into a different class
    def create_data_session(self, volume_label: str = "Data Volume"):
        self.metadata["sessions"]['data'] = {}
        self.metadata["sessions"]['data']["filename"] = "data_session.iso"
        self.metadata["sessions"]['data']["label"] = volume_label
        makedirs(self.project_path / "assets/iso/src", exist_ok=True)

    def add_iso_source(self, src_path):
        assert 'data' in self.metadata['session'].keys()
        makedirs(self.project_path / "assets/iso/src", exist_ok=True)
        shutil.copy2(src_path, self.project_path / "assets/iso/src")

    def build_iso(self):
        # TODO write ms_info into metadata
        # IDEA maybe each time check if ms_info changes and only then rebuild iso
        ms_info = drives.msinfo().decode("utf-8").splitlines()[-1]
        metadata_ms_info = self.metadata["sessions"]['data']['msinfo']
        if ms_info == metadata_ms_info:
            pass
        else:
            self.metadata["sessions"]['data']['msinfo'] = ms_info
            # TODO create the file and delete prev

        filename = self.metadata['sessions']['data']['filename']
        iso_file = self.project_path / "assets/iso/export" / filename
        volume_label = self.metadata['sessions']['data']['label']

        if not iso_file.exists():
            subprocess.run([
                "mkisofs",
                f"-C {ms_info}",
                "-V", volume_label,
                "-J", "-R",
                "-iso-level", "3",
                "-input-charset", "utf-8",
                "-o", iso_file,
                str(self.project_path / "assets/iso/src")
            ])

        # TODO add more asserts
        assert iso_file.exists()
        # verify if ms_info is good (or do I?)
        return iso_file

    def burn_cd(self):
        if self.metadata['sessions']['audio']['filename'] is None:
            raise NoAudioSource()
        # build toc file
        toc_file = toc_generator.generate_toc(self)
        if self.is_multisession:
            # TODO consider replacing with a dedicated logging system
            print("> Burning Enchanced CD")
            print("> Burning Audio CD session...")
            # detect if one session is already present

            subprocess.run(["cdrdao", "write",
                            "--multi",
                            # "--device", optical_drive, #find a way to support multiple drives!
                            toc_file])


            # build iso
            iso_file = self.build_iso()
            # TODO randomizable isos?

            # burn data
            burner_dev = drives.get_optical_drives_bus()[0]
            print("> Burning Data session...")
            drives.call_cdrecord(
                f"dev={burner_dev}",
                "-v", "-tao", "-data",
                iso_file.resolve()
            )

        else:
            print("> Burning Normal CD")
            print("> Burning Audio CD session...")
            subprocess.run(["cdrdao", "write", toc_file])

        print("> Finished burning")

    def verify_cd(self, tray: disclib.DiscTray):
        # TODO move to another class
        #  * challenge: either create new listener, pass existing disctray as argument
        #  * or move this function to DiscTray class and pass the project as an argument

        sessions = tray.sessions()
        tracks = tray.tracks()

        # TODO implement custom exceptions
        if sessions != len(self.metadata["sessions"]):
            raise RuntimeError(
                f"CD Verification Error: wrong number of sessions (expected={len(self.metadata["sessions"])}, got={sessions})")

        tracklist_len = len(self.metadata["sessions"]["audio"]["tracklist"])
        if self.is_multisession:
            if tracks != tracklist_len + 1:
                raise RuntimeError(
                    f"CD Verification Error: wrong number of tracks (multi session, expected={tracklist_len}, got={tracks})")
        else:
            if tracks != tracklist_len:
                raise RuntimeError(
                    f"CD Verification Error: wrong number of tracks (single session, expected={tracklist_len}, got={tracks})")

# class DiscInstance:
#     project_path: Path
#     project_name: str
#     is_compressed: bool
#     compressed_path: Path
#
#     metadata: dict
#
#     tracklist: list
#     is_multisession: bool





if __name__ == "__main__":
    # cd = DiscInstance(disc_dir / "ZmianyBonusCD.disc")
    # # cd = DiscInstance(disc_dir / "ZmianyBonusCD2.zip")
    # print(cd.tracklist)
    # print(cd.is_multisession)
    # cd.save(disc_dir / "ZmianyBonusCD.cdisc", overwrite=True, compressionlevel=8)
    # cd = DiscInstance(disc_dir / "ZmianyBonusCD.cdisc")
    # print(cd.tracklist)
    # print(cd.is_multisession)
    # print( Popup.asksave(disc_dir) )
    cd = DiscInstance.newf(disc_dir / "CD.disc", overwrite=False)
    # cd = DiscInstance.newf(disc_dir/ "New.test", overwrite=True, is_compressed=True)
    # cd.set_tracklist(["testsghr", "xhg"])
    # cd.save()
    cd.add_audio_source(Path("/Users/mati/PycharmProjects/ConcertRecordBurner/discs/ZmianyBonusCD.disc/assets/wav/zmiany_bonus_audio.wav"), is_linked=True)
    cd.set_tracklist(["To będzie nasz rok", "Nic", "Artysta"])
    cd.save()
    cd.burn_cd()
    # cd.save(disc_dir / "CD.cdisc", overwrite=False)
    # cd = DiscInstance(disc_dir/"Plyta.disc")
    # cd.save()
    # cd.set_tracklist(["Szypko", "Wolno"])
    # cd.add_audio_source(
    #     Path("/Users/mati/PycharmProjects/ConcertRecordBurner/discs/ZmianyBonusCD.disc/assets/wav/zmiany_bonus_audio.wav"),
    #     is_linked=False
    # )
    # input("Press Enter to continue...")
    # cd.burn_cd()
    # cd.burn_cd()
    # cd.save(disc_dir/"Płyta2.disc", compressionlevel=9, overwrite=True)
