# KCDS College ERP System

Complete college management portal built with HTML, CSS, Python Flask and MongoDB for admin, faculty and student operations.

## Features

- Jigel responsive ERP dashboard UI with fixed sidebar.
- Admin module for student registration, attendance and fee due tracking.
- Faculty module for faculty records, departments, designations and subjects.
- Academic module for courses and faculty allotments.
- Communication module for notices and announcements.
- Flask REST API with validation.
- MongoDB persistence using `MONGO_URI`.
- In-memory fallback when MongoDB is not configured.
- Render deployment configuration and GitHub Actions CI.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Environment Variables

- `MONGO_URI`: MongoDB Atlas or local MongoDB connection string.
- `MONGO_DB_NAME`: database name, default `college_erp_system`.
- `PORT`: server port, provided automatically by Render.

## API Endpoints

- `GET /api/health`
- `GET /api/stats`
- `GET /api/students`
- `POST /api/students`
- `PATCH /api/students/<id>/attendance`
- `GET /api/faculty`
- `POST /api/faculty`
- `GET /api/courses`
- `GET /api/notices`
- `POST /api/notices`

## Deploy on Render

Use `render.yaml`, connect this GitHub repository, and set `MONGO_URI` in Render environment variables.

## Tests

```bash
pytest -q
```
