# FastAPI Cookbook — Complete Summary

> *Giunio De Luca, Packt Publishing, 2024*

---

## Quick Reference Cheatsheet

| Category | Snippet | Notes |
|---|---|---|
| **Install** | `pip install fastapi[all]` | Includes uvicorn, pydantic, etc. |
| **Run (dev)** | `fastapi dev app/main.py` | Auto-reload enabled |
| **Run (prod)** | `fastapi run app/main.py --port 80` | No reload |
| **App instance** | `app = FastAPI()` | Entry point |
| **Router** | `router = APIRouter(); app.include_router(router)` | Modular route grouping |
| **Path param** | `@app.get("/items/{item_id}")` | Auto-typed from annotation |
| **Query param** | `def read(skip: int = 0, limit: int = 10)` | Params not in path = query |
| **Request body** | `def create(item: Item)` where `Item(BaseModel)` | Pydantic validation |
| **Response model** | `@app.get("/", response_model=ItemOut)` | Filters output fields |
| **Field validation** | `Field(..., gt=0, max_length=100)` | Pydantic constraints |
| **Custom validator** | `@field_validator("age")` | Class method on BaseModel |
| **Dependency** | `Depends(get_db)` | DI for DB sessions, auth, etc. |
| **Async endpoint** | `async def route():` | Use for I/O-bound work |
| **Sync endpoint** | `def route():` | Runs in threadpool |
| **Background task** | `background_tasks.add_task(fn, *args)` | Lightweight async work |
| **File upload** | `file: UploadFile = File(...)` | `shutil.copyfileobj` to save |
| **File download** | `return FileResponse(path=..., filename=...)` | Sets Content-Disposition |
| **SQLAlchemy engine** | `create_engine("sqlite:///./db.sqlite3")` | Sync engine |
| **Async engine** | `create_async_engine("sqlite+aiosqlite:///./db")` | Requires aiosqlite |
| **DB session dep** | `def get_db(): db=Session(); try: yield db; finally: db.close()` | Generator dependency |
| **MongoDB** | `MongoClient()` (sync) / `AsyncIOMotorClient()` (async) | pymongo / motor |
| **Redis cache** | `aioredis.from_url("redis://localhost"); await r.set(k, v, ex=3600)` | TTL in seconds |
| **JWT create** | `jose.jwt.encode({"sub": user, "exp": exp}, SECRET, algorithm="HS256")` | python-jose |
| **JWT decode** | `jose.jwt.decode(token, SECRET, algorithms=["HS256"])` | Raises JWTError |
| **OAuth2 scheme** | `OAuth2PasswordBearer(tokenUrl="token")` | Returns token string |
| **Password hash** | `CryptContext(schemes=["bcrypt"]).hash(pw)` | passlib |
| **RBAC** | `Annotated[User, Depends(RoleChecker(["admin"]))]` | Callable class dep |
| **TestClient** | `from fastapi.testclient import TestClient; c = TestClient(app)` | Sync tests |
| **Async test** | `async with AsyncClient(transport=ASGITransport(app=app)) as c:` | httpx + pytest-asyncio |
| **Override dep** | `app.dependency_overrides[get_db] = override_get_db` | Test isolation |
| **Alembic init** | `alembic init alembic` | Migration scaffolding |
| **Alembic migrate** | `alembic revision --autogenerate -m "msg"; alembic upgrade head` | Auto-detect changes |
| **WebSocket** | `@app.websocket("/ws"); await ws.accept(); await ws.receive_text()` | Full-duplex |
| **GraphQL** | `GraphQLRouter(strawberry.Schema(Query)); app.include_router(gql, prefix="/graphql")` | strawberry-graphql |
| **gRPC gateway** | `grpc.aio.insecure_channel("localhost:50051")` | FastAPI as REST proxy |
| **Rate limit** | `@limiter.limit("5/minute")` | slowapi |
| **Profiling** | `Profiler(interval=0.001, async_mode="enabled")` | pyinstrument |
| **CORS** | `app.add_middleware(CORSMiddleware, allow_origins=[...])` | Cross-origin |
| **Docker** | `FROM python:3.10; CMD ["fastapi", "run", "app/main.py", "--port", "80"]` | Production image |
| **Gunicorn** | `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker` | Multi-worker; `(2*cores)+1` |
| **Hatch build** | `hatch new "Project"; hatch shell; hatch build -t sdist ../dist` | Packaging |

---

## Chapter 1: First Steps with FastAPI

### Setting up your development environment

- Install with `pip install fastapi[all]` — bundles uvicorn, pydantic, starlette, and other essentials
- Always use a **virtual environment**: `python -m venv venv && source venv/bin/activate`
- Run the dev server: `uvicorn main:app --reload` (or `fastapi dev main.py` in newer versions)

### Creating a new FastAPI project

- Recommended structure for larger projects:

```
project/
├── src/           # Application code (models, routes, services)
├── tests/         # Test suite, mirrors src structure
├── docs/          # Documentation
├── requirements.txt
└── main.py
```

- Separate concerns into subdirectories under `src/`: models, routes, services
- Use `APIRouter` in each route module, then aggregate with `app.include_router()` in `main.py`

```python
# src/routes/items.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# main.py
from fastapi import FastAPI
from src.routes import items
app = FastAPI()
app.include_router(items.router)
```

### Understanding FastAPI basics

- Built on **Starlette** (ASGI) and **Pydantic** (data validation)
- Endpoints can be `async def` (non-blocking, ideal for I/O) or `def` (run in a threadpool automatically)
- Automatic interactive docs at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### Defining your first API endpoint

