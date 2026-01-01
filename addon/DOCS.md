# openHASP Designer Add-on

Visual designer for openHASP with Home Assistant integration.

![openHASP Designer](https://raw.githubusercontent.com/ketronkowski/openhasp-designer-ha/main/images/screenshot.png)

## About

openHASP Designer is a visual design tool that makes it easy to create beautiful user interfaces for your openHASP devices. Design your layouts visually, connect them to your Home Assistant entities, and deploy directly to your devices.

## Features

- **Visual Designer**: Drag-and-drop interface builder
- **Entity Browser**: Browse and search all your Home Assistant entities
- **Live Preview**: See your design with real entity states
- **Multi-Device**: Deploy to multiple openHASP devices
- **Import/Export**: Import existing configurations or export your designs
- **YAML Generation**: Generate Home Assistant automation YAML
- **Validation**: Automatic validation of entities, coordinates, and overlaps

## Installation

1. Add this repository to your Home Assistant add-on store:
   ```
   https://github.com/ketronkowski/openhasp-designer-ha
   ```

2. Install the "openHASP Designer" add-on

3. Configure the add-on (see Configuration section)

4. Start the add-on

5. Access via the "openHASP Designer" panel in your Home Assistant sidebar

## Configuration

### Option: `ha_url`

The URL to your Home Assistant instance. 

**Default**: `http://supervisor/core` (uses Supervisor API)

**Note**: In most cases, you don't need to change this.

### Option: `ha_token`

Long-lived access token for Home Assistant API.

**Default**: Empty (uses Supervisor token automatically)

**Note**: Only needed if you want to use a specific token instead of the automatic Supervisor token.

To generate a long-lived access token:
1. Go to your Home Assistant profile
2. Scroll down to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Copy the token and paste it here

## Usage

### Getting Started

1. Open the add-on Web UI from the Home Assistant sidebar
2. You'll see the visual designer canvas

### Designing Your Interface

1. **Add Objects**: Click the toolbar buttons to add labels, buttons, switches, etc.
2. **Position Objects**: Drag objects to position them on the canvas
3. **Resize Objects**: Drag the corners to resize
4. **Configure Properties**: Click an object to edit its properties in the right panel

### Connecting Entities

1. Click an object to select it
2. In the properties panel, click "Select Entity"
3. Search for your Home Assistant entity
4. The object will now be linked to that entity

### Deploying to Devices

1. Click the "Deploy" button in the toolbar
2. Select your target openHASP device
3. Choose validation options
4. Click "Deploy"
5. Your design will be sent to the device

### Importing Existing Configurations

1. Click the "Import" button
2. Upload a JSONL file or select a device
3. Preview the configuration
4. Choose merge or replace mode
5. Click "Import"

## Support

For issues, feature requests, or questions:

- **GitHub Issues**: https://github.com/ketronkowski/openhasp-designer-ha/issues
- **Discussions**: https://github.com/ketronkowski/openhasp-designer-ha/discussions
- **Documentation**: https://github.com/ketronkowski/openhasp-designer-ha/wiki

## Changelog

### Version 1.0.0

- Initial release
- Visual designer with drag-and-drop
- Entity browser integration
- Multi-device deployment
- Configuration import/export
- YAML generation
- Comprehensive validation
- Support for 15+ device models

## Credits

Based on the original [OpenHaspDesigner](https://github.com/Nerdiyde/OpenHaspDesigner) by Nerdiyde.

Enhanced with Home Assistant integration and modern web technologies.

## License

Apache 2.0 License - See LICENSE file for details
