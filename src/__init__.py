import concurrent.futures
import shutil
import subprocess
import sys
from pathlib import Path

from pynicotine.events import events
from pynicotine.pluginsystem import BasePlugin

VERBOSE = False
MAX_WORKERS = 1


class Plugin(BasePlugin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.settings = {
            "sox_path": None,
            "channels": "Left and right (default)",
            "width": 800,
            "height": 257,
            "title": "No title (default)",
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
                    "No title (default)",
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

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)

        if VERBOSE:
            self.log("Plugin initialized")

    def disable(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def download_finished_notification(self, user: str, virtual_path: str, real_path: str) -> None:
        if VERBOSE:
            self.log(f"Finished downloading {virtual_path} from user {user}. Saved at {real_path}")

        extension = Path(real_path).suffix.lower()
        if extension in (".aiff", ".flac", ".mp3", ".ogg", ".wav"):
            self.executor.submit(self.generate_spectrogram, real_path)

    def _log_main(self, message: str) -> None:
        """Dispatch self.log to the main thread.

        self.log() ends up emitting the 'log-message' event which is consumed
        by the GTK log view. Emitting it directly from a worker thread is not
        safe and can cause UI freezes or crashes.
        """
        events.invoke_main_thread(self.log, message)

    def generate_spectrogram(self, audio_file_path: str) -> None:
        input_file_path = Path(audio_file_path)
        input_filename = input_file_path.stem
        input_directory = input_file_path.parent
        output_file_path = Path(input_directory, f"{input_filename}.png")
        sox_path = self.settings["sox_path"] or shutil.which("sox")

        if not input_file_path.exists():
            self._log_main(f"File not found: {input_file_path}")
            return

        if not sox_path:
            self._log_main(
                "SoX binary not found. "
                "Please set the correct SoX binary path in the plugin settings. "
                "The path must contain the 'sox' executable."
            )
            return

        if VERBOSE:
            self._log_main(f"Generating spectrogram for '{input_filename}'...")

        arguments = self.build_arguments(sox_path, input_file_path, output_file_path)

        # Hide the transient console window SoX would otherwise pop up on Windows.
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        try:
            process = subprocess.Popen(
                arguments,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
            )
            try:
                _, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                self._log_main(f"SoX timed out after 120s for {input_file_path.name}, killed.")
                return

            if process.returncode == 0:
                self._log_main(f"Spectrogram saved at {output_file_path}")
            else:
                self._log_main(f"An error occurred: {stderr.decode(errors='replace').strip()}")

        except Exception as error:
            self._log_main(f"An error occurred: {error}")

    def build_arguments(self, sox_path: str, input_file_path: Path, output_file_path: Path) -> list:
        arguments = [
            sox_path,
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
            # SoX requires the height to be a power of two plus one.
            # Snap the user value to the nearest valid choice.
            valid_heights = (65, 129, 257, 513)
            height = min(valid_heights, key=lambda v: abs(v - self.settings["height"]))
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
            number_of_colors = max(min(self.settings["number_of_colors"], 249), 1)
            arguments.append("-q")
            arguments.append(str(number_of_colors))

        # Output file path
        arguments.append("-o")
        arguments.append(output_file_path.as_posix())

        if VERBOSE:
            self._log_main(f"Running command: {' '.join(arguments)}")

        return arguments
