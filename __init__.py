import subprocess
from pathlib import Path
from subprocess import Popen

from pynicotine.pluginsystem import BasePlugin

VERBOSE = True


class Plugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Settings code

        if VERBOSE:
            self.log("Plugin settings initialized")

    def download_finished_notification(
        self, user: str, virtual_path: str, real_path: str
    ):
        if VERBOSE:
            self.log(
                f"Finished downloading {virtual_path} from user {user}."
                f"Saved at {real_path}"
            )

        extension = real_path.split(".")[-1]
        if extension.lower() in ["aiff", "flac", "mp3", "ogg", "wav"]:
            self.generate_spectrogram(real_path)

    def generate_spectrogram(self, audio_file_path: str):
        input_file_path = Path(audio_file_path)
        input_filename = input_file_path.stem
        input_directory = input_file_path.parent
        output_file_path = Path(input_directory, f"{input_filename}.png")

        if not input_file_path.exists():
            self.log(f"File not found: {input_file_path}")

        if VERBOSE:
            self.log(f"Generating spectrogram for '{input_filename}...'")

        arguments = self.build_arguments(input_file_path, output_file_path)

        try:
            Popen(
                arguments,
                stdout=subprocess.PIPE,
                shell=True,
                start_new_session=True,
            )

            self.log(f"Spectrogram saved at {output_file_path}")

        except Exception as error:
            self.log(f"An error occurred: {error}")

    def build_arguments(self, input_file_path: Path, output_file_path: Path) -> list:
        command = [
            "sox",
            input_file_path.as_posix(),
            "-n",
            "remix",
            "1",
            "spectrogram",
            "-o",
            output_file_path.as_posix(),
        ]

        return command
