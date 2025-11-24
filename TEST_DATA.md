# Test Data for AutoDoc Frontend UI

Use this test data to manually test the Connections and Rules pages.

## 🔗 Connections Page Test Data

### Test Connection 1 (Example Confluence Instance)
```
Confluence Base URL: https://your-company.atlassian.net
Space Key: DOCS
API Token: ATATT3xFfGF0EXAMPLE_TOKEN_STRING_HERE_1234567890abcdef
```

**Notes:**
- The base URL should be a valid HTTPS URL format
- Space Key is typically uppercase (e.g., DOCS, DEV, PROD)
- API Token format: Starts with "ATATT" followed by alphanumeric characters
- To get a real API token: Go to Confluence → Account Settings → Security → API Tokens → Create API Token

### Test Connection 2 (Alternative)
```
Confluence Base URL: https://test-confluence.atlassian.net
Space Key: TEST
API Token: ATATT3xFfGF0ANOTHER_EXAMPLE_TOKEN_9876543210fedcba
```

**Validation:**
- ✅ Valid URL format: `https://domain.atlassian.net`
- ✅ Space Key: Any non-empty string (typically uppercase)
- ✅ API Token: Any non-empty string (will be encrypted in database)

---

## 📋 Rules Page Test Data

### Rule 1: Python API Files
```
Rule Name: Python API Changes
Selector: src/api/**/*.py
Space Key: DOCS
Page ID: 123456789
Template ID: (Leave empty or select from dropdown if templates exist)
Auto-approve: ☐ (unchecked)
```

**Explanation:**
- **Selector**: Uses glob pattern `src/api/**/*.py` to match all Python files in `src/api/` and subdirectories
- **Space Key**: Must match a Confluence space
- **Page ID**: Numeric ID of the Confluence page where documentation will be updated

### Rule 2: Frontend TypeScript Files (Regex Pattern)
```
Rule Name: Frontend TypeScript Changes
Selector: regex:^src/app/.*\.ts$
Space Key: DOCS
Page ID: 987654321
Template ID: (Leave empty)
Auto-approve: ☑ (checked)
```

**Explanation:**
- **Selector**: Uses regex pattern `regex:^src/app/.*\.ts$` to match TypeScript files in `src/app/` directory
- Note: Must start with `regex:` prefix for regex patterns

### Rule 3: Configuration Files
```
Rule Name: Config File Updates
Selector: **/*.config.{js,ts,json}
Space Key: DOCS
Page ID: 456789123
Template ID: (Leave empty)
Auto-approve: ☐ (unchecked)
```

**Explanation:**
- **Selector**: Glob pattern matching config files with multiple extensions

### Rule 4: All Python Files (Simple Pattern)
```
Rule Name: All Python Files
Selector: **/*.py
Space Key: TEST
Page ID: 111222333
Template ID: (Leave empty)
Auto-approve: ☐ (unchecked)
```

---

## 🧪 Testing Workflow

### Step 1: Test Connections Page
1. Navigate to **Connections** page
2. Enter Test Connection 1 data
3. Click **Save Connection**
4. Verify success message appears
5. Refresh page - connection should load with masked token
6. Try updating the Space Key only (token should remain masked)

### Step 2: Test Rules Page
1. Navigate to **Rules** page
2. Click **Create New Rule**
3. Enter Rule 1 data
4. Click **Create Rule**
5. Verify rule appears in the list
6. Click **Edit** on the rule
7. Modify the selector to `src/api/**/*.{py,ts}`
8. Click **Update Rule**
9. Verify changes are saved
10. Create Rule 2 with regex pattern
11. Verify both rules appear in the list
12. Test **Delete** functionality

### Step 3: Test Validation
1. Try submitting empty form - should show validation errors
2. Try invalid URL format (e.g., `not-a-url`) - should show error
3. Try creating rule with duplicate name - should show error
4. Test selector patterns:
   - Valid glob: `src/**/*.py` ✅
   - Valid regex: `regex:^src/.*\.py$` ✅
   - Invalid (no prefix): `^src/.*\.py$` (will work as glob, not regex)

---

## 📝 Selector Pattern Examples

### Glob Patterns (Default)
```
src/**/*.py                    # All Python files in src/ and subdirectories
**/*.test.{js,ts}              # Test files with .js or .ts extension
src/api/**/*                   # All files in src/api/ directory tree
*.config.js                    # Config files in root directory
src/components/**/*.component.ts  # Component files in components directory
```

### Regex Patterns (Must start with "regex:")
```
regex:^src/api/.*\.py$         # Python files in src/api/ directory
regex:^.*\.test\.(js|ts)$      # Test files anywhere
regex:^src/.*\.(py|ts)$        # Python or TypeScript files in src/
regex:^config/.*\.json$        # JSON files in config/ directory
```

---

## ⚠️ Important Notes

1. **Confluence API Token**: 
   - For real testing, you need a valid Confluence API token
   - Generate at: `https://id.atlassian.com/manage-profile/security/api-tokens`
   - Format: `ATATT3xFfGF0...` (long alphanumeric string)

2. **Confluence Page ID**:
   - Find page ID in Confluence URL: `https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456789/Page+Title`
   - The number `123456789` is the Page ID

3. **Space Key**:
   - Usually found in Confluence URL or space settings
   - Typically uppercase (e.g., DOCS, DEV, PROD)

4. **Backend Testing**:
   - Ensure backend is running on `http://localhost:8000`
   - Check browser console for API errors
   - Verify CORS is enabled in backend

---

## 🔍 Expected Behavior

### Connections Page
- ✅ Form validates URL format
- ✅ Token is masked after save (shows `••••••••••`)
- ✅ Token field clears when focused (to enter new token)
- ✅ Success message on save
- ✅ Connection details display after save

### Rules Page
- ✅ Form validates required fields
- ✅ Rules list displays all created rules
- ✅ Edit populates form with existing data
- ✅ Delete shows confirmation dialog
- ✅ Template dropdown loads available templates
- ✅ Selector help text shows based on pattern type

---

## 🐛 Troubleshooting

**Connection fails to save:**
- Check backend is running
- Verify API endpoint: `POST /api/connections`
- Check browser console for errors
- Verify CORS settings

**Rules not loading:**
- Check API endpoint: `GET /api/v1/rules`
- Verify database has rules table
- Check browser network tab for API calls

**Validation errors:**
- URL must start with `http://` or `https://`
- All required fields must be filled
- Selector cannot be empty

