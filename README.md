# Content Management Application

A RESTful Content Management Application built with **FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT authentication, Redis, and Celery**. The application provides user authentication, role-based access, blog and category management, comments, ratings, email verification, and administrative operations.

This README explains the project, architecture, installation, environment configuration, database migrations, API endpoints, Swagger testing, background workers, troubleshooting, and development workflow.



## 1. Project Overview

The Content Management Application is a backend platform for publishing and managing blog content.

It allows users to register, verify their email addresses, authenticate securely, view blogs, interact with blog posts through comments and ratings, and manage their profiles. Administrators can perform authorized management operations.

The application follows a modular structure to separate API routes, business logic, database operations, authentication, background tasks, and error handling.

### Main Objectives

- Provide secure user registration and authentication.
- Verify user email addresses.
- Support JWT access and refresh tokens.
- Implement role-based access control.
- Manage blogs and categories.
- Support comments and ratings.
- Provide administrative user-management APIs.
- Process email tasks using Celery and Redis.
- Store application data in PostgreSQL.
- Manage database schema changes using Alembic.
- Provide centralized exception handling, logging, and request tracking.
- Support automated testing and Docker-based Redis setup.

## 2. Features

### Authentication and User Management

- User registration.
- Email verification.
- Login and JWT-based authentication.
- Access-token and refresh-token workflows.
- Logout and refresh-token/session management.
- User profile creation and updates.
- Current-user information.
- Administrative user listing and detail retrieval.
- User activation and deactivation endpoints.

### Authorization and Security

- Role-based access control for protected operations.
- Authentication dependencies for identifying the current user.
- Authorization checks for restricted endpoints.
- Password hashing rather than storing plain-text passwords.
- Environment-based configuration for secrets and credentials.
- Input validation using Pydantic.
- Standardized error responses.
- Request tracking and application logging.

Actual permissions are determined by the application's implemented authorization rules.

### Blog Management

- Create blogs.
- Retrieve blog lists.
- Retrieve individual blogs.
- Update blog content.
- Delete blogs.
- Publish blogs.
- Search and filter blog listings where supported.
- Paginate list responses.

### Category Management

- Retrieve categories.
- Retrieve an individual category.
- Create categories through the administrative API.
- Update categories.
- Delete categories.

### Comments and Ratings

- Add comments to blogs.
- Retrieve blog comments.
- Update comments.
- Delete comments.
- Submit ratings.
- Retrieve rating summaries.
- Retrieve, update, or delete the current user's rating.

### Background Processing

- Queue email-verification tasks using Celery.
- Use Redis as the Celery message broker and, where configured, result backend.
- Process queued tasks through a separate worker instead of making the API perform all background work synchronously.

### Reliability and Documentation

- PostgreSQL database integration.
- SQLAlchemy ORM.
- Alembic database migrations.
- Centralized exception handling.
- Health-check endpoints.
- Automated tests.
- Docker Compose configuration for Redis.
- Interactive Swagger documentation.
- Reproducible development instructions.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| Pydantic | Request and response validation |
| PostgreSQL | Relational database |
| SQLAlchemy | ORM and database access |
| Alembic | Database schema migrations |
| JWT | Token-based authentication |
| Redis | Broker and session/token support, according to configuration |
| Celery | Background task processing |
| Docker Compose | Redis container management |
| Pytest | Automated testing |
| Swagger UI | Interactive API testing |
| Git | Version control |

The exact installed package versions are determined by the project's environment and dependency configuration.

## 4. Prerequisites

Before running the application, make sure the following are available:

- Python compatible with the project's installed dependencies.
- PostgreSQL.
- A PostgreSQL database named `content_management_db`, or the database name configured in `.env`.
- Docker Desktop, if Redis is being run through Docker Compose.
- Git.
- The project source code.
- Valid environment variables and credentials for the services being used.

Email verification also requires a correctly configured email delivery method.

## 5. Project Location

The current project root is:

text
D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application


Open Windows PowerShell and navigate to the project directory:

powershell
cd "D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application"


Activate the existing virtual environment:

powershell
.\.venv\Scripts\Activate.ps1


After activation, PowerShell should display `(.venv)` at the beginning of the prompt.

