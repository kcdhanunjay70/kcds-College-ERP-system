import os
from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError


DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "AIML", "DS"]
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]

DEFAULT_STUDENTS = [
    {"rollNo": "KCDS23AIML001", "name": "Akhil Kumar", "department": "AIML", "year": "3rd Year", "phone": "9876543210", "email": "akhil@kcds.edu", "attendance": 92, "feeDue": 0, "status": "Active"},
    {"rollNo": "KCDS23CSE014", "name": "Bhavana Reddy", "department": "CSE", "year": "3rd Year", "phone": "9876543211", "email": "bhavana@kcds.edu", "attendance": 86, "feeDue": 12500, "status": "Active"},
    {"rollNo": "KCDS22ECE044", "name": "Charan Teja", "department": "ECE", "year": "4th Year", "phone": "9876543212", "email": "charan@kcds.edu", "attendance": 74, "feeDue": 8200, "status": "Warning"},
]

DEFAULT_FACULTY = [
    {"facultyId": "FAC-AIML-01", "name": "Dr. Kavitha Rao", "department": "AIML", "designation": "Professor", "phone": "9123456780", "email": "kavitha@kcds.edu", "subjects": ["Machine Learning", "Python Lab"], "status": "Available"},
    {"facultyId": "FAC-CSE-04", "name": "Suresh Varma", "department": "CSE", "designation": "Assistant Professor", "phone": "9123456781", "email": "suresh@kcds.edu", "subjects": ["DBMS", "Web Technologies"], "status": "In Class"},
    {"facultyId": "FAC-ECE-03", "name": "Meena Priya", "department": "ECE", "designation": "Associate Professor", "phone": "9123456782", "email": "meena@kcds.edu", "subjects": ["Digital Electronics"], "status": "Available"},
]

DEFAULT_COURSES = [
    {"code": "AIML301", "title": "Machine Learning", "department": "AIML", "year": "3rd Year", "credits": 4, "faculty": "Dr. Kavitha Rao", "enrolled": 64},
    {"code": "CSE302", "title": "Database Management Systems", "department": "CSE", "year": "3rd Year", "credits": 4, "faculty": "Suresh Varma", "enrolled": 72},
    {"code": "ECE401", "title": "Digital Signal Processing", "department": "ECE", "year": "4th Year", "credits": 3, "faculty": "Meena Priya", "enrolled": 58},
]

DEFAULT_NOTICES = [
    {"title": "Mid Exam Timetable Released", "audience": "Students", "priority": "High", "message": "All departments must check the ERP timetable section before Friday.", "status": "Published"},
    {"title": "Faculty Attendance Review", "audience": "Faculty", "priority": "Medium", "message": "Department coordinators should update attendance records by 5 PM.", "status": "Published"},
]


def utc_now():
    return datetime.now(timezone.utc)


def clean(value, max_length=500):
    return str(value or "").strip()[:max_length]


def digits(value):
    return "".join(char for char in str(value or "") if char.isdigit())


def number(value, minimum, maximum, field_name):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum:g} and {maximum:g}")
    return parsed


def integer(value, minimum, maximum, field_name):
    return int(number(value, minimum, maximum, field_name))


def serialize(document):
    item = dict(document)
    if "_id" in item:
        item["id"] = str(item.pop("_id"))
    for key in ("createdAt", "updatedAt"):
        if isinstance(item.get(key), datetime):
            item[key] = item[key].isoformat()
    return item


