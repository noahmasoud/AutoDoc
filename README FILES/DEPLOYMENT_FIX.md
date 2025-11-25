# Why UI Changes After Pushing to GitHub

## The Problem

When you push code to GitHub and it gets deployed (via CI/CD or manual deployment), the production build uses `environment.prod.ts` which has `localhost:8000`. This causes:

1. **API calls fail** - The deployed frontend tries to call `http://localhost:8000/api` which doesn't exist in the deployment environment
2. **UI breaks** - Without API connectivity, components can't load data
3. **Errors appear** - Network errors, missing data, broken functionality

## Root Causes

### 1. Production Environment Configuration

**File:** `src/environments/environment.prod.ts`

**Problem:**
```typescript
apiBase: 'http://localhost:8000/api'  // ❌ Won't work in production
```

**Fixed:**
```typescript
apiBase: '/api'  // ✅ Relative path works with same-origin deployment
```

### 2. Build-Time Environment Replacement

Angular uses `angular.json` to replace environment files during production builds:

```json
"fileReplacements": [
  {
    "replace": "src/environments/environment.ts",
    "with": "src/environments/environment.prod.ts"
  }
]
```

This means production builds automatically use `environment.prod.ts`.

### 3. Missing Components

Some components may be incomplete or missing files:
- Connections component is just a placeholder
- Auth component is empty
- Components reference services that may not exist

## Solutions

### Solution 1: Use Relative API URLs (Recommended for Same-Origin)

If frontend and backend are served from the same domain:

```typescript
// environment.prod.ts
apiBase: '/api'
```

**Pros:**
- Works automatically
- No configuration needed
- Works with reverse proxy

**Cons:**
- Requires backend to be on same domain

### Solution 2: Use Environment Variables (Recommended for Different Origins)

For deployments where frontend and backend are on different domains:

1. **Update `environment.prod.ts`:**
```typescript
export const environment = {
  production: true,
  apiBase: (window as any)['env']?.['apiUrl'] || '/api',
  apiUrl: (window as any)['env']?.['apiUrl'] || '/api',
};
```

2. **Create a script to inject environment variables:**
```html
<!-- index.html -->
<script>
  window['env'] = window['env'] || {};
  window['env']['apiUrl'] = 'https://your-api-domain.com/api';
</script>
```

3. **Or use build-time replacement:**
```bash
# Set environment variable during build
API_URL=https://your-api-domain.com/api npm run build
```

Then in `environment.prod.ts`:
```typescript
apiBase: process.env['API_URL'] || '/api',
```

### Solution 3: Configure Backend CORS

Make sure your backend CORS allows the deployment origin:

```python
# core/config.py or api/main.py
CORS_ORIGINS: list[str] = [
    "http://localhost:4200",  # Dev
    "https://your-production-domain.com",  # Production
]
```

## Quick Fix Applied

I've updated `environment.prod.ts` to use relative paths (`/api`) which will work if:
- Frontend and backend are on the same domain, OR
- You use a reverse proxy (nginx, Apache) that routes `/api` to the backend

## Verification Steps

1. **Check deployment logs:**
   - Look for CORS errors
   - Check for 404s on API calls
   - Verify environment file is being used

2. **Check browser console:**
   - Open DevTools on deployed site
   - Look for network errors
   - Check which API URLs are being called

3. **Test locally with production build:**
```bash
ng build --configuration production
# Serve the dist folder and test
```

## If You Need Different API URL for Production

Update `environment.prod.ts` with your actual production API URL:

```typescript
export const environment = {
  production: true,
  apiBase: 'https://your-api-server.com/api',
  apiUrl: 'https://your-api-server.com/api',
};
```

**Important:** Make sure:
- Backend CORS allows your frontend domain
- Backend is accessible from the internet
- HTTPS is used in production

## Next Steps

1. ✅ Update `environment.prod.ts` (done - changed to relative path)
2. Configure your deployment platform with correct API URL
3. Update backend CORS to allow production domain
4. Test the deployed application

