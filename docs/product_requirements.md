# openHASP Designer - HA Integration Product Requirements

## Overview

This document defines the product requirements for tight Home Assistant integration with the openHASP Designer, based on user feedback and analysis of existing integrations.

---

## Requirement 1: Entity Browser with HA Entity Selection

### Current State
**HassPropertiesPanel.vue** currently has:
- ❌ Manual text input for `entity_id`
- ❌ Manual event selection dropdown
- ❌ Manual service name input

### Required State
✅ **Node-RED style entity browser** with:
- Searchable entity list from live HA instance
- Domain filtering (lights, switches, sensors, etc.)
- Entity preview with current state
- Friendly names and icons
- Auto-complete suggestions
- Recent/favorite entities

### User Story
> As a designer user, when I click on an openHASP object (button, slider, etc.), I want to see a panel that lets me **browse and select** HA entities visually, similar to Node-RED's entity selector, rather than typing entity IDs manually.

### Implementation Details

#### UI Components Needed

**EntityBrowser.vue** - Main entity selection component:
```
┌─────────────────────────────────────┐
│ Select Entity                    [×]│
├─────────────────────────────────────┤
│ 🔍 Search entities...               │
├─────────────────────────────────────┤
│ Filter: [All ▼] [Lights] [Switches]│
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ 💡 light.living_room            │ │
│ │    Living Room Light      [ON]  │ │
│ ├─────────────────────────────────┤ │
│ │ 💡 light.bedroom                │ │
│ │    Bedroom Light         [OFF]  │ │
│ ├─────────────────────────────────┤ │
│ │ 🔌 switch.coffee_maker          │ │
│ │    Coffee Maker          [ON]   │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Cancel]              [Select]      │
└─────────────────────────────────────┘
```

**Enhanced HassPropertiesPanel.vue:**
```vue
<template>
  <Accordion title="Home Assistant">
    <!-- Entity Selection -->
    <div class="entity-selector">
      <label>Entity</label>
      <div class="selected-entity" v-if="node.hass_entityid">
        <span class="entity-icon">{{ entityIcon }}</span>
        <span class="entity-name">{{ entityFriendlyName }}</span>
        <span class="entity-state">{{ entityState }}</span>
        <button @click="clearEntity">×</button>
      </div>
      <button @click="openEntityBrowser" v-else>
        + Select Entity
      </button>
    </div>
    
    <!-- Event/Action Configuration -->
    <div class="action-config" v-if="node.hass_entityid">
      <label>On Press</label>
      <select v-model="node.hass_event">
        <option value="toggle">Toggle</option>
        <option value="turn_on">Turn On</option>
        <option value="turn_off">Turn Off</option>
        <option value="custom">Custom Service...</option>
      </select>
      
      <!-- Custom service if selected -->
      <input v-if="node.hass_event === 'custom'" 
             v-model="node.hass_service"
             placeholder="e.g., light.turn_on" />
    </div>
  </Accordion>
  
  <!-- Entity Browser Modal -->
  <EntityBrowser 
    v-model:show="showBrowser"
    @select="onEntitySelected" />
</template>
```

#### Backend API Support

Already implemented in Python backend:
```python
GET /api/ha/entities?type=light&search=living
```

Returns:
```json
[
  {
    "entity_id": "light.living_room",
    "friendly_name": "Living Room Light",
    "state": "on",
    "icon": "mdi:lightbulb",
    "domain": "light",
    "attributes": {...}
  }
]
```

#### Node-RED Comparison

**Node-RED's entity selector features:**
- Live entity search with debouncing
- Domain icons (lightbulb for lights, plug for switches)
- Current state badges (ON/OFF, temperature values)
- Grouped by domain
- Recently used entities at top