- Decorators: `@app.get()`, `@app.post()`, `@app.put()`, `@app.delete()`, `@app.patch()`
- Status codes via `status_code` parameter or `fastapi.status` constants

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Hello World"}
```

### Working with path and query parameters

- **Path parameters**: defined in the route string, auto-cast from type annotations
- **Query parameters**: any function parameter not in the path string; use `Optional` or defaults for optional ones

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    # item_id is path param (required, int)
    # q is query param (optional, string)
    return {"item_id": item_id, "q": q}
```

### Defining and using request and response models

- **Pydantic `BaseModel`** for both request bodies and response shaping
- `Field(...)` for constraints: `min_length`, `max_length`, `gt`, `lt`, `ge`, `le`, `pattern`
- `response_model` on the decorator filters the output to only declared fields

```python
from pydantic import BaseModel, Field

class Book(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    author: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., gt=1900, lt=2100)

class BookOut(BaseModel):
    title: str
    author: str

@app.post("/books", response_model=BookOut)
async def create_book(book: Book):
    # book is fully validated; response only includes title & author
    return book
```

### Handling errors and exceptions

- `HTTPException(status_code=..., detail=...)` for standard error responses
- Custom exception handlers via `@app.exception_handler(ExceptionClass)`
- Override `RequestValidationError` for custom validation error formatting

```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": "Oops! Something went wrong"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return PlainTextResponse(
        f"Validation error:\n{json.dumps(exc.errors(), indent=2)}",
        status_code=status.HTTP_400_BAD_REQUEST
    )
```

---

## Chapter 2: Working with Data

### Setting up SQL databases

- **SQLAlchemy ORM** with the modern `DeclarativeBase` + `Mapped`/`mapped_column` style (SQLAlchemy 2.0+)
- Engine creation, session factory, and a `get_db` generator dependency for request-scoped sessions

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Understanding CRUD operations with SQLAlchemy

- **Create**: instantiate model, `db.add(obj)`, `db.commit()`, `db.refresh(obj)`
- **Read**: `db.query(Model).filter(Model.id == id).first()` or `.all()`
- **Update**: fetch → modify attributes → `db.commit()`
- **Delete**: fetch → `db.delete(obj)` → `db.commit()`

```python
from fastapi import Depends
from sqlalchemy.orm import Session

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Integrating MongoDB for NoSQL data storage

- **pymongo** for synchronous access; `motor` for async (covered in Ch7)
- `MongoClient()` → database → collection pattern
- `ObjectId` from `bson` for document IDs; validate with `ObjectId.is_valid()`

```python
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient()
database = client.mydatabase
user_collection = database["users"]

@app.post("/users")
def create_user(user: UserCreate):
    result = user_collection.insert_one(user.model_dump())
    return {"id": str(result.inserted_id)}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return user
```

### Working with data validation and serialization

- **`EmailStr`** from pydantic for email validation (requires `email-validator` package)
- **`field_validator`** for custom validation logic on individual fields
- **`model_dump()`** to serialize to dict; **`model_copy(update={...})`** for partial updates

```python
from pydantic import BaseModel, EmailStr, field_validator

class User(BaseModel):
    name: str
    email: EmailStr
    age: int

    @field_validator("age")
    def validate_age(cls, value):
        if value < 18 or value > 100:
            raise ValueError("Age must be between 18 and 100")
        return value
```

### Working with file uploads and downloads

- **Upload**: `UploadFile` + `File(...)`, save with `shutil.copyfileobj`
- **Download**: `FileResponse` with explicit `path` and `filename`

```python
import shutil
from pathlib import Path
from fastapi import File, UploadFile
from fastapi.responses import FileResponse