Run the remaining Python commands from the project root with the virtual environment activated.

## 6. Installation and Dependencies

### Step 1: Activate the virtual environment

powershell
.\.venv\Scripts\Activate.ps1


### Step 2: Install the dependencies

powershell
python -m pip install -r requirements.txt


**Dependency note:** Ensure `requirements.txt` contains all dependencies required by the application, not only Celery, Redis, and `itsdangerous`. The actual requirements must match the imports and features implemented in the source code.

For a reproducible setup, maintain and test a complete dependency list before distributing the project to another machine.

### Step 3: Verify the important packages

powershell
python -m pip show fastapi
python -m pip show uvicorn
python -m pip show sqlalchemy
python -m pip show alembic
python -m pip show pydantic-settings
python -m pip show celery
python -m pip show redis


If a required package is missing, install it through the project's dependency-management process and update `requirements.txt` accordingly.

## 7. Environment Configuration

The application uses environment variables to configure database connectivity, authentication, Redis, and email delivery.

### Step 1: Create the environment file

If `.env` does not already exist, create it from the example file:

powershell
Copy-Item .env.example .env


If `.env` already exists, do not overwrite it. Update its values instead.

### Step 2: Configure the environment variables

The following are the main configuration categories. Use the exact variable names expected by the project's settings class and `.env.example`.

| Configuration | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret used for signing JWTs, if this is the configured name |
| `JWT_ALGORITHM` | JWT signing algorithm |
| `REDIS_URL` | Redis connection URL |
| Email/SMTP settings | Email verification and other email delivery |

Example formats:

dotenv
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/content_management_db

JWT_SECRET_KEY=REPLACE_WITH_A_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256

REDIS_URL=redis://localhost:6379/0


These examples illustrate common formats. Keep the actual variable names and URL format consistent with the application's configuration and database driver.

Configure the required email settings using the names present in `.env.example`. Do not copy real credentials into public documentation.

### Security requirements

- Never commit `.env` or real secrets to Git.
- Keep `.env.example` limited to placeholders and non-sensitive defaults.
- Use a strong, unpredictable JWT secret.
- Do not expose database passwords, email passwords, refresh tokens, or secret keys in logs.
- Use HTTPS and suitable production configuration when deploying publicly.

## 8. PostgreSQL and Database Migrations

PostgreSQL stores the application's persistent data. SQLAlchemy provides database access, and Alembic manages schema changes.

### Step 1: Verify the database

Make sure PostgreSQL is running and that the configured database exists.

The current database name used by this project is:

text
content_management_db


The database URL in `.env` must point to the correct PostgreSQL instance and database.

### Step 2: Apply database migrations

From the project root, run:

powershell
python -m alembic upgrade head


This applies all migrations required to bring the database to the latest migration revision.

### Step 3: Check the current migration revision

powershell
python -m alembic current


### Step 4: Review available migration history

powershell
python -m alembic history


### Migration workflow

text
SQLAlchemy Model Changes
          |
          v
Alembic Migration
          |
          v
Review Migration File
          |
          v
Apply Migration
          |
          v
PostgreSQL Schema Updated


When database models change, generate a migration using the project's established Alembic workflow, review the generated file, and apply it before testing the updated functionality.

Do not delete migration files or modify an already shared migration casually. Never use production data as a substitute for a tested migration process.

## 9. Running the FastAPI Application

Start the API from the project root:

powershell
python -m uvicorn app.main:app --reload


The development server should start if the dependencies, environment variables, database configuration, and application imports are correct.

### Application URLs

| Resource | URL |
|---|---|
| Base URL | `http://127.0.0.1:8000` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |

Use Swagger UI to inspect endpoint schemas, required fields, response models, authorization requirements, and available request parameters.

The interactive documentation is the source of truth for the request and response schemas exposed by the running application.

## 10. Redis Setup

Redis supports configured background-processing and token/session-management functionality.

This project uses a Docker Compose Redis service. Start it from the project root.

### Step 1: Start Redis

powershell
docker compose up -d redis


### Step 2: Check the running container

powershell
docker ps


The configured Redis container name is:

text
content_app_redis


### Step 3: Test the Redis connection