**We should implement:**
- ✅ All of the above
- ✅ Plus: Entity state preview on canvas (show real values)
- ✅ Plus: Validation (warn if entity doesn't exist)

---

## Requirement 2: Export to Home Assistant (Not File Download)

### Current State
**Exporter.js** currently:
- ❌ Generates JSONL file
- ❌ Downloads to user's computer
- ❌ User must manually upload to HA

### Required State
✅ **Direct export to Home Assistant** with:
- One-click deployment
- Automatic JSONL generation
- Write to HA config directory
- Associate with specific openHASP device
- Trigger page reload automatically

### User Story
> As a designer user, when I finish my design, I want to click "Deploy to Device" and have it automatically pushed to my Lanbon L8 through Home Assistant, without downloading files or manual uploads.

### Implementation Details

#### UI Component

**DeployModal.vue:**
```
┌─────────────────────────────────────┐
│ Deploy to Home Assistant         [×]│
├─────────────────────────────────────┤
│ Select Device:                      │
│ ┌─────────────────────────────────┐ │
│ │ 📱 Lanbon L8 - Kitchen          │ │
│ │ 📱 Lanbon L8 - Living Room      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Configuration:                      │
│ ☑ Validate entities before deploy  │
│ ☑ Backup existing config           │
│ ☑ Reload pages after deploy        │
│                                     │
│ Preview:                            │
│ ┌─────────────────────────────────┐ │
│ │ Page 1: 5 objects               │ │
│ │ Page 2: 3 objects               │ │
│ │ Total: 8 objects                │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Cancel]              [Deploy]      │
└─────────────────────────────────────┘
```

#### Workflow

1. **User clicks "Deploy"**
2. **Designer validates:**
   - All entity IDs exist in HA
   - No overlapping objects
   - Valid coordinates
3. **Backend generates JSONL:**
   ```python
   POST /api/config/publish
   {
     "device_id": "lanbon_l8_kitchen",
     "objects": [...]
   }
   ```
4. **Backend writes to HA:**
   - Writes to `/config/openhasp/lanbon_l8_kitchen/pages.jsonl`
   - Calls `openhasp.load_pages` service with device selector
5. **Device updates:**
   - HA openHASP integration pushes to device
   - Device reloads pages
6. **Designer shows confirmation:**
   - "✅ Deployed to Lanbon L8 - Kitchen"

#### Device Association

**How to get openHASP devices from HA:**

```python
# New backend endpoint
GET /api/ha/devices?integration=openhasp

# Returns:
[
  {
    "device_id": "abc123",
    "name": "Lanbon L8 - Kitchen",
    "model": "Lanbon L8",
    "node_name": "plate01",
    "online": true
  }
]
```

**HA API call:**
```python
async def get_openhasp_devices(self):
    """Get all openHASP devices from HA."""
    # Query HA device registry
    response = await client.get(
        f"{self.base_url}/api/config/device_registry/list",
        headers=self.headers
    )
    devices = response.json()
    
    # Filter for openHASP devices
    return [
        d for d in devices 
        if any("openhasp" in i.lower() for i in d.get("identifiers", []))
    ]
```

---

## Requirement 3: Import from Home Assistant (Not File Upload)

### Current State
**Importer.js** currently:
- ❌ Imports from local JSONL file
- ❌ User must download from HA first

### Required State
✅ **Direct import from Home Assistant** with:
- List available configs from HA
- Select device to import from
- Preview before importing
- Merge or replace options

### User Story
> As a designer user, I want to import my existing openHASP configuration from Home Assistant to edit it, without downloading and uploading files manually.

### Implementation Details

#### UI Component

**ImportWizard.vue:**
```
┌─────────────────────────────────────┐
│ Import from Home Assistant       [×]│
├─────────────────────────────────────┤
│ Step 1: Select Device               │
│ ┌─────────────────────────────────┐ │
│ │ ○ Lanbon L8 - Kitchen           │ │
│ │ ● Lanbon L8 - Living Room       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Step 2: Preview Configuration       │
│ ┌─────────────────────────────────┐ │
│ │ Found: pages.jsonl              │ │
│ │ - Page 1: 5 objects             │ │
│ │ - Page 2: 3 objects             │ │
│ │                                 │ │
│ │ Entities used:                  │ │
│ │ ✓ light.living_room (exists)    │ │
│ │ ✗ light.old_lamp (missing!)     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Import mode:                        │
│ ○ Replace current design            │
│ ● Merge with current design         │
│                                     │
│ [Cancel]              [Import]      │
└─────────────────────────────────────┘
```

#### Backend Implementation

Already implemented in Python backend:
```python
GET /api/config/import/available
# Returns: ["plate01_pages.jsonl", "plate02_pages.jsonl"]

GET /api/config/import?filename=plate01_pages.jsonl
# Returns: Layout object with pages and objects
```

**Enhancement needed:**
```python
# New endpoint - import by device
GET /api/config/import/device/{device_id}

# Automatically finds the right JSONL file for that device
```

---

## Requirement 4: Entity ID Storage Explained

### What "Entity ID Storage" Means

#### Current Implementation

In the OpenHaspDesigner codebase, each `HaspObject` (button, slider, etc.) has a property:

```javascript
// In HaspObject.js
class HaspObject extends Group {
  hass_entityid = undefined;  // ← This stores the HA entity ID
  
  constructor(config) {
    // ...
    if (config.entity_id !== undefined) {
      this.hass_entityid = config.entity_id;
    }
  }
}
```

#### What This Enables

**1. Design-Time Storage:**
When you assign an entity to an object in the designer:
```javascript
button.hass_entityid = "light.living_room"
```

This is stored in the designer's internal state, so when you save/load the design, the entity association is preserved.

**2. Export to JSONL:**
When exporting, this becomes:
```json
{
  "page": 1,
  "id": 2,
  "obj": "btn",
  "x": 10,
  "y": 20,
  "w": 100,
  "h": 50,
  "text": "Living Room",
  "entity": "light.living_room"  // ← Exported as "entity"
}
```

**3. Runtime in HA:**
The openHASP custom component reads this and creates the binding:
```yaml
# Generated in HA configuration
openhasp:
  - plate: plate_livingroom
    objects:
      - obj: "p1b2"  # Page 1, Button 2
        properties:
          "val": "{{ 1 if is_state('light.living_room', 'on') else 0 }}"
        event:
          "down":
            - service: light.toggle
              target:
                entity_id: light.living_room
```

#### Why This Matters

**Without entity storage:**
- Designer is just a visual layout tool
- No connection to HA functionality
- User must manually configure everything in YAML

**With entity storage:**
- Designer knows which HA entity controls each object
- Can generate complete HA configuration automatically
- Can validate entities exist
- Can show live preview with real states

#### Enhanced Entity Storage (What We're Building)

**Current:** `hass_entityid` is just a string  
**Enhanced:** Rich entity object with metadata

```javascript
// Enhanced storage
button.hass_entity = {
  entity_id: "light.living_room",
  friendly_name: "Living Room Light",
  domain: "light",
  icon: "mdi:lightbulb",
  current_state: "on",
  actions: {
    on_press: "toggle",
    on_long_press: "turn_off"
  }
}
```

**Benefits:**
- Show friendly name in designer (not just `light.living_room`)
- Display current state on canvas ("ON" badge)
- Validate entity still exists
- Auto-suggest appropriate actions for entity type
- Generate smarter HA automations

---

## Implementation Priority

### Phase 1: Entity Browser (Highest Priority)
**Why:** Most impactful UX improvement, enables all other features

**Tasks:**
1. Create `EntityBrowser.vue` component
2. Integrate with backend `/api/ha/entities` endpoint
3. Replace text input in `HassPropertiesPanel.vue`
4. Add entity state display on canvas

**Estimated effort:** 8-12 hours

---

### Phase 2: Deploy to HA (High Priority)
**Why:** Core integration feature, eliminates manual file handling

**Tasks:**
1. Create `DeployModal.vue` component
2. Add device discovery endpoint
3. Implement validation before deploy
4. Add progress/status feedback

**Estimated effort:** 6-8 hours

---

### Phase 3: Import from HA (Medium Priority)
**Why:** Enables editing existing configs, but less critical than deploy

**Tasks:**
1. Create `ImportWizard.vue` component
2. Add device-based import endpoint
3. Implement entity validation on import
4. Add merge/replace logic

**Estimated effort:** 6-8 hours

---

### Phase 4: Enhanced Entity Storage (Medium Priority)
**Why:** Improves UX but not blocking

**Tasks:**
1. Extend `HaspObject` to store rich entity data
2. Add entity state preview on canvas
3. Implement entity validation warnings
4. Add auto-save of entity metadata

**Estimated effort:** 4-6 hours

---

## Technical Architecture

### Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                     Designer Frontend                     │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ EntityBrowser  │  │ Canvas       │  │ DeployModal  │ │
│  │ - Search       │  │ - Objects    │  │ - Validate   │ │
│  │ - Filter       │  │ - Preview    │  │ - Deploy     │ │
│  └────────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└───────────┼──────────────────┼──────────────────┼─────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────┐
│                   Python/FastAPI Backend                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ /api/ha/entities        - Entity browser            │ │
│  │ /api/ha/devices         - Device discovery          │ │
│  │ /api/config/publish     - Deploy to HA              │ │
│  │ /api/config/import      - Import from HA            │ │
│  └──────────────────────┬──────────────────────────────┘ │
└─────────────────────────┼────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   Home Assistant                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ REST API            - Entity states, services       │ │
│  │ Device Registry     - openHASP devices              │ │
│  │ Config Directory    - /config/openhasp/*.jsonl      │ │
│  │ openHASP Integration - Page loading, MQTT           │ │
│  └──────────────────────┬──────────────────────────────┘ │
└─────────────────────────┼────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   Lanbon L8 Device                        │
│  - Receives JSONL via MQTT                                │
│  - Renders UI                                             │
│  - Sends events back to HA                                │
└──────────────────────────────────────────────────────────┘
```

---

## Summary

These requirements transform the designer from a **layout tool** into a **complete HA integration platform**:

1. ✅ **Entity Browser** - Node-RED style entity selection
2. ✅ **Deploy to HA** - One-click deployment to devices
3. ✅ **Import from HA** - Edit existing configurations
4. ✅ **Rich Entity Storage** - Metadata, validation, preview

**Next step:** Implement Phase 1 (Entity Browser) as it enables all other features.