@app.post("/uploadfile")
async def upload_file(file: UploadFile = File(...)):
    with open(f"uploads/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}

@app.get("/downloadfile/{filename}", response_class=FileResponse)
async def download_file(filename: str):
    filepath = Path(f"uploads/{filename}")
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    return FileResponse(path=str(filepath), filename=filename)
```

### Handling asynchronous data operations

- `async def` endpoints free the event loop during I/O waits — critical for concurrent performance
- Sync `def` endpoints block a threadpool thread for the duration of the call
- Demonstrated with `asyncio.gather` benchmarking:

```python
import asyncio
from httpx import AsyncClient

async def make_requests(n: int, path: str):
    async with AsyncClient(base_url="http://localhost:8000") as client:
        tasks = (client.get(path, timeout=float("inf")) for _ in range(n))
        await asyncio.gather(*tasks)

# Result: 100 sync requests ~6.4s vs 100 async requests ~2.4s
```

- **Key takeaway**: use `async def` for I/O-bound endpoints (DB queries, HTTP calls, file I/O); use sync `def` for CPU-bound work (it runs in a threadpool and won't block the event loop)

### Securing sensitive data and best practices

- Store secrets in **environment variables**, never hardcode
- Hash passwords with **bcrypt** via `passlib`
- Use **HTTPS** in production
- Apply **RBAC** to restrict endpoint access by role
- Database-level security: parameterized queries (SQLAlchemy handles this), least-privilege DB users

---

## Chapter 3: Building RESTful APIs with FastAPI

### Creating CRUD operations

- Example: CSV-backed Task Manager demonstrating full CRUD without a database
- `csv.DictReader` / `csv.DictWriter` for persistence
- Pydantic models with inheritance: `Task(BaseModel)` for input, `TaskWithID(Task)` adding `id: int` for output

```python
class Task(BaseModel):
    title: str
    description: str
    status: str

class TaskWithID(Task):
    id: int

# Read all tasks
def read_tasks_from_csv() -> list[TaskWithID]:
    with open("tasks.csv", "r") as f:
        reader = csv.DictReader(f)
        return [TaskWithID(**row) for row in reader]
```

### Creating RESTful Endpoints

- Follow REST conventions: `GET /tasks` (list), `GET /tasks/{id}` (detail), `POST /tasks` (create), `PUT /tasks/{id}` (full update), `DELETE /tasks/{id}` (remove)
- Use appropriate HTTP status codes: 200 (OK), 201 (Created), 204 (No Content), 404 (Not Found)

### Testing your RESTful API

- `TestClient` from `fastapi.testclient` for quick synchronous tests
- Tests can verify status codes, response bodies, and side effects

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Test", "description": "Desc", "status": "pending"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test"
```

### Handling complex queries and filtering

- Use `Optional` query parameters with defaults of `None`
- Implement keyword-based search by checking if the search term appears in relevant fields
- Chain filters: each `Optional` param narrows results only when provided

```python
from typing import Optional

@app.get("/tasks")
def get_tasks(
    status: Optional[str] = None,
    keyword: Optional[str] = None
):
    tasks = read_tasks_from_csv()
    if status:
        tasks = [t for t in tasks if t.status == status]
    if keyword:
        tasks = [t for t in tasks if keyword.lower() in t.title.lower()
                 or keyword.lower() in t.description.lower()]
    return tasks
```

### Versioning your API

Five strategies presented:

1. **URL path versioning** (most common): `/v1/tasks`, `/v2/tasks` — separate routers per version
2. **Query parameter versioning**: `?version=1` — single endpoint dispatches by param
3. **Header versioning**: `X-API-Version: 2` — clean URLs, version in request header
4. **Consumer-based versioning**: different behavior per API key / consumer identity
5. **Semantic versioning**: version the API spec itself (major.minor.patch)

```python
# URL path versioning
v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")

@v1_router.get("/tasks")
def get_tasks_v1(): ...

@v2_router.get("/tasks")
def get_tasks_v2(): ...  # enhanced response schema

app.include_router(v1_router)
app.include_router(v2_router)
```

### Securing your API with OAuth2

- `OAuth2PasswordBearer(tokenUrl="token")` creates a dependency that extracts the bearer token
- `OAuth2PasswordRequestForm` for the login endpoint (username + password form data)

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    # token is the raw bearer token string
    user = verify_token(token)
    return {"user": user.username}
```

### Documenting your API with Swagger and Redoc

- Auto-generated at `/docs` (Swagger) and `/redoc` (ReDoc)
- Customize with `FastAPI(title=..., description=..., version=...)` constructor params
- Override the OpenAPI schema with `app.openapi()` method for advanced customization
- Add `tags`, `summary`, `description` to individual endpoints for better organization

---

## Chapter 4: Authentication and Authorization

### Setting up user registration

- Hash passwords with `passlib` + `bcrypt`: `CryptContext(schemes=["bcrypt"], deprecated="auto")`
- Use the **`lifespan`** context manager (replaces deprecated `@app.on_event`) for startup/shutdown logic
- Handle duplicate registration with `IntegrityError` catch

```python
from passlib.context import CryptContext
from contextlib import asynccontextmanager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, seed data, etc.
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup

app = FastAPI(lifespan=lifespan)

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed)
    try:
        db.add(db_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User registered"}
```

### Working with OAuth2 and JWT for authentication

- **python-jose** for JWT encoding/decoding
- Token payload: `{"sub": username, "exp": expiration_datetime}`
- Standard flow: login → verify password → issue JWT → client sends `Authorization: Bearer <token>`

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Setting up RBAC

- Define roles with `enum.Enum`: `class Role(str, Enum): admin = "admin"; user = "user"`
- Create a callable dependency class `RoleChecker` that validates the current user's role
- Chain dependencies with `Annotated` for clean, reusable type aliases

```python
from enum import Enum
from typing import Annotated

class Role(str, Enum):
    admin = "admin"
    user = "user"

class RoleChecker:
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

AdminUser = Annotated[User, Depends(RoleChecker([Role.admin]))]

@app.get("/admin")
def admin_only(user: AdminUser):
    return {"message": f"Welcome admin {user.username}"}
```

### Using third-party authentication

- Example: GitHub OAuth2 flow using `httpx`
- Flow: redirect user to GitHub → user authorizes → GitHub redirects back with `code` → exchange code for access token → fetch user profile

```python
import httpx

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@app.get("/login/github")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}"
    )

@app.get("/github-callback")
async def github_callback(code: str):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            params={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
            headers={"Accept": "application/json"}
        )
        access_token = token_resp.json()["access_token"]
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    return user_resp.json()
```

### Implementing MFA

- **TOTP** (Time-based One-Time Password) with `pyotp`
- Generate a secret per user, produce a provisioning URI for authenticator apps
- Verify the 6-digit code on login

```python
import pyotp

# During setup:
secret = pyotp.random_base32()
totp = pyotp.TOTP(secret)
provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="MyApp")
# Store secret with user record; share provisioning_uri (or QR code) with user

# During login verification:
totp = pyotp.TOTP(user.totp_secret)
if not totp.verify(submitted_code):
    raise HTTPException(status_code=401, detail="Invalid MFA code")
