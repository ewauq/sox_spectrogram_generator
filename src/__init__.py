import shutil
import subprocess
from pathlib import Path
from subprocess import Popen

from pynicotine.pluginsystem import BasePlugin

VERBOSE = True


class Plugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = {
            "sox_path": None,
            "channels": "Left and right (default)",
            "width": 800,
            "height": 257,
            "title": "Hide title (default)",
            "comment": "Created by SoX",
            "start_position": 0,
            "duration": 0,
            "window_function": "Hann (default)",
            "monochrome": False,
            "raw": False,
            "high_color_mode": False,
            "light_mode": False,
            "brightness": 120,
            "contrast": 0,
            "number_of_colors": 249,
        }
        self.metasettings = {
            "sox_path": {
                "description": "Path to the SoX binary (leave empty to use the system PATH)",
                "type": "string",
            },
            "channels": {
                "description": "Audio channel to generate the spectrogram from",
                "type": "dropdown",
                "options": [
                    "Left and right (default)",
                    "Left",
                    "Right",
                ],
            },
            "width": {
                "description": "Width of a channel spectrogram (default 800px)",
                "type": "integer",
                "minimum": 100,
                "maximum": 200000,
                "stepsize": 20,
            },
            "height": {
                "description": "Height of a channel spectrogram (default 257px)",
                "type": "integer",
                "minimum": 64,
                "maximum": 513,
                "stepsize": 1,
            },
            "title": {
                "description": "Title to display at the top of the generated image",
                "type": "dropdown",
                "options": [
                    "Hide title (default)",
                    "Filename without extension",
                    "Filename with extension",
                    "Full path, filename and extension",
                ],
            },
            "comment": {
                "description": "Comment to display at the bottom left of the image",
                "type": "string",
            },
            "start_position": {
                "description": "Starting position in seconds",
                "type": "integer",
                "minimum": 0,
                "stepsize": 1,
            },
            "duration": {
                "description": "Duration in seconds",
                "type": "integer",
                "minimum": 0,
                "stepsize": 1,
            },
            "window_function": {
                "description": "Window function to use",
                "type": "dropdown",
                "options": [
                    "Hann (default)",
                    "Hamming",
                    "Bartlett",
                    "Rectangular",
                    "Kaiser",
                    "Dolph",
                ],
            },
            "monochrome": {
                "description": "Generate a monochromatic spectrogram",
                "type": "bool",
            },
            "raw": {
                "description": "Hide axes and labels",
                "type": "bool",
            },
            "high_color_mode": {
                "description": "Use the high-intensity color mode",
                "type": "bool",
            },
            "light_mode": {
                "description": "Use a white background",
                "type": "bool",
            },
            "brightness": {
                "description": "Brightness adjustment (20 to 180, default 120)",
                "type": "integer",
                "minimum": 20,
                "maximum": 180,
                "stepsize": 10,
            },
            "contrast": {
                "description": "Contrast adjustment (-100 to 100, default 0)",
                "type": "integer",
                "minimum": -100,
                "maximum": 100,
                "stepsize": 10,
            },
            "number_of_colors": {
                "description": "Number of colors (default 249)",
                "type": "integer",
                "minimum": 1,
                "maximum": 249,
                "stepsize": 2,
            },
        }

        if VERBOSE:
            self.log("Plugin initialized")

    def download_finished_notification(self, user: str, virtual_path: str, real_path: str):
        if VERBOSE:
            self.log(f"Finished downloading {virtual_path} from user {user}. Saved at {real_path}")

        extension = Path(real_path).suffix.lower()
        if extension.lower() in [".aiff", ".flac", ".mp3", ".ogg", ".wav"]:
            self.generate_spectrogram(real_path)

    def generate_spectrogram(self, audio_file_path: str):
        input_file_path = Path(audio_file_path)
        input_filename = input_file_path.stem
        input_directory = input_file_path.parent
        output_file_path = Path(input_directory, f"{input_filename}.png")
        sox_path = self.settings["sox_path"] or shutil.which("sox")

        if not input_file_path.exists():
            self.log(f"File not found: {input_file_path}")

        if not sox_path:
            self.log(
                "SoX binary not found."
                "Please set the correct SoX binary path in the plugin settings."
                "The path must contain the 'sox' executable."
            )
            return

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
        arguments = [
            # SoX executable binary file
            self.settings["sox_path"] or "sox",
        ]

        # Input file to be processed
        arguments.append(input_file_path.as_posix())

        # Null file handler flag
        arguments.append("-n")

        # Channel selection
        if self.settings["channels"] != "Left and right (default)":
            arguments.append("remix")
            arguments.append("1" if self.settings["channels"] == "Left" else "2")

        # Effect to be applied
        arguments.append("spectrogram")

        # Raw spectrogram flag
        if self.settings["raw"]:
            arguments.append("-r")

        # Width of an audio spectrogram channel
        if self.settings["width"]:
            width = max(min(self.settings["width"], 200000), 100)
            arguments.append("-x")
            arguments.append(str(width))

        # Height of an audio spectrogram channel
        if self.settings["height"]:
            height = self.settings["height"]
            # SoX requires a power of two + one for the height
            if height % 2 != 1:
                height = height + 1

            height = max(min(height, 513), 64)
            arguments.append("-y")
            arguments.append(str(height))

        # Image title
        if self.settings["title"]:
            arguments.append("-t")

            title = self.settings["title"]

            if title == "Filename without extension":
                arguments.append(input_file_path.stem)
            elif title == "Filename with extension":
                arguments.append(input_file_path.name)
            elif title == "Full path, filename and extension":
                arguments.append(input_file_path.as_posix())
            else:
                arguments.append(input_file_path.name)

        # Image comment
        if self.settings["comment"]:
            arguments.append("-c")
            arguments.append(self.settings["comment"])

        # Spectrogram starting position
        if self.settings["start_position"]:
            arguments.append("-S")
            arguments.append(str(self.settings["start_position"]))

        # Spectrogram duration
        if self.settings["duration"]:
            arguments.append("-d")
            arguments.append(str(self.settings["duration"]))

        # Window function
        arguments.append("-w")
        arguments.append(
            "Hann"
            if self.settings["window_function"] == "Hann (default)"
            else self.settings["window_function"]
        )

        # Monochrome spectrogram flag
        if self.settings["monochrome"]:
            arguments.append("-m")

        # Raw spectrogram flag
        if self.settings["raw"]:
            arguments.append("-r")

        # High color mode flag
        if self.settings["high_color_mode"]:
            arguments.append("-h")

        if self.settings["light_mode"]:
            arguments.append("-l")

        # Brightness and contrast adjustments
        if self.settings["brightness"]:
            brightness = max(min(self.settings["brightness"], 180), 20)
            arguments.append("-z")
            arguments.append(str(brightness))

        if self.settings["contrast"]:
            contrast = max(min(self.settings["contrast"], 100), -100)
            arguments.append("-Z")
            arguments.append(str(contrast))

        # Number of colors (quantization)
        if self.settings["number_of_colors"]:
            number_of_colors = max(min(self.settings["number_of_colors"], 1), 249)
            arguments.append("-q")
            arguments.append(str(number_of_colors))

        # Output file path
        arguments.append("-o")
        arguments.append(output_file_path.as_posix())

        if VERBOSE:
            self.log(f"Running command: {' '.join(arguments)}")

        return arguments
