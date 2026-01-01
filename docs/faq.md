# openHASP Designer - Frequently Asked Questions

## openHASP Integration Questions

### Q: What does `openhasp.load_pages` do?

**Answer:** It's a Home Assistant service that loads JSONL configuration onto openHASP devices.

**How it works:**
1. Reads `pages.jsonl` from HA config directory (e.g., `/config/openhasp/pages.jsonl`)
2. Parses each line as a JSON object (one object per line)
3. Sends objects to the openHASP device via MQTT
4. Device renders the UI based on the objects

**Example service call:**
```yaml
service: openhasp.load_pages
target:
  entity_id: openhasp.plate_livingroom
data:
  path: /config/openhasp/pages.jsonl
```

**What our backend does:**
```python
# After writing pages.jsonl, we call:
POST /api/services/openhasp/load_pages
{
  "entity_id": "openhasp.lanbon_l8_kitchen"
}
```

---

### Q: Does HA openHASP integration automatically push to devices?

**Answer:** **Yes, but only when triggered.**

**Automatic push happens when:**
- ✅ You call `openhasp.load_pages` service (what we do)
- ✅ HA restarts and reloads configurations
- ✅ Device reconnects to MQTT

**It does NOT automatically push when:**
- ❌ You just write a JSONL file (file sits there until service is called)
- ❌ You edit the file manually

**Our workflow:**
```
Designer → Backend writes JSONL → Backend calls load_pages → 
HA openHASP integration → MQTT → Lanbon L8
```

---

### Q: Where is the openHASP binding configuration stored?

**Answer:** In Home Assistant YAML configuration files.

**Storage locations:**
- **Manual config:** `/config/configuration.yaml` or `/config/packages/*.yaml`
- **UI config:** `/config/.storage/` (for integrations configured via UI)

**Our approach:**
We'll write to `/config/packages/openhasp_designer.yaml` so uninstalling the integration makes cleanup easy.

**Example configuration:**
```yaml
# /config/packages/openhasp_designer.yaml
openhasp:
  - plate: plate_livingroom
    objects:
      - obj: "p1b2"  # Page 1, Button 2
        properties:
          "text": "{{ states('light.living_room') }}"
          "val": "{{ 1 if is_state('light.living_room', 'on') else 0 }}"
        event:
          "down":
            - service: light.toggle
              target:
                entity_id: light.living_room
```

---

### Q: Are screen sizes learned upon discovery by openHASP custom integration?

**Answer:** **No, screen sizes are NOT automatically discovered.**

**Current state:**
- openHASP devices report their model (e.g., "Lanbon L8", "WT32-SC01")
- Screen resolution is NOT exposed as a HA attribute
- There's an open feature request to expose resolution/orientation

**Common resolutions:**
- Lanbon L8: **480x320 pixels** (landscape)
- WT32-SC01: **320x480 pixels** (portrait)
- ESP32-2432S028r: **240x320 pixels**
- 7-inch panels: Various resolutions

**Our implementation:**
We'll need to:
1. **Maintain a device model → resolution mapping**
   ```python
   DEVICE_RESOLUTIONS = {
       "Lanbon L8": {"width": 480, "height": 320},
       "WT32-SC01": {"width": 320, "height": 480},
       # etc.
   }
   ```

2. **Allow manual override** in designer settings
   ```javascript
   // Designer settings
   {
     device: "Lanbon L8 - Kitchen",
     resolution: {width: 480, height: 320},  // Auto-detected
     customResolution: null  // User can override
   }
   ```

3. **Validate coordinates** against selected device's screen size
   ```python
   def validate_object(obj, device_resolution):
       if obj.x + obj.width > device_resolution.width:
           raise ValidationError("Object extends beyond screen width")
   ```

---

## Development Environment Questions

### Q: Can Rancher Desktop be used instead of Docker Desktop?

**Answer:** **Yes! Rancher Desktop is fully compatible.**

**Requirements:**
- Configure Rancher Desktop to use `dockerd` (Moby) runtime
- This provides Docker CLI compatibility
- VS Code Remote - Containers extension works out of the box

**Setup:**
1. Install Rancher Desktop
2. Go to Preferences → Container Engine
3. Select **dockerd (moby)** instead of containerd
4. Restart Rancher Desktop
5. Verify: `docker --version` should work

**Why Rancher Desktop is great:**
- ✅ Free and open-source
- ✅ Lighter resource usage
- ✅ Built-in Kubernetes (k3s)
- ✅ Full Docker CLI compatibility (with dockerd)

---

### Q: Can Antigravity be used instead of VS Code?

**Answer:** **Yes! Antigravity is a VS Code fork and fully compatible.**

**What works:**
- ✅ All VS Code extensions (including Remote - Containers)
- ✅ Devcontainer configurations
- ✅ Same keyboard shortcuts and UI
- ✅ All development workflows

**Setup is identical:**
1. Install "Remote - Containers" extension in Antigravity
2. Open your repo folder
3. Command Palette → "Remote-Containers: Reopen in Container"
4. Everything works the same

**Advantages of using Antigravity:**
- ✅ You're already using it
- ✅ No need to switch IDEs
- ✅ Familiar environment
- ✅ AI assistance built-in

**Note:** Anywhere the documentation says "VS Code", you can substitute "Antigravity".

---

## Configuration Management Questions

### Q: Why use `/config/packages/` for YAML configuration?

**Answer:** **Easy cleanup and organization.**

**Benefits:**
1. **Isolated configuration** - All designer-generated config in one file
2. **Easy uninstall** - Just delete `openhasp_designer.yaml`
3. **Version control friendly** - Single file to track
4. **No pollution** - Doesn't clutter main `configuration.yaml`

**Setup:**
```yaml
# configuration.yaml
homeassistant:
  packages: !include_dir_named packages
```

Then our designer writes to:
```
/config/packages/openhasp_designer.yaml
```

**Alternative approach:**
If user doesn't have packages enabled, we can:
1. Detect if packages directory exists
2. Fall back to writing to `/config/openhasp_designer.yaml`
3. Provide instructions to include it in `configuration.yaml`

---

## Testing Questions

### Q: Do I need a separate test HA instance?

**Answer:** **No, use VS Code devcontainer instead.**

**Recommended approach:**
- **Development:** Run backend/frontend directly (no HA needed)
- **Integration testing:** VS Code devcontainer (local HA)
- **Final testing:** Your production HA instance

**Why devcontainer is better than separate HA:**
- ✅ Faster setup (no hardware/VM needed)
- ✅ Isolated environment
- ✅ Hot reload for development
- ✅ Access to full HA features
- ✅ No network configuration

**When you might want separate HA:**
- Testing with real openHASP hardware (Lanbon L8)
- Testing MQTT communication
- Long-term stability testing
- Multiple device testing

---

## Next Steps

For detailed development setup, see:
- [Development & Testing Guide](file:///Users/kevin/.gemini/antigravity/brain/32471498-e5bf-4770-8b09-33368b1b242a/development_testing_guide.md)
- [Product Requirements](file:///Users/kevin/.gemini/antigravity/brain/32471498-e5bf-4770-8b09-33368b1b242a/product_requirements.md)
