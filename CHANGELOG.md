# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2025-08-19

### Fixed
- Updated GitHub Actions workflow to use `actions/upload-artifact@v4` and `actions/download-artifact@v4` to resolve CI/CD pipeline failures
- Fixed deprecated action versions that were causing automatic build failures

### Changed
- Enhanced `validate_country_code()` function to accept both 2-letter ISO country codes and empty strings
- Improved validation flexibility for country code parameters

## [1.0.2] - 2025-08-18

### Fixed
- Resolved issues with zone opening functionality
- Fixed zone management and configuration problems

### Added
- Created comprehensive test units for improved code reliability
- Added unit tests for core SDK functionality

## [1.0.1] - 2025-08-11

### Changed
- Replaced `browser_zone` parameter with `serp_zone` parameter in `bdclient` constructor
- `serp_zone` can now be configured directly from the client instead of only via environment variable
- Updated documentation and tests to reflect the parameter change

### Removed  
- `browser_zone` parameter from `bdclient` constructor (was unused in the codebase)

## [1.0.0] - 2024-08-10

### Added
- Initial release of Bright Data Python SDK
- Web scraping functionality using Bright Data Web Unlocker API
- Search engine results using Bright Data SERP API
- Support for multiple search engines (Google, Bing, Yandex)
- Parallel processing for multiple URLs and queries
- Comprehensive error handling with retry logic
- Input validation for URLs, zones, and parameters
- Automatic zone creation and management
- Multiple output formats (JSON, raw HTML, markdown)
- Content download functionality
- Zone management utilities
- Comprehensive logging system
- Built-in connection pooling
- Environment variable configuration support

### Features
- `bdclient` main client class
- `scrape()` method for web scraping
- `search()` method for SERP API
- `download_content()` for saving results
- `list_zones()` for zone management
- Automatic retry with exponential backoff
- Structured logging support
- Configuration via environment variables or direct parameters

### Dependencies
- `requests>=2.25.0`
- `python-dotenv>=0.19.0`

### Python Support
- Python 3.7+
- Cross-platform compatibility (Windows, macOS, Linux)