class CollegeStore:
    def __init__(self):
        self.client = None
        self.db = None
        self.mode = "memory"
        self.error = ""
        self.memory_students = []
        self.memory_faculty = []
        self.memory_courses = []
        self.memory_notices = []

        mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGO_DB_NAME", "college_erp_system")
        if mongo_uri:
            try:
                self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2500)
                self.client.admin.command("ping")
                self.db = self.client[db_name]
                self.mode = "mongodb"
                self.ensure_seed_data()
                return
            except (PyMongoError, ServerSelectionTimeoutError) as exc:
                self.error = str(exc)
        self.ensure_memory_seed_data()

    @property
    def students(self):
        return self.db["students"] if self.db is not None else None

    @property
    def faculty(self):
        return self.db["faculty"] if self.db is not None else None

    @property
    def courses(self):
        return self.db["courses"] if self.db is not None else None

    @property
    def notices(self):
        return self.db["notices"] if self.db is not None else None

    def ensure_seed_data(self):
        now = utc_now()
        seeds = [
            (self.students, DEFAULT_STUDENTS),
            (self.faculty, DEFAULT_FACULTY),
            (self.courses, DEFAULT_COURSES),
            (self.notices, DEFAULT_NOTICES),
        ]
        for collection, records in seeds:
            if collection.count_documents({}) == 0:
                collection.insert_many([{**record, "createdAt": now, "updatedAt": now} for record in records])

    def ensure_memory_seed_data(self):
        now = utc_now()
        self.memory_students = [{**item, "id": str(uuid4()), "createdAt": now, "updatedAt": now} for item in DEFAULT_STUDENTS]
        self.memory_faculty = [{**item, "id": str(uuid4()), "createdAt": now, "updatedAt": now} for item in DEFAULT_FACULTY]
        self.memory_courses = [{**item, "id": str(uuid4()), "createdAt": now, "updatedAt": now} for item in DEFAULT_COURSES]
        self.memory_notices = [{**item, "id": str(uuid4()), "createdAt": now, "updatedAt": now} for item in DEFAULT_NOTICES]

    def list_students(self):
        if self.mode == "mongodb":
            return [serialize(item) for item in self.students.find({}).sort("rollNo", 1)]
        return [serialize(item) for item in sorted(self.memory_students, key=lambda item: item["rollNo"])]

    def list_faculty(self):
        if self.mode == "mongodb":
            return [serialize(item) for item in self.faculty.find({}).sort("facultyId", 1)]
        return [serialize(item) for item in sorted(self.memory_faculty, key=lambda item: item["facultyId"])]

    def list_courses(self):
        if self.mode == "mongodb":
            return [serialize(item) for item in self.courses.find({}).sort("code", 1)]
        return [serialize(item) for item in sorted(self.memory_courses, key=lambda item: item["code"])]

    def list_notices(self):
        if self.mode == "mongodb":
            return [serialize(item) for item in self.notices.find({}).sort("createdAt", -1)]
        return [serialize(item) for item in sorted(self.memory_notices, key=lambda item: item["createdAt"], reverse=True)]

    def create_student(self, payload):
        now = utc_now()
        document = {
            "rollNo": clean(payload.get("rollNo"), 30).upper(),
            "name": clean(payload.get("name"), 80),
            "department": clean(payload.get("department"), 20),
            "year": clean(payload.get("year"), 20),
            "phone": digits(payload.get("phone"))[:10],
            "email": clean(payload.get("email"), 120),
            "attendance": integer(payload.get("attendance") or 0, 0, 100, "Attendance"),
            "feeDue": integer(payload.get("feeDue") or 0, 0, 500000, "Fee due"),
            "status": clean(payload.get("status"), 30) or "Active",
            "createdAt": now,
            "updatedAt": now,
        }
        validate_student(document)
        if self.mode == "mongodb":
            inserted = self.students.insert_one(document)
            document["_id"] = inserted.inserted_id
        else:
            document["id"] = str(uuid4())
            self.memory_students.append(document)
        return serialize(document)

    def create_faculty(self, payload):
        now = utc_now()
        subjects = [item.strip() for item in clean(payload.get("subjects"), 300).split(",") if item.strip()]
        document = {
            "facultyId": clean(payload.get("facultyId"), 30).upper(),
            "name": clean(payload.get("name"), 80),
            "department": clean(payload.get("department"), 20),
            "designation": clean(payload.get("designation"), 80),
            "phone": digits(payload.get("phone"))[:10],
            "email": clean(payload.get("email"), 120),
            "subjects": subjects,
            "status": clean(payload.get("status"), 30) or "Available",
            "createdAt": now,
            "updatedAt": now,
        }
        validate_faculty(document)
        if self.mode == "mongodb":
            inserted = self.faculty.insert_one(document)
            document["_id"] = inserted.inserted_id
        else:
            document["id"] = str(uuid4())
            self.memory_faculty.append(document)
        return serialize(document)

    def create_notice(self, payload):
        now = utc_now()
        document = {
            "title": clean(payload.get("title"), 120),
            "audience": clean(payload.get("audience"), 40) or "All",
            "priority": clean(payload.get("priority"), 20) or "Medium",
            "message": clean(payload.get("message"), 800),
            "status": "Published",
            "createdAt": now,
            "updatedAt": now,
        }
        if not document["title"] or not document["message"]:
            raise ValueError("Notice title and message are required")
        if document["priority"] not in {"Low", "Medium", "High"}:
            raise ValueError("Priority must be Low, Medium, or High")
        if self.mode == "mongodb":
            inserted = self.notices.insert_one(document)
            document["_id"] = inserted.inserted_id
        else:
            document["id"] = str(uuid4())
            self.memory_notices.insert(0, document)
        return serialize(document)

    def update_student_attendance(self, student_id, attendance):
        value = integer(attendance, 0, 100, "Attendance")
        if self.mode == "mongodb":
            if not ObjectId.is_valid(student_id):
                raise LookupError("Student not found")
            result = self.students.find_one_and_update(
                {"_id": ObjectId(student_id)},
                {"$set": {"attendance": value, "updatedAt": utc_now()}},
                return_document=ReturnDocument.AFTER,
            )
            if not result:
                raise LookupError("Student not found")
            return serialize(result)
        for item in self.memory_students:
            if item["id"] == student_id:
                item["attendance"] = value
                item["updatedAt"] = utc_now()
                return serialize(item)
        raise LookupError("Student not found")

    def stats(self):
        students = self.list_students()
        faculty = self.list_faculty()
        courses = self.list_courses()
        notices = self.list_notices()
        avg_attendance = round(sum(item["attendance"] for item in students) / len(students), 1) if students else 0
        fee_due = sum(item["feeDue"] for item in students)
        return {
            "studentCount": len(students),
            "facultyCount": len(faculty),
            "courseCount": len(courses),
            "noticeCount": len(notices),
            "averageAttendance": avg_attendance,
            "totalFeeDue": fee_due,
            "departments": DEPARTMENTS,
            "years": YEARS,
            "databaseReady": self.mode == "mongodb",
            "mode": self.mode,
            "databaseError": self.error,
        }


