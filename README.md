# Image Quality Filterer

## Overview

**Image Quality Filterer** is a Python script designed to organize and sort image files based on various criteria such as image shape (aspect ratio), resolution, and modification date. The script supports multi-threaded processing and is highly configurable, making it suitable for large-scale image sorting tasks.

## Features

- Sort images by shape (aspect ratio), resolution, and modification date
- Multi-threaded processing for improved performance
- Batch processing to manage system resources effectively
- Configurable through a `config.json` file
- Detailed logging with configurable log levels
- Handles interruptions gracefully for resource cleanup

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Logging](#logging)
- [Graceful Shutdown](#graceful-shutdown)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Dependencies

Install the required dependencies using pip:

```bash
pip install -r requirements.txt
```

### Configuration

The script is configured using a config.json file located in the config directory. Below is an example configuration file with comments explaining each parameter:

```json
{
 "_comments": {
  "input_directory": "The directory containing the images to be sorted.",
  "destination_directory": "The folder where sorted images will be copied. This can be customized.",
  "keep_directory_structure": "If true, organizes output into identical directory structure as input.",
  "sort_with_image_shape": "If true, images are also sorted by shape (e.g., 'landscape', 'portrait').",
  "min_modification_year": "Minimum year for categorizing images into the 'Best Quality' folder, if it also meets the DPI threshold.",
  "quality_dpi_threshold": "DPI threshold for high-quality images.",
  "xl_pixel_threshold": "Pixel threshold for categorizing images as extra-large.",
  "large_pixel_threshold": "Pixel threshold for categorizing images as large.",
  "folder_names": {
   "small": "Subfolder name for images smaller than the 'large_pixel_threshold' in both dimensions.",
   "standard": "Subfolder name for images larger than the 'large_pixel_threshold' in only one dimension.",
   "large": "Subfolder name for images larger than the 'large_pixel_threshold' but smaller than the 'xl_pixel_threshold'.",
   "xlarge": "Subfolder name for images larger than the 'xl_pixel_threshold'.",
   "best_quality": "Subfolder name for high-quality, XL images also meeting the DPI and year thresholds.",
   "errors": "Subfolder name for images that encountered errors during processing."
  },
  "max_workers": "The maximum number of workers to use for parallel processing.",
  "log_level": "The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
 },
 "input_directory": "data/Images",
 "destination_directory": "Sorted Images",
 "keep_directory_structure": false,
 "sort_with_image_shape": true,
 "min_modification_year": 2016,
 "quality_dpi_threshold": 300,
 "xl_pixel_threshold": 2000,
 "large_pixel_threshold": 1000,
 "folder_names": {
  "small": "Small",
  "standard": "Standard",
  "large": "Large",
  "xlarge": "XLarge",
  "best_quality": "Best Quality",
  "errors": "Errors"
 },
 "max_workers": 8,
 "log_level": "INFO"
}
```

### Usage

Run the script from the command line, specifying the base directory if different from configuration file:

```bash
python src/image_sorter.py /path/to/images
```

The script will read the configuration from config/config.json and begin processing the images.

### Logging

Logs are written to logs/photo_sorter.log with log rotation to prevent the log file from growing indefinitely. The log level can be configured in the config.json file.

### Graceful Shutdown

The script handles interruptions (e.g., Ctrl+C) gracefully, ensuring that resources are cleaned up properly.

### Future Improvements

While the current implementation is robust and feature-rich, there are several areas where further improvements could be made:

- **Enhanced Error Handling:** Implement more granular error handling to distinguish between transient and permanent errors. This could improve the retry logic and reduce unnecessary retries.
- **Scalability:** Explore distributed computing solutions to handle extremely large datasets across multiple machines. This would involve coordinating tasks and aggregating results from different nodes.
- **Graphical User Interface (GUI):** Develop a user-friendly GUI for less technical users. A GUI would make it easier to configure the script, monitor progress, and handle errors.
- **File Integrity Checks:** Implement file integrity checks using checksums to ensure that files are copied correctly. This would add a layer of validation to the file operations.
- **Unit Testing and Integration Testing:** Add comprehensive unit tests and integration tests to ensure the script functions correctly under various conditions. This would improve the reliability and maintainability of the code.
- **Advanced Configuration Management:** Consider using a more sophisticated configuration management system, such as YAML or TOML, for better readability and flexibility.
- **Performance Monitoring:** Integrate performance monitoring tools to track resource usage (CPU, memory) and identify potential bottlenecks. This would help in optimizing the performance further.

### Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss any changes or improvements.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
