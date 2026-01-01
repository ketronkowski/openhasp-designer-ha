# Testing Setup & Strategy Guide

## Overview

This guide covers the complete testing setup for the openHASP Designer project, including backend (Python), frontend (Vue 3), and E2E testing.

---

## Backend Testing (Python/FastAPI)

### Framework: pytest + pytest-asyncio

**Install dependencies:**
```bash
cd backend-python
pip install -r requirements-test.txt
```

**Configuration:** `pytest.ini` (already created)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = --verbose --cov=app --cov-report=term-missing
```

**Directory structure:**
```
backend-python/
├── tests/
│   ├── conftest.py           # Fixtures
│   ├── test_services.py      # Service tests
│   ├── test_models.py        # Model validation tests
│   └── test_api.py           # API endpoint tests
```

**Example test:** `tests/conftest.py`
```python
import pytest
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Test client for API testing."""
    return TestClient(app)

@pytest.fixture
def mock_ha_entities():
    """Mock Home Assistant entities."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"}
        }
    ]
```

**Run tests:**
```bash
# All tests with coverage
pytest

# Specific test file
pytest tests/test_services.py

# Watch mode
pytest-watch
```

---

## Frontend Testing (Vue 3)

### Framework: Vitest + Vue Test Utils

**Install dependencies:**
```bash
cd frontend
npm install -D vitest @vue/test-utils @vitest/ui jsdom
```

**Configuration:** `vitest.config.js`
```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['node_modules/', 'tests/']
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

**Directory structure:**
```
frontend/
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   └── api.spec.js
│   │   └── utils/
│   │       └── validation.spec.js
│   └── components/
│       ├── EntityBrowser.spec.js
│       ├── DeployModal.spec.js
│       └── HassPropertiesPanel.spec.js
```

**Example component test:** `tests/components/EntityBrowser.spec.js`
```javascript
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import EntityBrowser from '@/components/EntityBrowser.vue'

describe('EntityBrowser', () => {
  const mockEntities = [
    { entity_id: 'light.living_room', friendly_name: 'Living Room', domain: 'light' },
    { entity_id: 'switch.kitchen', friendly_name: 'Kitchen', domain: 'switch' }
  ]

  it('renders entity list', () => {
    const wrapper = mount(EntityBrowser, {
      props: { entities: mockEntities }
    })
    
    expect(wrapper.findAll('.entity-item')).toHaveLength(2)
  })

  it('filters entities by search query', async () => {
    const wrapper = mount(EntityBrowser, {
      props: { entities: mockEntities }
    })
    
    const searchInput = wrapper.find('input[type="search"]')
    await searchInput.setValue('living')
    
    expect(wrapper.findAll('.entity-item')).toHaveLength(1)
    expect(wrapper.text()).toContain('Living Room')
  })

  it('filters entities by domain', async () => {
    const wrapper = mount(EntityBrowser, {
      props: { entities: mockEntities }
    })
    
    await wrapper.find('button[data-domain="light"]').trigger('click')
    
    expect(wrapper.findAll('.entity-item')).toHaveLength(1)
    expect(wrapper.text()).toContain('Living Room')
  })

  it('emits select event when entity clicked', async () => {
    const wrapper = mount(EntityBrowser, {
      props: { entities: mockEntities }
    })
    
    await wrapper.find('.entity-item:first-child').trigger('click')
    
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0][0]).toEqual(mockEntities[0])
  })
})
```

**Run tests:**
```bash
# All tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# UI mode (interactive)
npm run test:ui
```

**Add to `package.json`:**
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest run --coverage"
  }
}
```

---

## E2E Testing (Playwright)

### Framework: Playwright

**Install:**
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

**Configuration:** `playwright.config.js`
```javascript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    // Optionally test on other browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] }
    // }
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI
  }
})
```

**Directory structure:**
```
frontend/
├── tests/
│   └── e2e/
│       ├── entity-browser.spec.js
│       ├── deploy-workflow.spec.js
│       └── import-workflow.spec.js
```

**Example E2E test:** `tests/e2e/entity-browser.spec.js`
```javascript
import { test, expect } from '@playwright/test'