powershell
docker exec content_app_redis redis-cli ping


Expected response:

text
PONG


If Docker reports that the container does not exist, inspect the Compose configuration and running containers. Use the service name from `docker-compose.yml`; do not assume a container named `reddis` or `redis` exists.

### Redis connection check from Python

powershell
python -c "from app.core.config import settings; import redis; client = redis.Redis.from_url(settings.REDIS_URL); print(client.ping())"


Expected successful result:

text
True


This command assumes that `settings.REDIS_URL` is the configured setting used by the project.

## 11. Celery Background Worker

Celery processes tasks outside the normal API request-response cycle. Redis is used as the broker when configured in the Celery application.

Email verification is a required background-processing workflow for this project.

Other possible background tasks include welcome emails, password-reset emails, comment notifications, and administrative notifications, where implemented.

### How background processing works

text
Client Sends Registration Request
                |
                v
        FastAPI Creates User
                |
                v
       Email Task Is Queued
                |
                v
       API Returns a Response
                |
                v
       Celery Worker Processes Task
                |
                v
          Email Is Sent


The API and Celery worker are separate processes. Starting the API alone does not guarantee that queued email tasks will be processed.

### Step 1: Keep Redis running

Use the Redis instructions in Section 10.

### Step 2: Open a separate PowerShell terminal

Navigate to the project root and activate the virtual environment in that terminal:

powershell
cd "D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application"
.\.venv\Scripts\Activate.ps1


### Step 3: Start the Celery worker

powershell
python -m celery -A app.core.celery_app worker --loglevel=info --pool=solo


The `--pool=solo` option is appropriate for a straightforward local Windows development setup.

Keep the worker terminal running while testing background tasks.

### Step 4: Test email verification

1. Start Redis.
2. Start the FastAPI application.
3. Start the Celery worker.
4. Register a test user through Swagger.
5. Inspect the worker logs for task execution.
6. Check the configured email inbox for the verification message.
7. Follow the verification link or use the verification endpoint as documented in Swagger.

If an email is not delivered, check the application logs, worker logs, Redis connectivity, email configuration, and the response returned by the registration endpoint.

## 12. API Reference

All application endpoints below use the `/api/v1` prefix unless otherwise indicated.

Use `http://127.0.0.1:8000/docs` for the live API documentation.

The HTTP methods and paths listed below describe the current API surface. Request schemas, query parameters, status codes, and authorization requirements must be checked against the running Swagger documentation.

### 12.1 Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/users/register` | Register a user |
| GET | `/api/v1/users/verify-email` | Verify a user's email |
| POST | `/api/v1/users/login` | Authenticate a user |
| POST | `/api/v1/users/refresh` | Refresh authentication tokens |
| POST | `/api/v1/users/logout` | Log out and process the configured token/session invalidation |

### 12.2 User Profile and Current User

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/users/admin/check` | Check the current user's administrative access |
| GET | `/api/v1/users/me/profile` | Retrieve the current user's profile |
| PUT | `/api/v1/users/me/profile` | Update the current user's profile |
| POST | `/api/v1/users/me/profile` | Create a profile, where permitted by the implementation |
| GET | `/api/v1/users/me` | Retrieve the current user's information |
| PUT | `/api/v1/users/me` | Update the current user's information |

### 12.3 Administrative User Management

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/admin/users` | Retrieve the user list |
| GET | `/api/v1/admin/users/{user_id}` | Retrieve a specific user's details |
| PATCH | `/api/v1/admin/users/{user_id}/activate` | Activate a user |
| PATCH | `/api/v1/admin/users/{user_id}/deactivate` | Deactivate a user |

### 12.4 Categories

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/categories` | Retrieve categories |
| GET | `/api/v1/categories/{category_id}` | Retrieve a category |
| POST | `/api/v1/admin/categories` | Create a category |
| PUT | `/api/v1/admin/categories/{category_id}` | Update a category |
| DELETE | `/api/v1/admin/categories/{category_id}` | Delete a category |

### 12.5 Blogs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/blogs/` | Create a blog |
| GET | `/api/v1/blogs/` | Retrieve the blog list |
| GET | `/api/v1/blogs/{blog_id}` | Retrieve a specific blog |
| PATCH | `/api/v1/blogs/{blog_id}` | Update a blog |
| DELETE | `/api/v1/blogs/{blog_id}` | Delete a blog |
| PATCH | `/api/v1/blogs/{blog_id}/publish` | Publish a blog |

