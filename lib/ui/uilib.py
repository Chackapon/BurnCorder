from enum import Enum
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from typing import Any, Generator


class Popup:
    filepath: list[Path] | Path

    @staticmethod
    def askfile(default_path: Path, *, filetypes: list = []) -> Path:
        return Path(filedialog.askopenfilename( initialdir=default_path, filetypes=filetypes ))

    @staticmethod
    def asksave(default_path: Path) -> Path:
        return Path(filedialog.asksaveasfilename( initialdir=default_path ))


    @staticmethod
    def askfiles(default_path: Path, *, filetypes: list = []) -> Generator[Path, Any, None]:
        for filepath in filedialog.askopenfilenames( initialdir=default_path, filetypes=filetypes ):
            yield Path(filepath)

    @staticmethod
    def askdir(default_path: Path) -> Path:
        return Path( filedialog.askdirectory( initialdir=default_path ) )

    @staticmethod
    def bool_dialog(msg: str, title: str = "Confirmation") -> bool:
        return messagebox.askyesno(title, msg)

disc_instance_filetypes = [
    ("CD Disc instance", "*.disc"),
]

class UIMode(Enum):
    GUI = "Graphical"
    CLI = "Console"

class UI:
    mode: UIMode

    def __init__(self, mode: UIMode):
        self.mode = mode

    def __str__(self):
        return f"{self.mode.name} User Interface"

    def ask_overwrite(self):
        if self.mode == UIMode.GUI:
            return Popup.bool_dialog("File with this name already exists, overwrite?")
        else:
            return input("File with this name already exists, overwrite? (y/n) ") == "y"

if __name__ == "__main__":

    file_selector = Popup()
    for path in file_selector.askfiles():
        print(path.name)
