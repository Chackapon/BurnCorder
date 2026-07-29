import ast
import os.path
import pathlib
import queue
import sys
import time
from math import floor
from time import perf_counter
# from toc_generator import milis_to_cdtime

import numpy
import pydub
import sounddevice
import soundfile


from lib.misc.configs import disc_dir
from midi import MIDI_Listener
from lib.file.discinstance import DiscInstance



def get_frames( filename ):
    return soundfile.info(filename).frames


def get_audio_device_idx(dev_name: str):
    for device_entry in sounddevice.query_devices():
        if ast.literal_eval(repr(device_entry))['name'] == dev_name:
            return ast.literal_eval(repr(device_entry))['index']
    raise RuntimeError( "No device found with name '{}'".format( dev_name ) )

CROSSFADE_DURATION = 7
PRG_CH_BUTTON_IDX = 4

class AudioRecorder:
    record_dev_idx: int
    left_ch: int
    right_ch: int
    sample_rate = 44100

    recorder_buffer: list # TODO consider changing to queue
    tracklist: list

    project_path: pathlib.Path
    output_filename: str

    midi_listener: MIDI_Listener
    
            
    def __init__(self, recording_dev_name: str):
        self.record_button_triggered = False
        self.record_dev_idx = get_audio_device_idx(recording_dev_name)

        self.recorder_buffer = []
        self.sample_rate = 44100

        self.left_ch = 1
        self.right_ch = 2
        self.midi_listener = MIDI_Listener()

    def select_channels(self, left, right):
        self.left_ch = left
        self.right_ch = right

    def set_projectfile(self, cdproject: DiscInstance):
        # Retreieve data from project file
        self.project_path = cdproject.project_path
        self.output_filename = cdproject.metadata['sessions']['audio']['filename']
        self.tracklist = cdproject.get_tracklist()

    def record_audio( self ):

        # Create audio stream
        audio_stream = self.create_audio_stream()

        # Create a file for timestamps output
        timestamps_file = open(
            os.path.join(self.project_path, "assets/wav", "timestamps"),
            "w"
        )

        # Start audio recording
        print("Recording started")
        audio_stream.start()

        # Write info for first track and handle fade in
        timestamps_file.write( "0" )
        print(f"Track 0: {self.tracklist[0]}")
        print(f"! Waiting for crossfade to end ({CROSSFADE_DURATION}s)...")
        time.sleep(CROSSFADE_DURATION)
        print("√ Ready for next input")
        self.midi_listener.wait_for_click()

        # Tracklist timestamper loop
        # TODO: add ability to skip tracks
        for track_idx in range( 1, len(self.tracklist) ):
            frames = sum(chunk.shape[0] for chunk in self.recorder_buffer)
            cd_frames = round(frames * 75 / 44100)
            timestamps_file.write( str(cd_frames) + "\n" )

            print(f"Track {track_idx+1}: {self.tracklist[track_idx]}")
            self.midi_listener.wait_for_click()

        # Handle fade out on last track and stop recording
        print(f"Reached last track, waiting for crossfade to end ({CROSSFADE_DURATION}s)...")
        time.sleep(CROSSFADE_DURATION)
        audio_stream.stop()

        # Write timestamp for the end of the audio file
        frames = sum(chunk.shape[0] for chunk in self.recorder_buffer)
        cd_frames = floor(frames * 75 / 44100)
        timestamps_file.write(str(cd_frames) + "\n")
        print("Recording stopped")

        # Close audio stream and timestamps file
        audio_stream.close()
        timestamps_file.close()

        # Process and export data
        self.export_data()

    def export_data(self) -> None:
        """
        Exports recorded audio stream data into a CD compatible WAV file. Add crossfade to the audio file
        """
        data = self.process_data()
        output_path = self.project_path / "assets/wav"
        print("Exporting data to {}".format(output_path.resolve()))

        # soundfile.write(
        #     output_path.resolve() / self.output_filename,
        #     data,
        #     samplerate=self.sample_rate,
        #     subtype="PCM_16",
        # )
        audio_segment = pydub.AudioSegment(
            data=data.tobytes(),
            frame_rate=self.sample_rate,
            sample_width=2,
            channels=2, # TODO make data driven maybe
        ).fade_in(CROSSFADE_DURATION * 1000).fade_out(CROSSFADE_DURATION * 1000)

        # Export audio
        audio_segment.export(
            output_path.resolve() / self.output_filename,
            format="wav",

        )

    def process_data(self) -> numpy.ndarray:
        """
        Converts audio stream data from float32 to int16
        :return: numpy array with audio data
        """
        audio_data = numpy.concatenate(self.recorder_buffer, axis=0)  # Convert to numpy array
        audio_int16 = numpy.int16(audio_data * 32767)  # Convert float32 (-1..1) → int16
        return audio_int16
        

    def create_audio_stream(self) -> sounddevice.InputStream:
        """
        Wrapper for sounddevice, creates a callback function for audio recording and creates an InputStream object that uses it
        :return: Audio stream object
        """
        def recorder_callback(indata, frames, _time, status):
            if status: print("> STATUS", status)

            desired_channels = indata[:, self.left_ch-1:self.right_ch]

            self.recorder_buffer.append(desired_channels.copy())
            # print(desired_channels.shape)
            # print(frames)
            # print(len(self.recorder_buffer))

        return sounddevice.InputStream(
            samplerate=self.sample_rate,
            device=self.record_dev_idx,
            dtype="float32",
            channels=2,  # TODO make data driven with checks if left and right idx are good INPUT SOURCES
            callback=recorder_callback,
        )




def main():
    # DiscInstance.new(disc_dir / "RecordingTest.disc")
    # quit()
    project = DiscInstance(disc_dir / "RecordingTest.disc")

    recorder = AudioRecorder("BlackHole 2ch")
    recorder.set_projectfile(project)

    # Start signal
    print("Press PAD_5 to start recording.")
    recorder.midi_listener.wait_for_click()

    # for device in sounddevice.query_devices():
    #     print( ast.literal_eval(repr(device)) )

    recorder.record_audio()


# import rtmidi

if __name__ == "__main__":

    main()
    pass