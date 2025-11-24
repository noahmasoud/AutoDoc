# How to Test "Test Connection" in the UI

## Prerequisites

1. **Backend is running** on `http://localhost:8000`
2. **Frontend is running** on `http://localhost:4200`
3. **You have a Confluence instance** (or test credentials)

## Step-by-Step Testing Instructions

### 1. Navigate to Connections Page

1. Open your browser and go to `http://localhost:4200`
2. Log in (if not already logged in)
3. Click on **"Connections"** in the navigation bar

### 2. Fill in the Connection Form

Enter the following test data:

```
Confluence Base URL: https://your-domain.atlassian.net
Space Key: DOCS
API Token: ATATT3xFfGF0YOUR_ACTUAL_TOKEN_HERE
```

**Note:** Replace with your actual Confluence credentials:
- **Base URL**: Your Confluence instance URL (e.g., `https://company.atlassian.net`)
- **Space Key**: A valid space key in your Confluence (usually uppercase, e.g., `DOCS`, `DEV`)
- **API Token**: Your Confluence API token (starts with `ATATT...`)

### 3. Test the Connection

1. **Click the "Test Connection" button** (gray button next to "Save Connection")
2. **Observe the spinner**: The button should show "Testing..." with a spinning icon
3. **Wait for the result**: The test will take 2-5 seconds

### 4. Expected Results

#### ✅ **Success Case** (Connection OK)
- You'll see a **green success message**: "Connection OK - Successfully connected to Confluence"
- The button returns to normal state
- No token field is cleared

#### ❌ **Error Cases**

**Invalid Token:**
- You'll see a **red error message**: "Token invalid - please re-enter."
- The **API Token field is automatically cleared**
- You need to enter a new token

**Invalid Space Key:**
- You'll see: "Space 'SPACEKEY' not found. Please check the space key."
- Token field is NOT cleared

**Invalid Base URL:**
- You'll see: "Unable to connect to [URL]. Please check the base URL."
- Or: "Connection timeout - Please check your base URL and network connection."

**Network Error:**
- You'll see: "Connection timeout" or connection error message

### 5. Testing Different Scenarios

#### Test 1: Valid Connection
```
Base URL: https://your-domain.atlassian.net
Space Key: DOCS
API Token: [Valid token]
```
**Expected**: Green success message

#### Test 2: Invalid Token
```
Base URL: https://your-domain.atlassian.net
Space Key: DOCS
API Token: INVALID_TOKEN_12345
```
**Expected**: Red error "Token invalid - please re-enter." + Token field cleared

#### Test 3: Invalid Space Key
```
Base URL: https://your-domain.atlassian.net
Space Key: INVALID_SPACE
API Token: [Valid token]
```
**Expected**: Red error "Space 'INVALID_SPACE' not found..."

#### Test 4: Invalid URL
```
Base URL: https://invalid-domain-that-does-not-exist.com
Space Key: DOCS
API Token: [Any token]
```
**Expected**: Red error about connection failure

#### Test 5: Empty Form
- Leave fields empty
- Click "Test Connection"
**Expected**: Form validation errors appear

#### Test 6: Masked Token
- If you have a saved connection with masked token (`••••••••••`)
- Click "Test Connection"
**Expected**: Error "Please enter your API token to test the connection."

### 6. Visual Indicators

**During Test:**
- Button shows: "Testing..." with spinner icon
- Button is disabled (grayed out)
- "Save Connection" button is also disabled

**After Test:**
- Button returns to "Test Connection"
- Status message appears at top of form
- Buttons are re-enabled

### 7. Browser Developer Tools

To see the API call in action:

1. Open **Developer Tools** (F12)
2. Go to **Network** tab
3. Click "Test Connection"
4. Look for request to: `POST http://localhost:8000/api/connections/test`
5. Check:
   - **Request payload**: Should have base_url, space_key, api_token (token is NOT masked in request, but is masked in backend logs)
   - **Response**: Should have `{ "ok": true/false, "details": "...", "timestamp": "..." }`

### 8. Backend Logs

Check your backend terminal for:
- `"Testing connection"` log entry (with masked token)
- `"Connection test successful"` or error messages
- No raw token should appear in logs (FR-28 compliance)

## Troubleshooting

### Issue: "Test Connection" button doesn't work
- **Check**: Is the form valid? All fields must be filled
- **Check**: Browser console for JavaScript errors
- **Check**: Backend is running and accessible

### Issue: Always getting "Token invalid"
- **Verify**: Your API token is correct
- **Note**: Confluence API tokens require email:token format for Basic auth
- **Try**: Generate a new API token from Confluence settings

### Issue: Connection timeout
- **Check**: Base URL is correct and accessible
- **Check**: Network connection
- **Check**: Confluence instance is not behind a firewall

### Issue: CORS errors
- **Check**: Backend CORS is configured for `http://localhost:4200`
- **Check**: `core/config.py` has correct CORS_ORIGINS

## Security Notes

✅ **What's Secure:**
- Token is encrypted when saved to database
- Token is masked in backend logs (FR-28)
- Token is never returned in GET requests
- Token field is cleared if invalid

⚠️ **Important:**
- Token is sent in POST request body (HTTPS recommended in production)
- Token appears in browser network tab (normal for API calls)
- Token is NOT logged in backend (masked)

## Quick Test Checklist

- [ ] Form validation works (empty fields show errors)
- [ ] Spinner appears during test
- [ ] Success message appears for valid connection
- [ ] Error message appears for invalid connection
- [ ] Token field clears on "Token invalid" error
- [ ] Buttons are disabled during test
- [ ] Status messages are color-coded (green/red)
- [ ] Backend logs show masked token (not raw token)

## Example Test Data

If you don't have a real Confluence instance, you can test with:

```
Base URL: https://test.atlassian.net
Space Key: TEST
API Token: ATATT3xFfGF0TEST_TOKEN_1234567890
```

**Note**: This will fail, but you can verify the error handling works correctly.

