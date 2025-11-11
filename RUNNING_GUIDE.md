# AutoDoc - Complete Running Guide

This guide explains how to run all the implemented features, including the backend API, frontend Angular app, and testing.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup & Running](#backend-setup--running)
3. [Frontend Setup & Running](#frontend-setup--running)
4. [Testing Endpoints](#testing-endpoints)
5. [Using Angular Components](#using-angular-components)
6. [Testing with Mock Data](#testing-with-mock-data)
7. [Running Tests](#running-tests)

---

## Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed
- **Git** installed

---

## Backend Setup & Running

### 1. Install Python Dependencies

```bash
# Install backend dependencies
pip install -e ".[dev]"

# Or using the Makefile
make setup
```

### 2. Start the FastAPI Backend Server

```bash
# Option 1: Using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Python module
python -m uvicorn api.main:app --reload --port 8000

# Option 3: Check Makefile for dev command
make dev
```

The backend will be available at: **http://localhost:8000**

### 3. Verify Backend is Running

- **API Documentation (Swagger UI)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## Frontend Setup & Running

### 1. Install Node Dependencies

```bash
# Navigate to project root (if not already there)
cd /path/to/AutoDoc-1

# Install Angular dependencies
npm install
```

### 2. Start the Angular Development Server

```bash
# Start Angular dev server
npm start

# Or using Angular CLI directly
ng serve

# The server will start on http://localhost:4200
```

The frontend will be available at: **http://localhost:4200**

---

## Testing Endpoints

### 1. Diff Parser Endpoint

**Endpoint**: `POST /api/diff/parse`

**Test with curl**:
```bash
curl -X POST "http://localhost:8000/api/diff/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "old_file": "def old_func():\n    pass",
    "new_file": "def new_func():\n    return True"
  }'
```

**Test with Swagger UI**:
1. Go to http://localhost:8000/docs
2. Find `/api/diff/parse` endpoint
3. Click "Try it out"
4. Enter JSON body:
```json
{
  "old_file": "def old_func():\n    pass",
  "new_file": "def new_func():\n    return True"
}
```
5. Click "Execute"

**Expected Response**:
```json
{
  "added": ["def new_func():\n    return True"],
  "removed": ["def old_func():\n    pass"],
  "modified": []
}
```

### 2. Generate Change Report Endpoint

**Endpoint**: `POST /api/v1/runs/{run_id}/report`

**Prerequisites**: You need a Run in the database first.

**Step 1: Create a Run**:
```bash
curl -X POST "http://localhost:8000/api/v1/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "created"
  }'
```

**Step 2: Generate Report** (use the run_id from step 1):
```bash
curl -X POST "http://localhost:8000/api/v1/runs/1/report" \
  -H "Content-Type: application/json" \
  -d '{
    "diffs": {
      "test.py": {
        "added": ["line1"],
        "removed": ["old_line"],
        "modified": []
      }
    },
    "findings": {
      "test.py": [
        {
          "type": "added",
          "symbol": "new_func",
          "severity": "info",
          "message": "New function added"
        }
      ]
    }
  }'
```

**Expected Response**:
```json
{
  "report_path": "/absolute/path/to/artifacts/1/change_report.json"
}
```

### 3. Get Change Report Endpoint

**Endpoint**: `GET /api/v1/runs/{run_id}/report`

**Test**:
```bash
curl "http://localhost:8000/api/v1/runs/1/report"
```

**Expected Response**: The full change report JSON

---

## Using Angular Components

### 1. Access Run Details Component

**URL**: http://localhost:4200/runs/{runId}

**Example**:
- http://localhost:4200/runs/1
- http://localhost:4200/runs/123
- http://localhost:4200/runs/run_001

### 2. Features Available

- **Run ID and Timestamp Display**: Shows at the top of the page
- **File Diffs**: Collapsible cards showing added/removed/modified lines
  - Green background for added lines
  - Red background for removed lines
  - Yellow background for modified lines
- **Analyzer Findings**: Grouped by file with chips showing symbols and types
- **Search/Filter**: Search bar at the top to filter by filename, symbol, or content
- **Loading State**: Spinner while fetching data
- **Error Handling**: Error messages with snackbar notifications

### 3. Testing the Component

1. **With Backend Running**:
   - Navigate to http://localhost:4200/runs/1
   - Component will fetch data from backend
   - If run exists and has a report, it will display

2. **Without Backend (Mock Data)**:
   - Stop the backend server
   - Navigate to http://localhost:4200/runs/1
   - Component will detect network error
   - Automatically fallback to mock data
   - Shows "Mock Data (Offline Mode)" banner
   - Displays snackbar notification

---

## Testing with Mock Data

### 1. Mock Data Location

The mock data file is located at: `src/assets/mock-data/change_report.json`

### 2. Using Mock Data

**Automatic Fallback**:
- When backend is unavailable, the component automatically uses mock data
- No configuration needed

**Manual Testing**:
1. Stop the backend server
2. Navigate to any run ID: http://localhost:4200/runs/123
3. The component will automatically load mock data
4. You'll see the "Mock Data (Offline Mode)" banner

### 3. Customizing Mock Data

Edit `src/assets/mock-data/change_report.json` to customize:
- Add more file diffs
- Add more analyzer findings
- Modify existing data

The changes will be reflected immediately (no rebuild needed for assets).

---

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_change_report_generator.py -v

# Run with coverage
pytest --cov=services --cov=api tests/

# Run diff parser tests
pytest tests/test_diff_parser.py -v
```

### Frontend Tests

```bash
# Run Angular unit tests
npm test

# Or using Angular CLI
ng test

# Run specific test file
ng test --include='**/run-details.component.spec.ts'

# Run tests in watch mode
ng test --watch
```

### Test Coverage

**Backend**:
```bash
pytest --cov=services --cov=api --cov-report=html tests/
# Open htmlcov/index.html in browser
```

**Frontend**:
```bash
ng test --code-coverage
# Coverage report will be in coverage/ directory
```

---

## Complete Workflow Example

### Scenario: Test the Full Stack

1. **Start Backend**:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

2. **Start Frontend** (in a new terminal):
   ```bash
   npm start
   ```

3. **Create a Run** (using Swagger UI or curl):
   - Go to http://localhost:8000/docs
   - Use `POST /api/v1/runs` to create a run
   - Note the `id` from the response

4. **Generate a Report**:
   - Use `POST /api/v1/runs/{id}/report` with diffs and findings
   - This creates `artifacts/{id}/change_report.json`

5. **View in Frontend**:
   - Navigate to http://localhost:4200/runs/{id}
   - See the report displayed with all features

6. **Test Offline Mode**:
   - Stop the backend server
   - Refresh the page
   - See automatic fallback to mock data

---

## Troubleshooting

### Backend Issues

**Port Already in Use**:
```bash
# Find and kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill
```

**Database Issues**:
```bash
# The app uses SQLite by default
# Database file: autodoc.db (in project root)
# Delete it to reset: rm autodoc.db
```

### Frontend Issues

**Port Already in Use**:
```bash
# Angular will automatically try next port (4201, 4202, etc.)
# Or specify port:
ng serve --port 4201
```

**CORS Errors**:
- Make sure backend CORS is configured (already done in `api/main.py`)
- Check `core/config.py` for CORS_ORIGINS setting

**Module Not Found**:
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Mock Data Not Loading

- Check that `src/assets/mock-data/change_report.json` exists
- Verify the file is valid JSON
- Check browser console for errors
- Ensure Angular dev server is serving assets correctly

---

## Quick Reference

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/runs` | List runs |
| GET | `/api/v1/runs/{id}` | Get run details |
| POST | `/api/v1/runs` | Create run |
| GET | `/api/v1/runs/{id}/report` | Get change report |
| POST | `/api/v1/runs/{id}/report` | Generate change report |
| POST | `/api/diff/parse` | Parse file differences (if diff_parser router exists) |

### Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Main dashboard |
| `/runs/:runId` | RunDetailsComponent | View run details and change report |
| `/dashboard` | DashboardComponent | Dashboard page |
| `/rules` | RulesComponent | Rules management |
| `/templates` | TemplatesComponent | Templates management |

### Key Files

- **Backend API**: `api/main.py`
- **Diff Parser**: `api/routers/diff_parser.py` (if exists)
- **Change Report Generator**: `services/change_report_generator.py`
- **Runs Router**: `api/routers/runs.py`
- **Frontend Component**: `src/app/pages/run-details/run-details.component.ts`
- **Mock Service**: `src/app/services/mock-change-report.service.ts`
- **Mock Data**: `src/assets/mock-data/change_report.json`

---

## Next Steps

1. **Explore API Docs**: Visit http://localhost:8000/docs
2. **Test Endpoints**: Use Swagger UI to test all endpoints
3. **View Components**: Navigate through the Angular app
4. **Run Tests**: Ensure all tests pass
5. **Customize Mock Data**: Edit the mock JSON for your needs

Happy coding! 🚀

