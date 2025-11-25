# Token Masking Implementation (FR-28, NFR-9)

## Overview

This document describes the comprehensive token masking implementation to ensure compliance with:
- **FR-28**: Token masking in all logs
- **NFR-9**: Secrets never logged or stored unencrypted

## Backend Implementation

### 1. Core Token Masking Utilities (`core/token_masking.py`)

**Functions:**
- `mask_token(token, visible_chars=0)`: Masks a single token string
- `mask_payload(payload, keys=None, deep=True)`: Masks sensitive fields in dictionaries (recursive)
- `mask_dict_keys(data, keys_to_mask)`: Masks specific keys in a dictionary

**Sensitive Field Names (auto-masked):**
- `token`
- `api_token`
- `password`
- `secret`
- `api_key`
- `access_token`
- `refresh_token`
- `auth_token`
- `authorization`
- `x-api-key`

### 2. Security Middleware (`core/security_middleware.py`)

**Features:**
- Automatically masks sensitive data in request/response logs
- Masks headers containing sensitive field names
- Masks request bodies for sensitive endpoints (`/connections`, `/login`, `/auth`)
- Masks error messages to prevent token leakage

**Endpoints Monitored:**
- `/api/connections` (save, test)
- `/api/login`
- `/api/auth`

### 3. Error Handler Masking (`core/errors.py`)

**Updates:**
- All exception handlers use `mask_exception_message()` to mask tokens in error responses
- Prevents token leakage through error traces
- Applied to: `IntegrityError`, `SQLAlchemyError`, and general `Exception` handlers

### 4. Connection Router Masking (`api/routers/connections.py`)

**Implementation:**
- All log statements use `mask_payload()` before logging
- Token is encrypted before database storage
- GET endpoint never returns token (only metadata)

## Frontend Implementation

### 1. Token Display Masking

**Connections Component (`src/app/pages/connections/connections.component.ts`):**
- Token field always shows `••••••••••` when loaded from saved connection
- Token is never displayed in plaintext after initial entry
- Token field clears on focus if it contains masked value

**Key Features:**
- `isTokenSaved` flag tracks if token is masked
- Form validation prevents sending masked token as real token
- Token field uses `type="password"` for input

### 2. Service Layer

**Connections Service (`src/app/services/connections.service.ts`):**
- Token is sent in POST requests only when user enters new value
- GET requests never include token
- Service doesn't store or cache tokens

### 3. Network Tab Considerations

**Important Note:**
- Browser DevTools Network tab will show request/response bodies including tokens
- This is expected behavior for API calls
- **Mitigation:**
  - Tokens are never cached in localStorage or sessionStorage
  - Tokens are cleared from form after save/test
  - Tokens are masked in backend logs (what appears in server logs)

## Database Storage

### Encryption (`core/encryption.py`)

**Implementation:**
- Tokens are encrypted using Fernet symmetric encryption
- Encryption key derived from `SECRET_KEY` using PBKDF2
- All tokens stored in `connections.encrypted_token` field
- Never stored as plaintext (NFR-9 compliance)

**Key Derivation:**
```python
PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
)
```

## Testing

### Unit Tests (`tests/unit/test_token_masking.py`)

**Coverage:**
- `mask_token()` with various inputs (None, empty, short, long)
- `mask_payload()` with simple and nested structures
- `mask_dict_keys()` with specific key lists
- Edge cases and custom key lists

### Integration Tests (`tests/integration/test_connection_security.py`)

**Tests:**
1. **Test Save Connection Masks Token in Logs**
   - Verifies raw token never appears in backend logs
   - Checks for masked version in logs

2. **Test GET Connection Omits Token**
   - Verifies token is never returned in GET response
   - Checks all response fields

3. **Test Test Connection Masks Token in Logs**
   - Verifies test endpoint logs are masked

4. **Test Error Response Omits Token**
   - Verifies error responses never include token

## Security Checklist

### Backend ✅
- [x] All log statements use `mask_payload()` before logging
- [x] Security middleware masks request/response bodies
- [x] Error handlers mask exception messages
- [x] Tokens encrypted in database
- [x] GET endpoints never return tokens
- [x] Sensitive headers masked in logs

### Frontend ✅
- [x] Token field always masked when loaded
- [x] Token never displayed in plaintext after save
- [x] Token field cleared on invalid token error
- [x] Password input type used for token field
- [x] No token caching in localStorage/sessionStorage

### Database ✅
- [x] Tokens encrypted at rest (Fernet)
- [x] Encryption key derived from SECRET_KEY
- [x] No plaintext token storage

### Testing ✅
- [x] Unit tests for masking functions
- [x] Integration tests for log masking
- [x] Integration tests for response omission
- [x] Error handling tests

## Usage Examples

### Backend Logging
```python
from core.token_masking import mask_payload

payload = {"api_token": "ATATT3x..."}
safe_payload = mask_payload(payload)
logger.info("Saving connection", extra={"payload": safe_payload})
# Logs: {"payload": {"api_token": "••••••••••"}}
```

### Frontend Display
```typescript
// Load connection - token is masked
this.connectionForm.patchValue({
  api_token: '••••••••••'
});
this.isTokenSaved = true;
```

### Error Handling
```python
from core.security_middleware import mask_exception_message

try:
    # ... operation with token ...
except Exception as e:
    masked_message = mask_exception_message(e)
    logger.error(masked_message)  # Token masked in error
```

## Compliance Status

### FR-28 (Token Masking) ✅
- All logs contain masked tokens (`••••••••••`)
- Request/response bodies masked in middleware
- Error messages masked
- No raw tokens in log files

### NFR-9 (Secrets Never Logged) ✅
- Tokens encrypted in database
- Tokens masked in all log statements
- Tokens never returned in GET responses
- Error traces don't expose tokens

## Known Limitations

1. **Browser Network Tab**: Cannot prevent tokens from appearing in browser DevTools Network tab (expected behavior for API calls)

2. **Client-Side Console**: Tokens may appear in browser console if explicitly logged (not recommended in production)

3. **Request Body**: Tokens must be sent in POST request body (HTTPS recommended in production)

## Recommendations

1. **Production:**
   - Use HTTPS for all API calls
   - Rotate SECRET_KEY regularly
   - Monitor logs for any accidental token exposure
   - Use environment variables for sensitive configuration

2. **Development:**
   - Never commit real tokens to repository
   - Use test tokens for development
   - Review logs to verify masking works

3. **Monitoring:**
   - Set up alerts for suspicious log patterns
   - Audit logs regularly for compliance
   - Review error logs to ensure masking is working

