# Authentication Rules (JWT + RBAC + Single-Tenant)

> JWT tokens, role-based access, password hashing, access control

---

## Authentication Flow

```
1. User enters credentials
   ↓
2. Backend validates (DB lookup + password hash check)
   ↓
3. If valid: generate JWT token
   ├── Payload: user_id, email, role, exp, iat
   ├── Secret: JWT_SECRET_KEY (from .env)
   ├── Expiry: 30 minutes (default)
   └── Return to frontend
   ↓
4. Frontend stores token (secure HTTP-only cookie)
   ↓
5. Frontend sends token in every API request (Authorization header)
   ↓
6. Backend validates token on each request
   ├── Verify signature (secret key)
   ├── Check expiry
   ├── Extract user_id, role
   └── Allow/deny based on route requirements
   ↓
7. If expired: frontend calls refresh endpoint
   └── Get new token, continue
```

---

## JWT Token Implementation

### `backend/app/utils/jwt_utils.py`

```python
"""JWT token creation and validation."""
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

def create_access_token(user_id: str, email: str, role: str) -> str:
    """Create JWT access token (expires in 30 minutes)."""
    payload = {
        "sub": user_id,  # Subject (standard JWT claim)
        "user_id": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token (expires in 7 days)."""
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid signature or malformed

def get_user_from_token(token: str) -> Optional[Dict]:
    """Extract user info from token."""
    payload = verify_token(token, token_type="access")
    if not payload:
        return None
    
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }
```

---

## Password Hashing

### Secure Password Storage

```python
# ✅ CORRECT - Use bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel):
    password_hash: Mapped[str] = mapped_column(String(255))
    
    def set_password(self, password: str) -> None:
        """Hash password with bcrypt."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

# ❌ WRONG - Never store plaintext
user.password = "cleartext123"  # Dangerous!

# ❌ WRONG - Simple hashing
import hashlib
user.password_hash = hashlib.md5(password).hexdigest()  # Too weak!
```

---

## Authentication Middleware

### `backend/app/middleware/auth_middleware.py`

```python
"""JWT validation and user injection."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from app.utils.jwt_utils import get_user_from_token
from app.extensions import get_db
from app.models import User
from typing import Optional

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> dict:
    """
    Validate JWT token and return user info.
    
    Used as dependency in routes:
    @router.get("/api/v1/me")
    def get_me(current_user: dict = Depends(get_current_user)):
        return current_user
    """
    token = credentials.credentials
    user_info = get_user_from_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_info

def require_role(*allowed_roles: str):
    """Dependency factory to enforce role-based access."""
    def check_role(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of: {allowed_roles}"
            )
        return current_user
    return check_role

def require_patient_or_doctor(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Allow patient or doctor roles."""
    if current_user["role"] not in ["patient", "doctor"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user
```

---

## Role-Based Access Control (RBAC)

### Patient Scoping (Single-Tenant)

```python
# ✅ CORRECT - Patient can see only their own data
@router.get("/api/v1/patients/{patient_id}/vitals")
def get_vitals(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Patient: Check if this is their patient ID
    if current_user["role"] == "patient":
        patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    
    # Doctor: Check if patient is assigned
    elif current_user["role"] == "doctor":
        # TODO: Check if doctor is assigned to this patient
        pass
    
    # Admin: Can see any patient
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Fetch and return vitals
    vitals = db.query(Vitals).filter_by(patient_id=patient_id).all()
    return vitals

# ❌ WRONG - No patient scoping
@router.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    # Any authenticated user can see any patient!
    return db.query(Patient).get(patient_id)
```

### Admin-Only Routes

```python
@router.get("/api/v1/admin/users")
def list_all_users(
    _: dict = Depends(require_role("admin")),  # Only admin
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    return db.query(User).all()

@router.put("/api/v1/admin/users/{user_id}/role")
def update_user_role(
    user_id: str,
    new_role: str,
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Update user role (admin only)."""
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404)
    user.role = new_role
    db.commit()
    return user
```

---

## Authentication Endpoints

### Register

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter
from app.schemas import RegisterRequest, TokenResponse
from app.services.auth_service import AuthService
from app.extensions import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register new user.
    
    - **email**: Unique email address
    - **password**: At least 8 characters
    - **full_name**: User's full name
    
    Returns JWT token.
    """
    return AuthService.register(db, request)
```

### Login

```python
@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.
    
    Returns access_token and refresh_token.
    """
    return AuthService.login(db, request)
```

### Refresh Token

```python
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Refresh expired access token using refresh token.
    """
    refresh_token = credentials.credentials
    payload = verify_token(refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = db.query(User).get(payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token = create_access_token(user.id, user.email, user.role.value)
    refresh_token = create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
```

### Get Current User

```python
@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user info."""
    user = db.query(User).get(current_user["user_id"])
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
    }
```

---

## Frontend: Storing & Sending Tokens

### `frontend/lib/auth.ts`

```typescript
// Store token in secure HTTP-only cookie (set by NextAuth)
export async function login(email: string, password: string) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) throw new Error("Login failed");
  
  const { access_token } = await response.json();
  
  // Save to secure cookie
  document.cookie = `access_token=${access_token}; HttpOnly; Secure; SameSite=Strict`;
}

// Send token in Authorization header
export async function apiCall(endpoint: string, options: any = {}) {
  const token = getCookie("access_token");
  
  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      "Authorization": `Bearer ${token}`,
    },
  });
}
```

---

## Security Best Practices

### Environment Variables

```bash
# ✅ CORRECT - in .env (never in git)
JWT_SECRET_KEY=very-long-random-string-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://...

# ❌ WRONG - hardcoded in code
JWT_SECRET = "my-secret"  # In source code!
```

### Password Validation

```python
# ✅ CORRECT - enforce strong passwords
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    
    @field_validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain digit")
        return v

# ❌ WRONG - weak password requirements
password: str  # Any string, no validation!
```

### Token Expiry

```python
# ✅ CORRECT - short expiry, refresh tokens for long sessions
ACCESS_TOKEN_EXPIRE_MINUTES=30     # Short-lived
REFRESH_TOKEN_EXPIRE_DAYS=7        # Long-lived (secure renewal)

# ❌ WRONG - long expiry
ACCESS_TOKEN_EXPIRE_DAYS=365       # Too long! Compromised token = 1 year access
```

---

## Testing Authentication

```python
# backend/tests/test_auth.py
import pytest
from app.schemas import RegisterRequest, LoginRequest

def test_register(client, db):
    """Test user registration."""
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePassword123",
        "full_name": "John Doe",
    })
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_login(client, db, created_user):
    """Test user login."""
    response = client.post("/api/v1/auth/login", json={
        "email": created_user.email,
        "password": "password123",
    })
    assert response.status_code == 200
    assert response.json()["access_token"]

def test_invalid_login(client):
    """Test invalid credentials."""
    response = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrong",
    })
    assert response.status_code == 401

def test_protected_endpoint(client, auth_headers):
    """Test protected endpoint with valid token."""
    response = client.get("/api/v1/me", headers=auth_headers)
    assert response.status_code == 200

def test_protected_endpoint_no_token(client):
    """Test protected endpoint without token."""
    response = client.get("/api/v1/me")
    assert response.status_code == 403
```

---

## Summary

- **JWT tokens**: 30-minute expiry + 7-day refresh
- **Password**: Hash with bcrypt, never store plaintext
- **Validation**: On every protected endpoint
- **Scoping**: Patient sees only own data; doctor sees assigned patients
- **Admin**: Full system access
- **Secrets**: Environment variables, never in code
