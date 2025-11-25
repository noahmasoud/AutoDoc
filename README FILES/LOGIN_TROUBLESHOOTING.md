# Login Troubleshooting Guide

## Quick Diagnostic Steps

### 1. Check Backend is Running
Open browser and visit:
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

If these don't work, the backend is NOT running.

### 2. Check Browser Console (F12)
Look for errors when clicking "Sign In":
- CORS errors
- Connection refused
- 404 Not Found
- 500 Internal Server Error

### 3. Check Network Tab (F12 → Network)
When clicking "Sign In":
- Look for a POST request to `http://localhost:8000/api/login`
- Check the status code:
  - 200 = Success
  - 401 = Wrong credentials
  - 404 = Endpoint not found
  - 500 = Server error
  - 0 or CORS error = Backend not running or CORS misconfigured

### 4. Test Backend Directly

**Using PowerShell (Windows):**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/login" -Method POST -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
```

**Using Python:**
```python
import requests
response = requests.post("http://localhost:8000/api/login", json={"username":"admin","password":"admin123"})
print(response.json())
```

## Common Issues and Solutions

### Issue 1: "Unable to connect to server"
**Cause**: Backend not running
**Solution**: 
```bash
uvicorn api.main:app --reload --port 8000
```

### Issue 2: CORS Error
**Cause**: Backend CORS not configured for frontend
**Solution**: Check `core/config.py` has:
```python
CORS_ORIGINS: list[str] = ["http://localhost:4200"]
```

### Issue 3: 404 Not Found
**Cause**: Wrong endpoint URL
**Solution**: Verify endpoint is at `/api/login` (not `/api/v1/login`)

### Issue 4: 401 Unauthorized
**Cause**: Wrong username/password
**Solution**: Use one of:
- admin / admin123
- demo / demo123
- user / user123

### Issue 5: ModuleNotFoundError
**Cause**: Dependencies not installed
**Solution**:
```bash
pip install -e ".[dev]"
# Or
pip install fastapi uvicorn python-jose[cryptography]
```