```

### Handling API key authentication

- Simple scheme: check an `X-API-Key` header against stored keys
- Implement as a `Depends()` function or `Security()` dependency

### Handling session cookies and logout functionality

- Set cookies with `response.set_cookie(key="session_id", value=token, httponly=True)`
- Clear on logout with `response.delete_cookie("session_id")`
- `httponly=True` prevents JavaScript access (XSS protection)

---

## Chapter 5: Testing and Debugging FastAPI Applications

> ⚡ **Extra detail section** — per user request

### Setting up testing environments

- Install: `pip install pytest httpx pytest-asyncio`
- **`conftest.py`**: shared fixtures (app instance, test client, test DB session)
- Test DB isolation: use **in-memory SQLite** with `StaticPool` to avoid polluting production data

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite://"  # in-memory

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### Writing and running unit tests

- Tests as plain functions prefixed with `test_`
- Use `assert` statements directly (pytest rewrites them for detailed output)
- Group related tests in classes: `class TestUserEndpoints:`

```python
def test_create_user(client):
    response = client.post("/users", json={"name": "Alice", "email": "a@b.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert "id" in data
```

### Testing API Endpoints

- **Sync testing**: `TestClient(app)` — wraps requests, no need for async
- **Async testing**: `httpx.AsyncClient` with `ASGITransport` — required for testing `async def` endpoints that use async dependencies

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/async-endpoint")
        assert response.status_code == 200
```

- **Dependency overrides** (`app.dependency_overrides[original] = replacement`) are the primary mechanism for test isolation — mock DB sessions, auth, external services

### Running tests techniques

- `pytest` — run all tests
- `pytest -v` — verbose output
- `pytest --cov=app` — coverage report (requires `pytest-cov`)
- `pytest -m integration` — run only tests marked with `@pytest.mark.integration`
- **Markers** for categorization:

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
]

@pytest.mark.integration
def test_db_connection(client):
    ...
```

### Handling logging messages

- Standard library `logging` module with configurable handlers
- **`StreamHandler`** for console output, **`TimedRotatingFileHandler`** for rotating log files
- **`ColourizedFormatter`** (from uvicorn) for colored terminal output
- Logging middleware to log every request/response:

```python
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)

# Console handler with color
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(ColourizedFormatter("%(levelprefix)s %(message)s"))
logger.addHandler(stream_handler)

# File handler with rotation
file_handler = TimedRotatingFileHandler("app.log", when="midnight", backupCount=7)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)
```

- **Logging middleware pattern**: wrap `call_next(request)` to log request method, URL, status code, and timing

### Debugging techniques

- **PDB**: `import pdb; pdb.set_trace()` — interactive debugger in terminal
- **debugpy**: remote debugging, attach from VS Code or PyCharm
  - `pip install debugpy`
  - Add `debugpy.listen(("0.0.0.0", 5678))` at startup
  - Configure IDE to attach to port 5678
- **PyCharm**: native FastAPI run configuration with breakpoints

### Performance testing for high traffic applications

- **Locust** for load testing: define user behavior as a Python class
- `HttpUser` base class, `@task` decorator for weighted actions
- Run headless for CI/CD integration

```python
# locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_items(self):
        self.client.get("/items")

    @task(1)
    def create_item(self):
        self.client.post("/items", json={"name": "test", "price": 9.99})
```

```bash
# Run headless
locust --headless --users 10 --spawn-rate 1 -H http://localhost:8000
```

---

## Chapter 6: Integrating FastAPI with SQL Databases

### Setting up SQLAlchemy

- **SQLAlchemy 2.0+ async** with `create_async_engine` and `AsyncSession`
- Requires an async driver: `aiosqlite` for SQLite, `asyncpg` for PostgreSQL

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./db.sqlite3"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Dependency
async def get_db():
    async with async_session() as session:
        yield session
```

### Implementing CRUD operations

- Async CRUD uses `await` with session methods and `async with session.begin()` for transactions

```python
from sqlalchemy import select

@app.post("/items")
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404)
    return item
```

### Working with migrations

- **Alembic** for database schema migrations
- Setup: `alembic init alembic` → configure `alembic.ini` and `env.py` with your DB URL and Base metadata
- Workflow: modify models → `alembic revision --autogenerate -m "description"` → `alembic upgrade head`
- Rollback: `alembic downgrade -1`

### Handling relationships in SQL databases

- **One-to-one**: `relationship()` with `uselist=False`
- **Many-to-one / One-to-many**: `ForeignKey` + `relationship()` with `back_populates`
- **Many-to-many**: association table + `relationship()` with `secondary`

```python
# Many-to-many example
from sqlalchemy import Table, Column, ForeignKey, Integer

# Association table
student_course = Table(
    "student_course", Base.metadata,
    Column("student_id", Integer, ForeignKey("student.id")),
    Column("course_id", Integer, ForeignKey("course.id")),
)

class Student(Base):
    __tablename__ = "student"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    courses: Mapped[list["Course"]] = relationship(secondary=student_course, back_populates="students")

class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    students: Mapped[list["Student"]] = relationship(secondary=student_course, back_populates="courses")
```

### Optimizing SQL queries for performance

- **N+1 problem**: accessing lazy-loaded relationships in a loop triggers one query per row
- Fix with **eager loading**: `joinedload()` or `selectinload()`
- **`load_only()`** to fetch only specific columns

```python
from sqlalchemy.orm import joinedload, load_only

# Eager load relationships
result = await db.execute(
    select(Student).options(joinedload(Student.courses))
)

# Load only specific columns
result = await db.execute(
    select(Item).options(load_only(Item.name, Item.price))
)
```

### Securing sensitive data in SQL databases

- **Fernet symmetric encryption** for encrypting fields at rest

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
f = Fernet(key)

