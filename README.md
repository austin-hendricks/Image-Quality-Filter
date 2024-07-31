# Image Sorter

## Overview

**Image Sorter** is a Python script designed to organize and sort image files based on various criteria such as aspect ratio, resolution, and modification date. The script supports multi-threaded processing and is highly configurable, making it suitable for large-scale image sorting tasks.

## Features

- Sort images by aspect ratio, resolution, and modification date
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
  "base_directory": "The directory containing the images to be sorted.",
  "destination_directory": "The base directory where sorted images will be stored.",
  "large_pixel_threshold": "Pixel threshold for categorizing images as large.",
  "xl_pixel_threshold": "Pixel threshold for categorizing images as extra-large.",
  "dpi_threshold": "DPI threshold for high-quality images.",
  "min_year": "Minimum year for categorizing images into the 'Best Quality' folder.",
  "simple_restructure_mode": "Boolean flag to enable simple restructure mode.",
  "sort_with_image_shape": "Boolean flag to enable sorting by image shape.",
  "dpi_date_sort_mode": "Boolean flag to enable sorting with additional criteria based on DPI and modification date.",
  "folder_names": {
   "small": "Subfolder name for small images.",
   "large": "Subfolder name for large images.",
   "xlarge": "Subfolder name for extra-large images.",
   "standard": "Subfolder name for standard images.",
   "best_quality": "Subfolder name for best quality images.",
   "errors": "Subfolder name for images that encountered errors during processing."
  },
  "max_workers": "The number of worker threads for processing images concurrently.",
  "batch_size": "The number of images to process in each batch.",
  "log_level": "The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
 },
 "base_directory": "Images",
 "destination_directory": "Sorted Images",
 "large_pixel_threshold": 1000,
 "xl_pixel_threshold": 2000,
 "dpi_threshold": 300,
 "min_year": 2016,
 "simple_restructure_mode": false,
 "sort_with_image_shape": true,
 "dpi_date_sort_mode": false,
 "folder_names": {
  "small": "Small",
  "large": "Large",
  "xlarge": "XLarge",
  "standard": "Standard",
  "best_quality": "Best Quality",
  "errors": "Errors"
 },
 "max_workers": 8,
 "batch_size": 100,
 "log_level": "INFO"
}
```

### Usage

Run the script from the command line, specifying the base directory if different from the default:

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

This project is licensed under the MIT License. See the LICENSE file for details.