Blog-list query parameters exposed in Swagger include:

- `search`: search text, where supported.
- `category_id`: filter by category.
- `is_published`: filter by publication status.
- `skip`: number of records to skip; the documented constraint is non-negative.
- `limit`: maximum number of records to return; the documented constraint is 1–100.

Check the live Swagger schema for defaults, parameter types, and any additional restrictions.

### 12.6 Comments

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/blogs/{blog_id}/comments` | Add a comment |
| GET | `/api/v1/blogs/{blog_id}/comments` | Retrieve comments for a blog |
| PUT | `/api/v1/blogs/{blog_id}/comments/{comment_id}` | Update a comment |
| DELETE | `/api/v1/blogs/{blog_id}/comments/{comment_id}` | Delete a comment |

### 12.7 Ratings

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/blogs/{blog_id}/ratings` | Submit a rating |
| GET | `/api/v1/blogs/{blog_id}/ratings/summary` | Retrieve the rating summary |
| GET | `/api/v1/blogs/{blog_id}/ratings/me` | Retrieve the current user's rating |
| PUT | `/api/v1/blogs/{blog_id}/ratings/me` | Update the current user's rating |
| DELETE | `/api/v1/blogs/{blog_id}/ratings/me` | Delete the current user's rating |

### 12.8 Health Checks

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check application health |
| GET | `/health/redis` | Check Redis connectivity |
| GET | `/health/db` | Check database connectivity |

Health endpoints indicate the status of the components checked by their implementation. A successful API health response does not necessarily prove that the Celery worker or email delivery is working; verify those separately.

## 13. Swagger API Testing Guide

Open:

text
http://127.0.0.1:8000/docs


Swagger provides an interactive interface to send API requests and inspect their responses.

### General Testing Procedure

1. Expand the endpoint you want to test.
2. Read the description and required parameters.
3. Click **Try it out**.
4. Enter the request data using the displayed schema.
5. Click **Execute**.
6. Review the HTTP status code and response body.
7. Record any unexpected result and compare it with the endpoint's intended behavior.

Do not assume a request body for an endpoint if Swagger does not display one.

### Authentication Workflow

1. Register a test user using `POST /api/v1/users/register`.
2. Complete email verification if registration requires it.
3. Log in through `POST /api/v1/users/login`.
4. Inspect the returned token response.
5. Click Swagger's **Authorize** button if the API uses bearer authentication.
6. Enter the token in the format requested by Swagger, commonly `Bearer YOUR_ACCESS_TOKEN`.
7. Test the protected endpoints.
8. Test token refresh and logout using the documented request format.

Do not share real access tokens, refresh tokens, or credentials in screenshots or public reports.

### User Workflow

Using a normal test account:

1. Register and verify the account.
2. Log in.
3. Retrieve the current user's information.
4. Retrieve or update the profile.
5. Retrieve the available categories.
6. Retrieve the available blogs.
7. Open a blog's details.
8. Add a comment if authorized.
9. Submit a rating if authorized.
10. Retrieve the rating summary.
11. Test updating or deleting the current user's own comment or rating, as applicable.

### Administrator Workflow

Use an administrator account that has been provisioned through the project's approved setup process.

1. Log in as the administrator.
2. Authorize Swagger with the administrator's token.
3. Test the administrative access-check endpoint.
4. Retrieve the user list.
5. Retrieve an individual user's details.
6. Test user activation and deactivation using a dedicated test account.
7. Create a category.
8. Retrieve and update the category.
9. Delete a disposable test category when appropriate.
10. Test blog management and publishing according to the configured authorization rules.

Do not promote a user or modify a production account solely to make a test pass. Follow the project's approved administrative-account setup procedure.

## 14. Authorization and Negative Testing

Successful responses are not enough to establish that protected endpoints are secure. Test both allowed and denied requests.

