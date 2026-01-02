# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2026-01-02)


### Features

* Add Release Please for automated versioning ([2d48250](https://github.com/ketronkowski/openhasp-designer-ha/commit/2d48250ce2b6a6ce377d0f38b406818db2cc24be))
* Complete device discovery and import from HA server ([1a9772c](https://github.com/ketronkowski/openhasp-designer-ha/commit/1a9772c5a20f42a18f3f640bbedcc5c357ae5c3f))
* Complete openHASP Designer - All 5 phases ([d01151d](https://github.com/ketronkowski/openhasp-designer-ha/commit/d01151da626f8b0b6c3db305b52f8a85d849d855))
* Extract device info from openhasp.{device_id} entity ([fe833d4](https://github.com/ketronkowski/openhasp-designer-ha/commit/fe833d4a059bba48a893faf560fedabca127dea2))
* Extract device name from common prefix of entity names ([e82ef4f](https://github.com/ketronkowski/openhasp-designer-ha/commit/e82ef4fef34bd5c2ed0545a8dd91d82ac1afa1ae))


### Bug Fixes

* Filter out non-openHASP devices from discovery ([b138039](https://github.com/ketronkowski/openhasp-designer-ha/commit/b138039ecc1aa25a09da8f7f7dac4ea2648f9814))
* Improve device discovery filtering and name extraction ([69890f7](https://github.com/ketronkowski/openhasp-designer-ha/commit/69890f75d884f9d569136cb302d8024c66023e31))
* Improve device discovery using entity-based approach ([6be6065](https://github.com/ketronkowski/openhasp-designer-ha/commit/6be6065286e76cf0a46cccb7a479e4f3f8ea5d4f))

## [Unreleased]

### Added
- Initial release of openHASP Designer
- Entity Browser Integration with search and filtering
- Multi-device deployment to Home Assistant
- Configuration import from Home Assistant (file and device-based)
- Enhanced features:
  - 15+ device model support
  - Overlap detection
  - YAML configuration generation
  - Entity state preview API
- Home Assistant add-on packaging
- Multi-stage Docker build (233MB optimized)
- GitHub Actions CI/CD with multi-arch support
- Devcontainer for local development
- Comprehensive test suite (74 tests)

### Features
- Visual drag-and-drop designer
- Real-time entity state display
- Comprehensive validation (entities, coordinates, overlaps)
- Merge/replace import modes
- YAML automation generation
- Multi-architecture Docker images (amd64, aarch64, armv7)

[Unreleased]: https://github.com/ketronkowski/openhasp-designer-ha/compare/v1.0.0...HEAD
