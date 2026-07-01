use("college_erp_system");

db.students.createIndex({ rollNo: 1 }, { unique: true });
db.students.createIndex({ department: 1, year: 1 });
db.faculty.createIndex({ facultyId: 1 }, { unique: true });
db.courses.createIndex({ code: 1 }, { unique: true });
db.notices.createIndex({ createdAt: -1 });

db.students.insertOne({
  rollNo: "KCDS23AIML001",
  name: "Demo Student",
  department: "AIML",
  year: "3rd Year",
  phone: "9999999999",
  email: "student@kcds.edu",
  attendance: 92,
  feeDue: 0,
  status: "Active",
  createdAt: new Date(),
  updatedAt: new Date()
});