| Test | What to verify |
|---|---|
| Request without a token | Protected endpoints reject unauthenticated access |
| Invalid or malformed token | The API rejects invalid authentication |
| Expired token | The API rejects an expired access token |
| Normal user accessing admin operation | Access is denied when the operation is administrator-only |
| User editing another user's resource | Ownership rules are enforced where applicable |
| Missing required field | Request validation returns an appropriate error |
| Invalid field type | Request validation rejects invalid data |
| Non-existent resource ID | The API returns the configured not-found response |
| Duplicate rating | Behavior matches the implemented duplicate-rating policy |
| Invalid rating value | The API rejects values outside the permitted range |
| Redis unavailable | Redis-dependent features report or handle the failure appropriately |
| Database unavailable | Database-dependent operations fail in a controlled manner |

For each test, record the endpoint, test data, expected result, actual status code, and response body.

The exact status codes and error-body format should be confirmed against the implementation and the API's error-handling conventions.

## 15. Request Validation and Response Handling

FastAPI and Pydantic validate request data according to the schemas defined by the application.

Validation can include required fields, data types, lengths, ranges, and other declared constraints.

The application also has centralized exception-handling infrastructure for application exceptions, request validation errors, HTTP exceptions, and unexpected exceptions.

When testing an error response, check:

- HTTP status code.
- Error response structure.
- Error message.
- Whether sensitive information is omitted.
- Whether the error is logged appropriately.
- Whether a request identifier is available when configured.

Do not expose stack traces, database credentials, JWT secrets, or other internal information in client-facing error responses.

## 16. Logging and Error Handling

The application includes centralized error-handling and logging functionality.

The exception-handling setup is registered by the application's main entry point. It handles the configured application exceptions, validation errors, HTTP exceptions, and unexpected exceptions.

Logging helps diagnose issues in API requests, database access, Redis connectivity, and background tasks.

### Development Troubleshooting Procedure

1. Read the FastAPI terminal output.
2. Check the Celery worker terminal for task failures.
3. Check the Redis container status and connection.
4. Verify PostgreSQL availability and the database URL.
5. Inspect the HTTP response and status code.
6. Review the relevant application logs.
7. Reproduce the problem with a controlled test case.

Avoid logging passwords, raw tokens, email credentials, or other sensitive values.

## 17. Project Structure

The project uses a modular structure. The following is a high-level guide; the exact current files should be confirmed against the repository.

text
Content_Management_Application/
|
|-- alembic/
|   |-- versions/
|   |-- env.py
|   |-- script.py.mako
|
|-- app/
|   |-- main.py
|   |-- core/
|   |   |-- config.py
|   |   |-- celery_app.py
|   |   |-- redis_client.py
|   |   |-- email_verification.py
|   |   |-- exceptions/
|   |   |   |-- handlers.py
|   |
|   |-- db/
|   |-- models/
|   |-- schemas/
|   |-- api/
|   |   |-- v1/
|   |-- services/
|   |-- dependencies/
|   |-- middleware/
|   |-- workers/
|   |-- tasks/
|       |-- email_tasks.py
|
|-- tests/
|-- .env
|-- .env.example
|-- .gitignore
|-- alembic.ini
|-- docker-compose.yml
|-- requirements.txt
|-- README.md


### Responsibilities

| Component | Responsibility |
|---|---|
| `app/main.py` | Creates and configures the FastAPI application |
| `app/core/config.py` | Application settings and environment configuration |
| `app/core/` | Shared application infrastructure |
| `app/db/` | Database connectivity and related utilities |
| `app/models/` | Database models |
| `app/schemas/` | Request and response schemas |
| `app/api/v1/` | Versioned API endpoints |
| `app/services/` | Business logic |
| `app/dependencies/` | Reusable dependencies, including authorization dependencies where implemented |
| `app/middleware/` | Request and response middleware |
| `app/core/exceptions/handlers.py` | Centralized exception handlers |
| `app/core/celery_app.py` | Celery application configuration |
| `app/core/redis_client.py` | Redis connection functionality |
| `app/tasks/` | Background task definitions |
| `alembic/versions/` | Database migration scripts |
| `tests/` | Automated tests |

A directory may be empty, renamed, or organized differently as development continues. The repository itself is the final authority for the current file structure.