def validate_student(document):
    required = ["rollNo", "name", "department", "year", "phone", "email"]
    missing = [field for field in required if not document.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    if document["department"] not in DEPARTMENTS:
        raise ValueError("Invalid department")
    if document["year"] not in YEARS:
        raise ValueError("Invalid year")
    if len(document["phone"]) != 10:
        raise ValueError("Phone number must contain 10 digits")


def validate_faculty(document):
    required = ["facultyId", "name", "department", "designation", "phone", "email"]
    missing = [field for field in required if not document.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    if document["department"] not in DEPARTMENTS:
        raise ValueError("Invalid department")
    if len(document["phone"]) != 10:
        raise ValueError("Phone number must contain 10 digits")


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    store = CollegeStore()

    @app.get("/")
    def home():
        return render_template("index.html", departments=DEPARTMENTS, years=YEARS)

    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "status": "ok", "storeMode": store.mode})

    @app.get("/api/stats")
    def stats():
        return jsonify({"success": True, "stats": store.stats()})

    @app.get("/api/students")
    def students():
        return jsonify({"success": True, "students": store.list_students()})

    @app.post("/api/students")
    def students_create():
        try:
            created = store.create_student(request.get_json(silent=True) or {})
            return jsonify({"success": True, "student": created}), 201
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except PyMongoError as exc:
            return jsonify({"success": False, "message": f"Database error: {exc}"}), 502

    @app.patch("/api/students/<student_id>/attendance")
    def students_attendance(student_id):
        try:
            updated = store.update_student_attendance(student_id, (request.get_json(silent=True) or {}).get("attendance"))
            return jsonify({"success": True, "student": updated})
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except LookupError as exc:
            return jsonify({"success": False, "message": str(exc)}), 404

    @app.get("/api/faculty")
    def faculty():
        return jsonify({"success": True, "faculty": store.list_faculty()})

    @app.post("/api/faculty")
    def faculty_create():
        try:
            created = store.create_faculty(request.get_json(silent=True) or {})
            return jsonify({"success": True, "faculty": created}), 201
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except PyMongoError as exc:
            return jsonify({"success": False, "message": f"Database error: {exc}"}), 502

    @app.get("/api/courses")
    def courses():
        return jsonify({"success": True, "courses": store.list_courses()})

    @app.get("/api/notices")
    def notices():
        return jsonify({"success": True, "notices": store.list_notices()})

    @app.post("/api/notices")
    def notices_create():
        try:
            created = store.create_notice(request.get_json(silent=True) or {})
            return jsonify({"success": True, "notice": created}), 201
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except PyMongoError as exc:
            return jsonify({"success": False, "message": f"Database error: {exc}"}), 502

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