# Encrypt before storing
encrypted = f.encrypt(sensitive_data.encode())

# Decrypt when reading
decrypted = f.decrypt(encrypted).decode()
```

### Handling transactions and concurrency

- **Atomic updates** with conditions to prevent race conditions: use `and_()` in WHERE clauses
- SQL **isolation levels**: control how concurrent transactions see each other's changes
- `asyncio.gather` to test concurrent behavior

```python
from sqlalchemy import and_, update

# Atomic conditional update
stmt = (
    update(Item)
    .where(and_(Item.id == item_id, Item.version == expected_version))
    .values(quantity=new_quantity, version=expected_version + 1)
)
result = await db.execute(stmt)
if result.rowcount == 0:
    raise HTTPException(status_code=409, detail="Concurrent modification detected")
await db.commit()
```

---

## Chapter 7: Integrating FastAPI with NoSQL Databases

### Setting up MongoDB with FastAPI

- **motor** (`AsyncIOMotorClient`) for async MongoDB access
- Register `ObjectId` serializer for Pydantic compatibility

```python
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ENCODERS_BY_TYPE
from bson import ObjectId

ENCODERS_BY_TYPE[ObjectId] = str

client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client.mydb
collection = database.get_collection("items")
```

### CRUD operations in MongoDB

- `insert_one()`, `find_one()`, `find()`, `update_one()`, `delete_one()` — all `await`-able with motor
- Convert `ObjectId` to string for API responses

### Handling relationships in NoSQL databases

- **Embedding** (nested documents): denormalized, fast reads, good when data is always accessed together
- **Referencing** (storing IDs): normalized, avoids duplication, requires additional queries
- Choose based on access patterns and data size

### Working with indexes in MongoDB

- `create_index()` for single-field, compound, and text indexes
- Text indexes enable `$text` / `$search` queries
- Use `explain()` to analyze query performance

```python
# Single field index
await collection.create_index("email", unique=True)

# Text index for search
await collection.create_index([("title", "text"), ("description", "text")])

# Query using text search
results = await collection.find({"$text": {"$search": "python fastapi"}}).to_list(100)
```

### Exposing sensitive data from NoSQL databases

- **Data masking** techniques using MongoDB aggregation:
  - `$redact` to conditionally prune document fields
  - `$unset` to remove specific fields from output
  - `$map` / `$mergeObjects` to transform nested arrays
- **MongoDB Views**: stored aggregation pipelines that present masked/filtered data

### Integrating FastAPI with Elasticsearch

- **`AsyncElasticsearch`** client for async search operations
- DSL queries: `match`, `multi_match`, `bool` with `must`/`should`/`filter`
- Aggregations for analytics (e.g., `terms`, `avg`, `date_histogram`)

```python
from elasticsearch import AsyncElasticsearch

es = AsyncElasticsearch("http://localhost:9200")

@app.get("/search")
async def search(q: str):
    result = await es.search(
        index="products",
        body={"query": {"multi_match": {"query": q, "fields": ["name", "description"]}}}
    )
    return result["hits"]["hits"]
```

### Using Redis for caching in FastAPI

- **aioredis** for async Redis access
- Cache frequently accessed data with TTL to reduce DB load

```python
import aioredis
import json

redis = aioredis.from_url("redis://localhost")

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # Check cache first
    cached = await redis.get(f"item:{item_id}")
    if cached:
        return json.loads(cached)

    # Cache miss — fetch from DB
    item = await fetch_from_db(item_id)
    await redis.set(f"item:{item_id}", json.dumps(item), ex=3600)  # TTL: 1 hour
    return item
```

---

## Chapter 8: Advanced Features and Best Practices

> ⚡ **Extra detail section** — per user request

### Implementing dependency injection

- FastAPI DI via `Depends()` — functions, generators, or callable classes
- **Nested dependencies**: dependencies can themselves have dependencies, forming a chain
- **`Annotated` type aliases** for reusable dependency declarations (cleaner than repeating `Depends()`)
- `Query(...)`, `Path(...)` descriptors add validation + OpenAPI metadata to parameters

```python
from typing import Annotated
from fastapi import Depends, Query

# Sub-dependency
def get_settings():
    return Settings()

def get_db(settings: Annotated[Settings, Depends(get_settings)]):
    engine = create_engine(settings.database_url)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

DB = Annotated[Session, Depends(get_db)]

@app.get("/items")
def list_items(db: DB, skip: int = Query(0, ge=0), limit: int = Query(10, le=100)):
    return db.query(Item).offset(skip).limit(limit).all()
```

- **Testing with dependency overrides**: `app.dependency_overrides[original_dep] = mock_dep` — swap any dependency for tests without changing production code

### Creating custom middleware

- **`BaseHTTPMiddleware`**: simple pattern — override `dispatch(self, request, call_next)`, return response
- Use for cross-cutting concerns: logging, timing, header injection, client info

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class ClientInfoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host
        user_agent = request.headers.get("user-agent", "unknown")
        logger.info(f"Request from {client_host} using {user_agent}")
        response = await call_next(request)
        response.headers["X-Client-Host"] = client_host
        return response

app.add_middleware(ClientInfoMiddleware)
```

### Internationalization and localization

- **`babel`** library for locale negotiation
- Parse `Accept-Language` header → `negotiate_locale` to find best match from supported locales
- Return localized responses based on resolved locale