test.describe('Entity Browser Workflow', () => {
  test('select entity from browser', async ({ page }) => {
    // Navigate to designer
    await page.goto('/')
    
    // Click on a button object
    await page.click('.hasp-button')
    
    // Properties panel should open
    await expect(page.locator('.properties-panel')).toBeVisible()
    
    // Click "Select Entity" button
    await page.click('button:has-text("Select Entity")')
    
    // Entity browser modal should open
    await expect(page.locator('.entity-browser')).toBeVisible()
    
    // Search for entity
    await page.fill('input[placeholder*="Search"]', 'light.living')
    
    // Wait for search results
    await page.waitForSelector('.entity-item')
    
    // Verify entity appears
    await expect(page.locator('.entity-item')).toContainText('Living Room')
    
    // Click entity to select
    await page.click('.entity-item:first-child')
    
    // Modal should close
    await expect(page.locator('.entity-browser')).not.toBeVisible()
    
    // Selected entity should display in properties panel
    await expect(page.locator('.selected-entity')).toContainText('Living Room')
  })

  test('filter entities by domain', async ({ page }) => {
    await page.goto('/')
    await page.click('.hasp-button')
    await page.click('button:has-text("Select Entity")')
    
    // Click "Lights" filter
    await page.click('button[data-domain="light"]')
    
    // Verify only lights are shown
    const entities = await page.locator('.entity-item').all()
    for (const entity of entities) {
      await expect(entity).toContainText('light.')
    }
  })
})
```

**Run E2E tests:**
```bash
# All E2E tests
npx playwright test

# Specific test
npx playwright test entity-browser

# Debug mode
npx playwright test --debug

# UI mode (interactive)
npx playwright test --ui

# Generate report
npx playwright show-report
```

---

## CI/CD Integration

### GitHub Actions Workflow

**Create:** `.github/workflows/test.yml`
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          cd backend-python
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: |
          cd backend-python
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend-python/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['18']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run unit tests
        run: |
          cd frontend
          npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps
      
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Demo Recording with Antigravity

### Use Case: Visual Documentation

While **not for automated testing**, Antigravity's browser automation is perfect for:
- Creating demo videos
- Recording user workflows
- Visual documentation
- Bug reproduction

**Example usage:**
```markdown
Create a demo recording showing:
1. Opening the designer
2. Selecting an entity from the browser
3. Deploying to Home Assistant
4. Showing the result on the device
```

Then use Antigravity's `browser_subagent` tool to record the workflow.

---

## Testing Strategy Summary

```
┌─────────────────────────────────────────────────────────┐
│ Testing Pyramid                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  E2E (Playwright)                    [~10 tests]        │
│  ├─ Critical user flows                                 │
│  ├─ Entity browser → Deploy → Verify                    │
│  └─ Import → Edit → Deploy                              │
│                                                         │
│  Component (Vitest)                  [~50 tests]        │
│  ├─ EntityBrowser                                       │
│  ├─ DeployModal                                         │
│  ├─ ImportWizard                                        │
│  └─ HassPropertiesPanel                                 │
│                                                         │
│  Unit (pytest/Vitest)                [~100 tests]       │
│  ├─ Backend services                                    │
│  ├─ Validation logic                                    │
│  ├─ JSONL generation                                    │
│  └─ Utility functions                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Coverage targets:**
- Backend: >80%
- Frontend: >70%
- E2E: Critical paths only

---

## Quick Reference

**Backend:**
```bash
cd backend-python
pytest                    # Run all tests
pytest -v                 # Verbose
pytest --cov              # With coverage
pytest -k test_name       # Specific test
```

**Frontend Unit:**
```bash
cd frontend
npm run test              # Run once
npm run test:watch        # Watch mode
npm run test:ui           # Interactive UI
npm run test:coverage     # Coverage report
```

**Frontend E2E:**
```bash
cd frontend
npx playwright test       # Run all
npx playwright test --ui  # Interactive
npx playwright test --debug  # Debug mode
```

**All tests:**
```bash
# From project root
npm run test:all          # Run backend + frontend + E2E
```
