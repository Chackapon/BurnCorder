import pty
import threading
import subprocess
import os

import select
from abc import ABC, abstractmethod
from lib.file.discinstance import DiscInstance


class ForegroundListener:
    _cmd: list[str]

    def __init__( self, cmd: list[str] ):
        self._cmd = cmd

class BackgroundListener( threading.Thread ):
    _stop_event: threading.Event
    _proc: subprocess.Popen
    _cmd: list[str]
    _master_fd: int

    def __init__( self, cmd: list[str] ):
        threading.Thread.__init__( self )
        self._cmd = cmd
        self._stop_event = threading.Event()

    def run(self):
        self._master_fd, slave_fd = pty.openpty()
        self._proc = subprocess.Popen(
            self._cmd,
            stdout=slave_fd,
        )
        os.close(slave_fd)

        while not self._stop_event.is_set():
            read, write, exception = select.select([self._master_fd], [], [], 0.1)
            if self._stop_event.is_set():
                os.close(self._master_fd)
                break

            if read: self.process_output()

        self._proc.terminate()

    def stop(self):
        self._stop_event.set()

    def process_output(self):
        data = os.read(self._master_fd, 4096).split()
        # print("* Read data")
        print("> ", data)


class DrUtilProcess( BackgroundListener ):
    _device_name: str

    media_state = b'(null)'
    prev_media_state = b'(null)'
    tray_open = b'(null)'
    prev_tray_open = b'(null)'
    is_blank = b'(null)'
    is_erasable = b'(null)'
    dev_disk = b'(null)'
    disc_sessions = b'(null)'
    disc_tracks = b'(null)'


    def __init__( self ):
        super().__init__(["drutil", "poll"])

    def process_output(self):
        data = os.read(self._master_fd, 4096).split()
        # print("* Read data")
        # print("> ", data)
        if b'DRDeviceAppearedNotification' in data:
            self._device_name = ' '.join([word.decode() for word in data[1:]])[1:-1]
            # print(self._device_name)
        if b'-DRDeviceMediaStateKey:' in data:
            idx = data.index(b'-DRDeviceMediaStateKey:')
            self.media_state = data[idx + 3]
            self.prev_media_state = data[idx + 1]
            # print(self.media_state.decode())
        if b'-DRDeviceIsTrayOpenKey:' in data:
            idx = data.index(b'-DRDeviceIsTrayOpenKey:')
            self.tray_open = data[idx + 3]
            self.prev_tray_open = data[idx + 1]
        if b'DRDeviceMediaIsBlankKey' in data:
            idx = data.index(b'DRDeviceMediaIsBlankKey')
            self.is_blank = data[idx + 2]
            # print(self.is_blank)
        if b'DRDeviceMediaIsErasableKey' in data:
            idx = data.index(b'DRDeviceMediaIsErasableKey')
            self.is_erasable = data[idx + 2]
            # print(self.is_erasable)
        if b'DRDeviceMediaBSDNameKey' in data:
            idx = data.index(b'DRDeviceMediaBSDNameKey')
            self.dev_disk = data[idx + 2]
        if b'DRDeviceMediaSessionCountKey' in data:
            idx = data.index(b'DRDeviceMediaSessionCountKey')
            self.disc_sessions = data[idx + 2]
        if b'DRDeviceMediaTrackCountKey' in data:
            idx = data.index(b'DRDeviceMediaTrackCountKey')
            self.disc_tracks = data[idx + 2]


class DiscTrayBase(ABC):
    """
    Base class for handling disc tray operations. Inheriting classes are supposed to implement OS specific disc APIs
    """

    @abstractmethod
    def start_listening(self):
        """

        """
        pass

    @abstractmethod
    def stop_listening(self):
        pass

    @abstractmethod
    def wait_for_cd(self):
        pass

    @abstractmethod
    def is_blank(self):
        pass

    @abstractmethod
    def is_erasable(self):
        pass

    @abstractmethod
    def sessions(self) -> int:
        pass

    @abstractmethod
    def tracks(self) -> int:
        pass

    @abstractmethod
    def eject_cd(self):
        pass

    @abstractmethod
    def erase_cd(self):
        pass

    # @abstractmethod
    # def burn_cd(self, cd: DiscInstance):
    #     pass

    @abstractmethod
    def verify_cd(self, cd: DiscInstance):
        pass

class DiscTrayOSX(DiscTrayBase):
    _state_listener: DrUtilProcess

    def __init__( self ):
        self._state_listener = DrUtilProcess()

    def start_listening(self):
        self._state_listener.start()

    def stop_listening(self):
        self._state_listener.stop()
        self._state_listener.join()

    def wait_for_cd(self):
        while not self._state_listener.media_state == b'DRDeviceMediaStateMediaPresent':
            pass

    def is_blank(self):
        return self._state_listener.is_blank == b'1;'

    def is_erasable(self):
        return self._state_listener.is_erasable == b'1;'

    def sessions(self) -> int:
        return int(self._state_listener.disc_sessions.decode("utf-8").replace(';',''))

    def tracks(self) -> int:
        return int(self._state_listener.disc_tracks.decode("utf-8").replace(';',''))

    def eject_cd(self):
        subprocess.run(["drutil", "eject"])

    def erase_cd(self):
        subprocess.run(["hdiutil", "burn", "-erase"])

    def verify_cd(self, cd: DiscInstance):

        sessions = self.sessions()
        tracks = self.tracks()

        # TODO implement custom exceptions
        if sessions != len(cd.metadata["sessions"]):
            raise RuntimeError(
                f"CD Verification Error: wrong number of sessions (expected={len(cd.metadata["sessions"])}, got={sessions})")

        tracklist_len = len(cd.metadata["sessions"]["audio"]["tracklist"])
        if cd.is_multisession:
            if tracks != tracklist_len + 1:
                raise RuntimeError(
                    f"CD Verification Error: wrong number of tracks (multi session, expected={tracklist_len+1}, got={tracks})")
        else:
            if tracks != tracklist_len:
                raise RuntimeError(
                    f"CD Verification Error: wrong number of tracks (single session, expected={tracklist_len}, got={tracks})")






if __name__ == "__main__":

    tray = DiscTrayOSX()
    tray.start_listening()

    for i in range(2):
        print("Waiting for a CD...")
        tray.wait_for_cd()
        print("Detected CD")
        print("Is it blank?", tray.is_blank())
        print("Is it erasable?", tray.is_erasable())
        if not tray.is_blank() and tray.is_erasable():
            print("Can erase CD")
            tray.erase_cd()
        tray.eject_cd()

    tray.stop_listening()
