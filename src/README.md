# Mergington High School Activities API

FastAPI application for activity registration and school announcements.

## Features

- View and filter extracurricular activities
- Teacher authentication for student registration and unregistration
- Database-driven announcements with optional start date and required expiration date
- Signed-in-only announcement management (create/update/delete)

## Getting Started

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   uvicorn src.app:app --reload
   ```

3. Open your browser:
   - App: http://localhost:8000/
   - API docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Activities

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | List activities (supports optional day/time filtering) |
| POST | `/activities/{activity_name}/signup?email=...&teacher_username=...` | Register a student (teacher auth required) |
| POST | `/activities/{activity_name}/unregister?email=...&teacher_username=...` | Unregister a student (teacher auth required) |

### Authentication

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/auth/login?username=...&password=...` | Sign in teacher/admin user |
| GET | `/auth/check-session?username=...` | Validate user session by username |

### Announcements

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/announcements` | List currently active announcements for public display |
| GET | `/announcements/manage?teacher_username=...` | List all announcements for management UI (auth required) |
| POST | `/announcements?teacher_username=...` | Create announcement (auth required) |
| PUT | `/announcements/{announcement_id}?teacher_username=...` | Update announcement (auth required) |
| DELETE | `/announcements/{announcement_id}?teacher_username=...` | Delete announcement (auth required) |

## Data Storage

Data is stored in MongoDB (`mergington_high` database) with these collections:

- `activities`
- `teachers`
- `announcements`

Database initialization (`src/backend/database.py`) seeds sample activities, teacher accounts, and one sample announcement when collections are empty.