## 18. Running Automated Tests

Run the test suite from the project root with the virtual environment activated:

powershell
python -m pytest -v


For a shorter summary:

powershell
python -m pytest -q


For test output that includes print statements:

powershell
python -m pytest -v -s


### Test Coverage Areas

Depending on the implemented test suite, tests should cover:

- Authentication and registration.
- Email-verification behavior.
- Token validation and refresh.
- Protected endpoints and authorization.
- User profile operations.
- Blog and category operations.
- Comment ownership and updates.
- Rating validation and duplicate handling.
- Error responses.
- Database behavior.
- Health checks.

A successful test run means the tests that were executed passed. It does not automatically prove that every possible production scenario has been tested.

When adding or changing functionality, update the relevant tests and run the suite again.

## 19. Docker Compose

The project's Docker Compose configuration provides the Redis service used during local development.

Start Redis:

powershell
docker compose up -d redis


Check the Compose configuration:

powershell
docker compose config --quiet


View running containers:

powershell
docker ps


View Redis logs:

powershell
docker logs content_app_redis


Stop the Redis service when it is no longer required:

powershell
docker compose stop redis


The FastAPI application and Celery worker may still need to be started separately, according to the current Compose configuration.

## 20. Health-Check Verification

After starting the API, open the following URLs in a browser or test them through Swagger:

text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/db
http://127.0.0.1:8000/health/redis

Check the responses and confirm that the reported status matches the actual service availability.

If a check fails:

1. Confirm the API is running.
2. Verify the database URL and PostgreSQL status.
3. Confirm Redis is running.
4. Check application logs.
5. Verify that the required dependencies are installed.

## 21. Common Problems and Solutions

### Problem: `uvicorn` is not available

Activate the virtual environment and install the project's complete dependencies. Then run:

powershell
python -m uvicorn app.main:app --reload


### Problem: `ModuleNotFoundError`

Confirm that the virtual environment is active, the required package is installed, and the command is being executed from the project root.

### Problem: `email_validator` is missing

Check which dependency provides the email-validation functionality used by the application's Pydantic schemas. Add the required dependency to the project requirements and install it in the virtual environment.

### Problem: PostgreSQL connection fails

Verify:

- PostgreSQL is running.
- The database exists.
- The username and password are correct.
- The configured database URL is correct.
- The required database driver is installed.
- The database is reachable from the application environment.

### Problem: Alembic migration fails

Run:

powershell
python -m alembic current
python -m alembic history


Then inspect the migration error, database connection, model metadata, and Alembic configuration before changing migration files.

### Problem: Redis container is not found

Run:

powershell
docker compose ps
docker ps -a


Start the configured service:

powershell
docker compose up -d redis


Use the container name shown by Docker when executing container-specific commands.

### Problem: Celery worker does not process tasks

Verify that Redis is available, the configured broker URL is correct, the worker uses `app.core.celery_app`, and the task has been registered and queued successfully.

Run the worker from the project root:

powershell
python -m celery -A app.core.celery_app worker --loglevel=info --pool=solo


Inspect the worker logs for connection failures or task exceptions.

### Problem: Email verification does not arrive

Verify the email settings, task queue, Celery worker, provider configuration, and spam folder. Check both API and worker logs.

### Problem: Protected API returns `401` or `403`

Check whether the request has a valid token, whether the token has expired, whether Swagger's authorization header is correct, and whether the logged-in user has the required permissions.

A `401` commonly indicates an authentication problem; a `403` commonly indicates an authorization restriction. The actual response depends on the application's implementation.

### Problem: A request returns `404`

Confirm the route, HTTP method, resource ID, and API prefix. Use Swagger to verify the current endpoint path.

## 22. Git Workflow

Use Git to track source-code changes and share reviewed updates.

Check the current branch and working-tree status:

powershell
git status
git branch --show-current


Review the changes:

powershell
git diff


Stage intended files:

powershell
git add README.md


Stage other changed files individually after reviewing them. Avoid staging `.env`, credentials, or unrelated files.

Review staged changes:

powershell
git diff --cached


Commit the changes:

powershell
git commit -m "docs: update project README"


Push the current branch when the repository's remote and branch are configured:

powershell
git push


Before committing, verify that secrets are excluded and that the README accurately reflects the current application.

## 23. Security and Development Notes

- Never store passwords in plain text.
- Never commit `.env` or real credentials.
- Validate incoming request data.
- Protect administrative endpoints with the appropriate authorization checks.
- Enforce ownership rules for resources where required.
- Handle expired, invalid, and revoked tokens according to the implemented authentication flow.
- Avoid returning internal stack traces to API clients.
- Keep dependencies updated and tested.
- Review database migrations before applying them.
- Use a separate test database and disposable test accounts for destructive testing.
- Do not assume that a successful login automatically grants administrative privileges.
- Confirm authorization requirements in the code and Swagger documentation.
- Do not expose debug configuration in a public production deployment.
- Use a production-grade ASGI server configuration, HTTPS, secure secret management, and appropriate monitoring when deploying outside local development.

## 24. Definition of Done / Acceptance Checklist

Use this checklist to review the application before delivery.

### Authentication and Users

- [ ] User registration works.
- [ ] Passwords are hashed securely.
- [ ] Email verification works.
- [ ] Login and token issuance work.
- [ ] Refresh-token behavior works.
- [ ] Logout and configured token/session invalidation work.
- [ ] User profile endpoints work.
- [ ] Administrative user-management endpoints enforce the required permissions.

### Authorization

- [ ] Protected endpoints reject unauthenticated requests.
- [ ] Administrative operations enforce administrator authorization.
- [ ] Ownership restrictions are enforced where required.
- [ ] Invalid and expired tokens are handled appropriately.

### Blogs and Categories

- [ ] Blog creation, retrieval, updating, and deletion work.
- [ ] Blog publishing works.
- [ ] Listing, search, filtering, and pagination behave according to the implementation.
- [ ] Category retrieval works.
- [ ] Administrative category creation, updating, and deletion work.

### Comments and Ratings

- [ ] Comment creation and retrieval work.
- [ ] Comment update and deletion follow the required authorization rules.
- [ ] Rating submission works.
- [ ] Rating values are validated.
- [ ] Duplicate-rating behavior matches the intended policy.
- [ ] Rating summary and current-user rating operations work.

### Background Processing and Infrastructure

- [ ] Redis starts successfully.
- [ ] Redis connectivity can be verified.
- [ ] Celery worker starts successfully.
- [ ] Email-verification tasks are queued and processed.
- [ ] PostgreSQL connectivity works.
- [ ] Alembic migrations apply successfully.
- [ ] Health-check endpoints return appropriate results.

### Reliability and Delivery

- [ ] Validation and exception handling work.
- [ ] Logging supports troubleshooting without exposing secrets.
- [ ] Request tracking works where configured.
- [ ] Automated tests pass.
- [ ] Docker Compose configuration is valid.
- [ ] `.env` and secrets are excluded from Git.
- [ ] `requirements.txt` contains the required dependencies.
- [ ] README setup instructions have been tested.
- [ ] API endpoints and schemas match the running Swagger documentation.

Mark an item complete only after verifying it through a test, code review, or an appropriate runtime check.

## 25. Quick Start Reference

For local development, the main workflow is:

**Terminal 1 — Start Redis**

powershell
cd "D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application"
docker compose up -d redis
docker exec content_app_redis redis-cli ping


**Terminal 2 — Start FastAPI**

powershell
cd "D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application"
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
python -m uvicorn app.main:app --reload


**Terminal 3 — Start Celery**

powershell
cd "D:\Company_projects\Internal_project\Blog_Content_Managment_App\Production_Work\Content_Management_Application"
.\.venv\Scripts\Activate.ps1
python -m celery -A app.core.celery_app worker --loglevel=info --pool=solo


**Swagger UI**

text
http://127.0.0.1:8000/docs


**Run the tests**

powershell
python -m pytest -v


Run the database migration after confirming that the environment variables and PostgreSQL database are configured correctly.


## Final Note

This README documents the project's intended workflows and the API paths listed in the current project reference. The running application's Swagger documentation, configuration, source code, and automated tests remain the authoritative sources for exact request schemas, response formats, permissions, and runtime behavior.