```python
from babel import Locale, negotiate_locale

SUPPORTED_LOCALES = ["en_US", "fr_FR", "de_DE"]

def resolve_accept_language(
    accept_language: str = Header("en-US"),
) -> str:
    requested = [accept_language.replace("-", "_")]
    locale = negotiate_locale(requested, SUPPORTED_LOCALES)
    return locale or "en_US"

@app.get("/greeting")
def greeting(locale: str = Depends(resolve_accept_language)):
    greetings = {"en_US": "Hello!", "fr_FR": "Bonjour!", "de_DE": "Hallo!"}
    return {"message": greetings.get(locale, "Hello!")}
```

### Optimizing application performance

- **pyinstrument** profiler for identifying bottlenecks in async FastAPI code
- Wrap as middleware to profile every request and output HTML reports

```python
from pyinstrument import Profiler
from starlette.middleware.base import BaseHTTPMiddleware

class ProfileEndpointsMiddleWare(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        profiler = Profiler(interval=0.001, async_mode="enabled")
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        profiler.write_html("profiler_output.html")
        return response
```

- **Key metrics to watch**: response time per endpoint, DB query count/duration, memory usage

### Implementing rate limiting

- **slowapi** — built on top of `limits`, integrates directly with FastAPI
- `Limiter(key_func=get_remote_address)` — rate limit per client IP
- Per-endpoint: `@limiter.limit("2/minute")`
- Global default: `default_limits=["5/minute"]` + `SlowAPIMiddleware`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Per-endpoint
@app.get("/limited")
@limiter.limit("2/minute")
async def limited_endpoint(request: Request):
    return {"message": "This endpoint is rate limited"}

# Global (alternative)
limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
app.add_middleware(SlowAPIMiddleware)
```

### Implementing background tasks

- **`BackgroundTasks`**: lightweight, built-in — tasks run after the response is sent
- Inject via parameter: `background_tasks: BackgroundTasks`
- Add tasks: `background_tasks.add_task(function, *args, **kwargs)`
- **When to use**: logging, sending emails, lightweight data processing
- **When NOT to use**: heavy/long-running work → use **Celery** with a message broker instead

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")

def send_notification(email: str, message: str):
    # Simulate email sending
    ...

@app.post("/orders")
async def create_order(order: Order, background_tasks: BackgroundTasks):
    # Process order synchronously
    result = process_order(order)
    # Queue background work
    background_tasks.add_task(write_log, f"Order {result.id} created")
    background_tasks.add_task(send_notification, order.email, "Order confirmed!")
    return result
```

- **Important concurrency note**: `BackgroundTasks` run in the same event loop. CPU-heavy tasks will block async endpoints. For heavy work, use Celery with Redis/RabbitMQ as a broker.

---

## Chapter 9: Working with WebSocket

### Setting up WebSockets in FastAPI

- `@app.websocket("/ws")` decorator for WebSocket endpoints
- Must `await websocket.accept()` before sending/receiving

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Connected!")
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### Sending and receiving messages over WebSockets

- `send_text()` / `receive_text()` for string data
- `send_json()` / `receive_json()` for structured data
- `send_bytes()` / `receive_bytes()` for binary data

### Handling WebSocket connections and disconnections

- **`ConnectionManager`** pattern: track active connections, handle connect/disconnect/broadcast

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
```

### Handling WebSocket errors and exceptions

- Catch `WebSocketDisconnect` to handle client disconnections gracefully

```python
from fastapi import WebSocketDisconnect

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{client_id} left the chat")
```

### Implementing chat functionality with WebSockets

- Combine `ConnectionManager` + Jinja2 HTML template with JavaScript `WebSocket` API
- Server broadcasts messages to all connected clients
- Client-side: `new WebSocket("ws://localhost:8000/ws/username")` + `onmessage` handler

### Optimizing WebSocket performance

- Set **connection limits** to prevent resource exhaustion
- Implement **heartbeat/ping-pong** to detect stale connections
- Use `asyncio.wait_for()` with timeouts on receive operations

### Securing WebSocket connections with OAuth2

- WebSockets don't support HTTP headers in the browser API — pass token as a **query parameter**
- Validate token during the `connect` phase before accepting

```python
@app.websocket("/ws")
async def secured_ws(websocket: WebSocket, token: str = Query(...)):
    try:
        user = verify_token(token)
    except Exception:
        await websocket.close(code=1008)  # Policy Violation
        return
    await websocket.accept()
    ...
```

---

## Chapter 10: Integrating FastAPI with other Python Libraries

### Integrating FastAPI with gRPC

- Define service in **`.proto`** file (proto3 syntax)
- Generate Python stubs: `python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. service.proto`
- gRPC server: `grpc.aio.server()` with servicer implementation
- FastAPI as a **REST-to-gRPC gateway**:

```python
import grpc
from generated_pb2_grpc import GrpcServerStub
from generated_pb2 import Message

grpc_channel = grpc.aio.insecure_channel("localhost:50051")

@app.get("/grpc")
async def call_grpc(message: str):
    async with grpc_channel as channel:
        stub = GrpcServerStub(channel)
        response = await stub.GetServerResponse(Message(message=message))
    return {"server_message": response.message, "received": response.received}
```

### Connecting FastAPI with GraphQL

- **strawberry-graphql** with FastAPI integration
- Define types with `@strawberry.type`, queries with `@strawberry.field`
- Mount with `GraphQLRouter`

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class User:
    name: str
    age: int
    country: str

@strawberry.type
class Query:
    @strawberry.field
    def users(self, country: str | None = None) -> list[User]:
        if country:
            return [u for u in users_db if u.country == country]
        return users_db

schema = strawberry.Schema(Query)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

- Access GraphiQL IDE at `/graphql` for interactive queries

### Using ML models with Joblib

- Load serialized models with `joblib.load()` during app `lifespan`
- **`hf_hub_download()`** from `huggingface_hub` to pull model files from HuggingFace
- **`pydantic.create_model()`** to dynamically generate request models from feature lists

```python
import joblib
from huggingface_hub import hf_hub_download
from pydantic import create_model
from contextlib import asynccontextmanager

