import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os
import shutil
import sys
import time
import signal
from PIL import Image, UnidentifiedImageError
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing


class ImageSorter:
    def __init__(self, config_path="config/config.json"):
        with open(config_path, "r") as config_file:
            config = json.load(config_file)

        # Ignore comments in the config
        config = {k: v for k, v in config.items() if not k.startswith("_")}

        # Load config values
        self.input_directory = os.path.abspath(
            config.get("input_directory", "data/Images")
        )
        self.destination_directory = os.path.abspath(
            config.get("destination_directory", "Sorted Images")
        )
        self.large_pixel_threshold = config.get("large_pixel_threshold", 1000)
        self.xl_pixel_threshold = config.get("xl_pixel_threshold", 2000)
        self.quality_dpi_threshold = config.get("quality_dpi_threshold", 300)
        self.min_modification_year = config.get("min_modification_year", 2016)
        self.keep_directory_structure = config.get("keep_directory_structure", False)
        self.sort_with_image_shape = config.get("sort_with_image_shape", True)

        self.folder_names = config.get("folder_names", {})
        self.folder_names.setdefault("small", "Small")
        self.folder_names.setdefault("large", "Large")
        self.folder_names.setdefault("xlarge", "XLarge")
        self.folder_names.setdefault("standard", "Standard")
        self.folder_names.setdefault("best_quality", "Best Quality")
        self.folder_names.setdefault("errors", "Errors")

        self.max_workers = config.get(
            "max_workers", multiprocessing.cpu_count()
        )  # Default to the number of CPUs if not specified
        self.batch_size = config.get("batch_size", 100)  # Default batch size

        log_level = config.get(
            "log_level", "INFO"
        ).upper()  # Default to INFO if not specified
        numeric_log_level = getattr(logging, log_level, logging.INFO)

        # Initialize other variables
        self.sort_queue = []
        self.error_count = 0
        self.processed_count = 0

        # Setup logging configuration with log rotation
        log_handler = RotatingFileHandler(
            "logs/photo_sorter.log", maxBytes=10**6, backupCount=5
        )
        logging.basicConfig(
            handlers=[log_handler],
            level=numeric_log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def graceful_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(
            f"Received shutdown signal ({signum}), shutting down gracefully..."
        )
        sys.exit(0)

    def process_directory(self, directory):
        """Process a given directory to enqueue supported images for sorting."""
        directory = os.path.abspath(directory)  # Ensure the directory is absolute
        if not self.is_within_input_directory(directory):
            self.logger.error(f"Attempted access to restricted directory: {directory}")
            return

        try:
            # Recursively process all subdirectories
            for dir_item in os.scandir(directory):
                item_path = os.path.abspath(dir_item.path)
                if not self.is_within_input_directory(item_path):
                    self.logger.error(
                        f"Attempted access to restricted directory: {item_path}"
                    )
                    continue

                if dir_item.is_dir():
                    self.process_directory(item_path)
                elif dir_item.is_file() and self.is_supported_image(dir_item.name):
                    # Process the image file
                    self.process_image_file(item_path)

        # Handle exceptions
        except (PermissionError, FileNotFoundError) as e:
            self.error_count += 1
            self.logger.error(f"Error accessing directory '{directory}': {e}")
        except Exception as e:
            self.error_count += 1
            self.logger.error(
                f"An unexpected error occurred while processing the directory '{directory}': {e}"
            )

    def process_image_file(self, initial_image_path):
        """Process an individual image file, determine its destination, and enqueue it."""
        if self.keep_directory_structure:
            # Determine the full destination path, keeping the initial directory structure intact
            new_folder_path = os.path.join(
                self.destination_directory,
                os.path.relpath(
                    os.path.dirname(initial_image_path), self.input_directory
                ),
            )
            new_folder_path = os.path.abspath(
                new_folder_path
            )  # Ensure the path is absolute
            # Determine the organization of the image and retrieve the full destination path
            full_destination_path = self.determine_destination_path(
                initial_image_path, baseDestinationFolder=new_folder_path
            )
        else:
            # Determine the full destination path, ignoring the initial directory structure
            full_destination_path = self.determine_destination_path(initial_image_path)

        # Enqueue the image for sorting
        self.enqueue_image_for_sorting(initial_image_path, full_destination_path)

    def is_within_input_directory(self, path):
        """Check if the given path is within the input directory."""
        return os.path.commonpath([self.input_directory, path]) == self.input_directory

    @staticmethod
    def is_supported_image(filename):
        """Check if the file has a supported image extension."""
        supported_extensions = (".jpg", ".jpeg", ".png", ".heic", ".webp")
        return filename.lower().endswith(supported_extensions)

    def determine_destination_path(self, image_path, baseDestinationFolder=None):
        """Calculate the shape of the image and return the corresponding folder."""
        baseDestinationFolder = (
            baseDestinationFolder
            if baseDestinationFolder
            else self.destination_directory
        )
        baseDestinationFolder = os.path.abspath(baseDestinationFolder)

        # Retrieve image information and determine the destination folder
        try:
            with Image.open(image_path) as im:
                dpi = im.info.get("dpi", (0, 0))[0]
                mod_time = os.path.getmtime(image_path)
                mod_year = datetime.fromtimestamp(mod_time).year

                width, height = im.size

                # Determine the image size
                folder = self.determine_size_folder(
                    baseDestinationFolder, width, height, dpi, mod_year
                )

                # Add the image shape to the folder name if the option is enabled
                if self.sort_with_image_shape:
                    folder += "/" + self.get_shape_label(width, height)

        # Handle exceptions
        except UnidentifiedImageError:
            self.error_count += 1
            self.logger.error(f"Unidentified image format for '{image_path}'.")
            return os.path.join(self.destination_directory, self.folder_names["errors"])
        except PermissionError:
            self.error_count += 1
            self.logger.error(f"Permission denied for accessing '{image_path}'.")
            return os.path.join(self.destination_directory, self.folder_names["errors"])
        except FileNotFoundError:
            self.error_count += 1
            self.logger.error(f"File not found: '{image_path}'.")
            return os.path.join(self.destination_directory, self.folder_names["errors"])
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"An unexpected error occurred for '{image_path}': {e}")
            return os.path.join(self.destination_directory, self.folder_names["errors"])

        return folder

    def determine_size_folder(self, base_folder, width, height, dpi, mod_year):
        """Determine the size-based subfolder based on image dimensions and DPI."""
        # Categorize the image based on its size
        if width < self.large_pixel_threshold and height < self.large_pixel_threshold:
            # Small image
            base_folder += f"/{self.folder_names['small']}"
        elif (
            width > self.xl_pixel_threshold
            and height > self.xl_pixel_threshold
            and (
                dpi
                and dpi >= self.quality_dpi_threshold
                and mod_year
                and mod_year >= self.min_modification_year
            )
        ):
            # Best quality image
            base_folder += f"/{self.folder_names['best_quality']}"
        elif width > self.xl_pixel_threshold and height > self.xl_pixel_threshold:
            # XL image
            base_folder += f"/{self.folder_names['xlarge']}"
        elif width > self.large_pixel_threshold and height > self.large_pixel_threshold:
            # Large image
            base_folder += f"/{self.folder_names['large']}"
        else:
            # Standard image
            base_folder += f"/{self.folder_names['standard']}"
        return base_folder

    @staticmethod
    def get_shape_label(width, height):
        """Get the shape matching the nearest common aspect ratio label for the given width and height."""
        # Predefined common aspect ratio decimal ranges with their shape labels
        aspect_ratio_ranges = {
            (0.9, 1.1): "square",
            (1.1, 2): "landscape",
            (0.5, 0.9): "portrait",
        }

        # Calculate the aspect ratio from the given width and height
        aspect_ratio = width / height

        # Iterate over predefined aspect ratios to find the closest one
        for (floor, ceiling), label in aspect_ratio_ranges.items():
            if floor <= aspect_ratio and aspect_ratio <= ceiling:
                return label

        # Otherwise, image must logically be 2:1 ratio or greater, a horizontal banner
        # (or 1:2 ratio or smaller in which case it's a vertical banner)
        return "Banner"

    def enqueue_image_for_sorting(self, image_path, destination_folder):
        """Add the image and destination folder to the sort queue."""
        self.sort_queue.append((image_path, destination_folder))

    @staticmethod
    def get_unique_filename(destination_folder, filename):
        """Generate a unique filename in the destination folder by appending a suffix."""
        base, extension = os.path.splitext(filename)
        unique_filename = filename
        counter = 1

        # Increase the counter until a unique filename is found, append count to end of filename
        while os.path.exists(os.path.join(destination_folder, unique_filename)):
            unique_filename = f"{base} ({counter}){extension}"
            counter += 1

        return unique_filename

    def copy_file(self, image_path, destination_folder):
        """Copy a single image file to its destination folder with retries and exponential backoff."""
        max_delay = 16  # Maximum delay of 16 seconds
        retries = 5
        filename = os.path.basename(image_path)

        if not os.path.isfile(image_path):
            self.logger.warning(f"The file '{image_path}' does not exist.")
            return False

        if not os.path.isdir(destination_folder):
            try:
                os.makedirs(destination_folder, exist_ok=True)
                self.logger.debug(f"Created the folder '{destination_folder}'.")
            except PermissionError as e:
                self.error_count += 1
                self.logger.error(f"Permission denied: {e}")
                return False
            except FileNotFoundError as e:
                self.error_count += 1
                self.logger.error(f"File not found: {e}")
                return False
            except Exception as e:
                self.error_count += 1
                self.logger.error(
                    f"An unexpected error occurred while creating the folder '{destination_folder}': {e}"
                )
                return False

        unique_filename = self.get_unique_filename(destination_folder, filename)
        destination_path = os.path.join(destination_folder, unique_filename)

        attempt = 0
        delay = 1
        while attempt < retries:
            try:
                shutil.copy2(image_path, destination_path)
                self.logger.debug(f"Copied '{image_path}' to '{destination_path}'.")
                self.processed_count += 1
                return True
            except PermissionError as e:
                self.error_count += 1
                self.logger.error(
                    f"Permission denied while copying '{image_path}': {e}"
                )
            except FileNotFoundError as e:
                self.error_count += 1
                self.logger.error(f"File not found while copying '{image_path}': {e}")
            except Exception as e:
                self.error_count += 1
                self.logger.error(
                    f"Attempt {attempt + 1}: An unexpected error occurred while copying the file '{image_path}': {e}"
                )
            attempt += 1
            time.sleep(delay)
            delay = min(max_delay, delay * 2)  # Exponential backoff

        self.logger.error(
            f"Failed to copy the file '{image_path}' after {retries} attempts."
        )
        return False

    def process_queue(self):
        """Copy images from the queue to their destination folders using multithreading."""
        while self.sort_queue:
            batch = self.sort_queue[: self.batch_size]
            self.sort_queue = self.sort_queue[self.batch_size :]

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.copy_file, image_path, destination_folder): (
                        image_path,
                        destination_folder,
                    )
                    for image_path, destination_folder in batch
                }
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Processing images",
                    unit="file",
                ):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"An error occurred during processing: {e}")

    def run(self):
        """Main function to set up the base folder and start processing."""
        start_time = time.time()
        print("Starting image sorting...")
        current_directory = os.getcwd()  # Get the current working directory
        base_folder_name = self.destination_directory
        base_folder_path = os.path.join(current_directory, base_folder_name)

        try:
            os.makedirs(base_folder_path, exist_ok=True)
            self.logger.info(f"Base folder '{base_folder_name}' created successfully.")
            print(f"Base folder '{base_folder_name}' created successfully.")
        except PermissionError as e:
            self.error_count += 1
            self.logger.error(
                f"Permission denied while creating the base folder '{base_folder_name}': {e}"
            )
            print(
                f"Error: Permission denied while creating the base folder '{base_folder_name}'."
            )
        except FileNotFoundError as e:
            self.error_count += 1
            self.logger.error(
                f"File not found while creating the base folder '{base_folder_name}': {e}"
            )
            print(
                f"Error: File not found while creating the base folder '{base_folder_name}'."
            )
        except Exception as e:
            self.error_count += 1
            self.logger.error(
                f"An unexpected error occurred while creating the base folder '{base_folder_name}': {e}"
            )
            print(
                f"Error: An unexpected error occurred while creating the base folder '{base_folder_name}'."
            )

        if self.keep_directory_structure:
            self.logger.info("Simple restructure mode enabled.")
            print("Simple restructure mode enabled.")

        print("Processing images...")
        self.process_directory(self.input_directory)
        self.process_queue()

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Final logging statement to indicate completion
        if self.error_count == 0:
            self.logger.info("Sorting completed successfully with no errors.")
            print("Sorting completed successfully with no errors.")
        else:
            self.logger.info(f"Sorting completed with {self.error_count} errors.")
            print(f"Sorting completed with {self.error_count} errors.")
        self.logger.info(
            f"Processed {self.processed_count} files in {elapsed_time:.2f} seconds."
        )
        print(f"Processed {self.processed_count} files in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    # Parse command line arguments
    args = sys.argv[1:]

    sorter = ImageSorter(config_path="config/config.json")
    # Override base_directory if the first command line argument is provided
    if len(args) > 0 and not args[0].startswith("-"):
        sorter.input_directory = os.path.abspath(args[0])

    sorter.run()
