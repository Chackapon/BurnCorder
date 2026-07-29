import glob
import json
from pathlib import Path
import soundfile
import yaml


from lib.misc.configs import config
# from lib.file.cdinstance import DiscInstance


def get_frames( filename ):
    return soundfile.info(filename).frames

def milis_to_cdtime( milis_time ) -> str:
    if int(milis_time) == 0: return "0"

    total_seconds = int(milis_time) // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    milis = int(milis_time) % 1000
    frames = round(milis * 75 / 1000)

    return f"{minutes:02}:{int(seconds):02}:{frames:02}"

def frames_to_milis( frames ) -> float:
    return frames / 75 * 1000

def milis_to_frames( milis_time ) -> float:
    return milis_time / 1000 * 75

def frames_to_cdtime( frames ) -> str:
    if int(frames) == 0: return "0"

    total_seconds = int(frames) // 75
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    frames = int(frames) % 75

    return f"{minutes:02}:{int(seconds):02}:{frames:02}"


def song_preamble() -> str:
    # // Track 1
    # TRACK AUDIO
    # COPY
    # NO PRE_EMPHASIS
    # TWO_CHANNEL_AUDIO
    # ISRC "000000000000"
    return "TRACK AUDIO"

def song_cdtext( song_title: str, artist: str ) -> str:
    return f"CD_TEXT {{\n\tLANGUAGE {0} {{\n\t\tTITLE \"{song_title}\"\n\t\tPERFORMER \"{artist}\"\n\t}}\n}}"

def song_postfix( filename: str, start_timestamp: str, end_timestamp: str ) -> str:
    return f"FILE \"{filename}\" {frames_to_cdtime(start_timestamp)} {frames_to_cdtime(int(end_timestamp) - int(start_timestamp))}"



def audio_session_metadata( audio_metadata: dict ) -> str:


    # languages = list(audio_metadata["lang"].keys())

    result = "CD_TEXT {\n\tLANGUAGE_MAP {\n"
    result += f"\t\t0: EN\n"
    result += "\t}\n"


    result += f"\tLANGUAGE 0 {{\n"
    result += "\t\tTITLE \"" + audio_metadata["title"] + "\"\n"
    result += "\t\tPERFORMER \"" + audio_metadata["artist"] + "\"\n"
    result += "\t}\n"
    result += "}"

    return result

# TODO i cant include DiscInstance type hint due to circular import which suggests my object hierarchy is bad here
def generate_toc(cd):
    # str_path = str(project_path.resolve())
    export_path = cd.project_path / "assets" / "audio_session.toc" # TODO refactor to Path
    audio_metadata = json.load( open( cd.project_path / "project_metadata.json", 'r' ) )["sessions"]["audio"]

    if True:
        output_file = open(export_path, "w")
        audio_filename = str( (cd.project_path / "assets/wav" / audio_metadata["filename"]).resolve() )
        print(audio_filename)


        output_file.write("CD_ROM_XA\n")
        output_file.write( audio_session_metadata( audio_metadata ) + "\n\n")

        # tracklist_file = open("assets/tracklist", "r")
        # disc_meta = json.load(open('assets/project_metadata.json', 'r'))
        tracklist = audio_metadata["tracklist"]
        artist = audio_metadata["artist"]

        # print(tracklist_file)
        # exit()

        # tracklist = tracklist_file.read().splitlines()
        try:
            timestamps_file = open( cd.project_path.resolve() / "assets/timestamps", "r" )
        except:
            # TODO how should the timestamps file be added?
            raise RuntimeError("No timestamps file found")
        timestamps = timestamps_file.read().splitlines()

        for i in range(len(tracklist)):
            result = ""
            result += song_preamble() + '\n'
            result += song_cdtext(tracklist[i], artist) + '\n'
            result += song_postfix( audio_filename, timestamps[i], timestamps[i + 1] ) + '\n'

            output_file.write(result + '\n')

        output_file.close()

    return export_path


if __name__ == "__main__":
    pass
    # disc_meta = json.load(open( str() + '/assets/project_metadata.json' , 'r'))
    project_dir = config["DISC_INSTANCES_DIR"]
    # print( generate_toc(DiscInstance(project_dir / "ZmianyBonusCD.disc")) )
    print(get_frames('/Users/mati/PycharmProjects/ConcertRecordBurner/discs/ZmianyBonusCD.disc/assets/wav/zmiany_bonus_audio.wav'))
    # metadata['sessions']['audio']['filename']
    # disc_meta = json.load(open('assets/project_metadata.json', 'r'))
    # print(disc_meta[0])
    # print( audio_session_metadata( disc_meta[0] ) )