ml_model = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = hf_hub_download(repo_id=REPO_ID, filename=FILENAME)
    ml_model["model"] = joblib.load(model_path)
    yield
    ml_model.clear()

# Dynamic Pydantic model from feature list
Symptoms = create_model(
    "Symptoms",
    **{symptom: (bool, False) for symptom in symptoms_list[:10]}
)

@app.post("/predict")
async def predict(symptoms: Symptoms):
    features = [int(v) for v in symptoms.model_dump().values()]
    prediction = ml_model["model"].predict([features])
    return {"prediction": prediction[0]}
```

### Integrating FastAPI with Cohere

- **Cohere `AsyncClient`** for async LLM API calls
- `client.chat(model="command-r-plus", chat_history=[...], message=...)` for conversational AI
- `ChatMessage(role=..., message=...)` for maintaining chat history

```python
from cohere import AsyncClient, ChatMessage

co = AsyncClient(api_key=os.getenv("COHERE_API_KEY"))

@app.post("/chat")
async def chat(message: str):
    response = await co.chat(
        model="command-r-plus",
        chat_history=[ChatMessage(role="USER", message="Hi"), ChatMessage(role="CHATBOT", message="Hello!")],
        message=message,
    )
    return {"response": response.text}
```

### Integrating FastAPI with LangChain

- **RAG (Retrieval-Augmented Generation)** pipeline:
  1. Load documents with `DirectoryLoader`
  2. Split with `CharacterTextSplitter`
  3. Embed + store in vector DB (`Chroma` + `CohereEmbeddings`)
  4. Query: similarity search → inject context into prompt → LLM generates answer
- Chain composition with pipe operator: `template | model | StrOutputParser()`

```python
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Setup at startup
loader = DirectoryLoader("./documents")
splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(loader.load())
db = Chroma.from_documents(docs, CohereEmbeddings())

model = ChatCohere()
template = ChatPromptTemplate.from_template(
    "Answer based on context:\n{context}\n\nQuestion: {question}"
)
chain = template | model | StrOutputParser()

def get_context(question: str, db):
    docs = db.similarity_search(question, k=3)
    return "\n".join(doc.page_content for doc in docs)

@app.post("/ask")
async def ask(question: str):
    context = get_context(question, db)
    response = await chain.ainvoke({"question": question, "context": context})
    return {"answer": response}
```

---

## Chapter 11: Middleware and Webhooks

### Creating custom ASGI middleware

- Lower-level than `BaseHTTPMiddleware` — implements the raw ASGI interface
- Class with `__init__(self, app)` and `async __call__(self, scope, receive, send)`
- `scope["type"]` is `"http"`, `"websocket"`, or `"lifespan"`

```python
from starlette.types import ASGIApp, Scope, Receive, Send

class CustomASGIMiddleware:
    def __init__(self, app: ASGIApp, some_param: str = "default"):
        self.app = app
        self.some_param = some_param

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            # Pre-processing
            logger.info(f"Request scope: {scope}")
        await self.app(scope, receive, send)
        # Note: post-processing requires wrapping `send`

app.add_middleware(CustomASGIMiddleware, some_param="custom_value")
```

- Also supports a **function decorator** pattern for simpler cases

### Developing middleware for request modification

- Example: `HashBodyContentMiddleware` — reads request body, computes SHA1 hash, adds to headers
- Must reconstruct the `receive` callable since the body stream is consumed once

```python
import hashlib

class HashBodyContentMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            body = await receive()
            body_bytes = body.get("body", b"")
            body_hash = hashlib.sha1(body_bytes).hexdigest()
            # Inject hash into headers
            headers = dict(scope.get("headers", []))
            scope["headers"] = list(scope.get("headers", [])) + [
                (b"x-body-hash", body_hash.encode())
            ]
            # Re-wrap receive so downstream can read the body
            async def new_receive():
                return body
            await self.app(scope, new_receive, send)
        else:
            await self.app(scope, receive, send)
```

### Developing middleware for response modification

- Wrap the `send` callable to intercept and modify response headers/body
- `MutableHeaders` from Starlette for clean header manipulation

```python
from starlette.datastructures import MutableHeaders

class ExtraHeadersResponseMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def modified_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.append("X-Custom-Header", "my-value")
            await send(message)
        await self.app(scope, receive, modified_send)
```

### Handling CORS with middleware

- `CORSMiddleware` from Starlette — essential for frontend-backend separation

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- **`allow_origins`**: list of permitted origins (use specific origins in production, not `["*"]`)
- **`allow_methods`**: HTTP methods to allow
- **`allow_headers`**: headers the client can send

### Restricting incoming requests from hosts

- **`TrustedHostMiddleware`**: reject requests not matching allowed `Host` headers

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```

### Implementing webhooks

- **Pattern**: register webhook URLs at startup, fire events via middleware on every request
- `Event(BaseModel)` with host, path, timestamp, and body
- `httpx.AsyncClient` to POST events; `asyncio.create_task()` for non-blocking dispatch
- Document webhooks with `@app.webhooks.post("event-name")` for OpenAPI schema

```python
from pydantic import BaseModel
from datetime import datetime
from asyncio import create_task
import httpx

class Event(BaseModel):
    host: str
    path: str
    time: str
    body: str

webhook_urls: list[str] = []

async def send_event_to_url(url: str, event: Event):
    async with httpx.AsyncClient() as client:
        await client.post(url, json=event.model_dump())

class WebhookSenderMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            body_msg = await receive()
            request = Request(scope=scope)
            event = Event(
                host=request.client.host,
                path=str(request.url.path),
                time=datetime.now().isoformat(),
                body=body_msg.get("body", b"").decode()
            )
            for url in webhook_urls:
                create_task(send_event_to_url(url, event))
            async def new_receive():
                return body_msg
            await self.app(scope, new_receive, send)
        else:
            await self.app(scope, receive, send)

# Register webhook URLs via lifespan or endpoint
@app.post("/webhooks/register")
async def register_webhook(url: str):
    webhook_urls.append(url)
    return {"registered": url}

# Document in OpenAPI
@app.webhooks.post("new-request")
async def new_request_webhook(event: Event):
    """Fired on every incoming HTTP request."""
    ...
```

---

## Chapter 12: Deploying and Managing FastAPI Applications

### Running the server with the FastAPI CLI

- **`fastapi dev app/main.py`**: development mode with auto-reload
- **`fastapi run app/main.py --port 80`**: production mode, no reload
- Equivalent to `uvicorn app.main:app` with appropriate flags

### Enabling HTTPS on FastAPI applications

- **`mkcert`** for generating locally-trusted SSL certificates (development)
- `HTTPSRedirectMiddleware` to force HTTPS

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

# Run with SSL:
# uvicorn app.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Running FastAPI applications in Docker containers

```dockerfile
FROM python:3.10
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt
COPY ./app /code/app
CMD ["fastapi", "run", "app/main.py", "--port", "80"]
```

```bash
# Build
docker build -f Dockerfile.dev -t myapp .

# Run
docker run -p 8000:80 myapp
```

### Running the server across multiple workers

- **Gunicorn** as process manager with **Uvicorn workers** for production
- Heuristic for worker count: `(2 × CPU cores) + 1`

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

- Each worker is an independent process with its own event loop — true parallelism for multi-core utilization
- Combine with a reverse proxy (Nginx) for static files, SSL termination, and load balancing in production

### Deploying your FastAPI application on the cloud

- Example: **Railway** deployment
- Create a `Procfile`: `web: fastapi run app/main.py --port $PORT`
- Connect GitHub repo → Railway auto-builds and deploys on push
- Environment variables configured via Railway dashboard

### Shipping FastAPI applications with Hatch

- **Hatch**: modern Python project manager and build tool
- `hatch new "Project Name"` — scaffold with `pyproject.toml`, src layout, tests
- `hatch shell` — activate isolated virtual environment
- `hatch build -t sdist ../dist` — build source distribution (`.tar.gz`)
- Configure metadata, dependencies, and entry points in `pyproject.toml`

```bash
# Create new project
hatch new "FCA Server"

# Enter virtual environment
cd fca-server
hatch shell

# Install dependencies
pip install fastapi uvicorn

# Build distribution
hatch build -t sdist ../dist
```

---

## Notable Libraries Reference

| Library | Purpose | Install |
|---|---|---|
| `fastapi[all]` | Framework + all extras | `pip install fastapi[all]` |
| `uvicorn` | ASGI server | Included in `fastapi[all]` |
| `pydantic` | Data validation | Included in `fastapi[all]` |
| `sqlalchemy` | SQL ORM (sync + async) | `pip install sqlalchemy` |
| `aiosqlite` | Async SQLite driver | `pip install aiosqlite` |
| `asyncpg` | Async PostgreSQL driver | `pip install asyncpg` |
| `alembic` | DB migrations | `pip install alembic` |
| `pymongo` | MongoDB sync driver | `pip install pymongo` |
| `motor` | MongoDB async driver | `pip install motor` |
| `aioredis` | Async Redis client | `pip install aioredis` |
| `elasticsearch[async]` | Async Elasticsearch | `pip install elasticsearch[async]` |
| `passlib[bcrypt]` | Password hashing | `pip install passlib[bcrypt]` |
| `python-jose[cryptography]` | JWT tokens | `pip install python-jose[cryptography]` |
| `pyotp` | TOTP/MFA codes | `pip install pyotp` |
| `httpx` | Async HTTP client | `pip install httpx` |
| `pytest` | Testing framework | `pip install pytest` |
| `pytest-asyncio` | Async test support | `pip install pytest-asyncio` |
| `pytest-cov` | Coverage reporting | `pip install pytest-cov` |
| `locust` | Load testing | `pip install locust` |
| `slowapi` | Rate limiting | `pip install slowapi` |
| `pyinstrument` | Profiling | `pip install pyinstrument` |
| `babel` | i18n/l10n | `pip install babel` |
| `strawberry-graphql[fastapi]` | GraphQL | `pip install strawberry-graphql[fastapi]` |
| `grpcio` + `grpcio-tools` | gRPC | `pip install grpcio grpcio-tools` |
| `joblib` | Model serialization | `pip install joblib` |
| `huggingface_hub` | HF model download | `pip install huggingface_hub` |
| `cohere` | Cohere LLM API | `pip install cohere` |
| `langchain` | LLM orchestration | `pip install langchain langchain-cohere langchain-community` |
| `cryptography` | Fernet encryption | `pip install cryptography` |
| `gunicorn` | Process manager | `pip install gunicorn` |
| `hatch` | Build/packaging | `pip install hatch` |