const state = {
  students: [],
  faculty: [],
  courses: [],
  notices: [],
  stats: {},
  studentQuery: "",
  facultyQuery: "",
};

const statsEl = document.getElementById("stats");
const dbMode = document.getElementById("dbMode");
const studentRows = document.getElementById("studentRows");
const facultyGrid = document.getElementById("facultyGrid");
const courseGrid = document.getElementById("courseGrid");
const noticeList = document.getElementById("noticeList");
const studentForm = document.getElementById("studentForm");
const facultyForm = document.getElementById("facultyForm");
const noticeForm = document.getElementById("noticeForm");
const studentMessage = document.getElementById("studentMessage");
const facultyMessage = document.getElementById("facultyMessage");
const noticeMessage = document.getElementById("noticeMessage");
const studentSearch = document.getElementById("studentSearch");
const facultySearch = document.getElementById("facultySearch");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.success === false) {
    throw new Error(data.message || "Request failed");
  }
  return data;
}

function rupees(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function renderStats() {
  const cards = [
    ["Students", state.stats.studentCount || 0],
    ["Faculty", state.stats.facultyCount || 0],
    ["Courses", state.stats.courseCount || 0],
    ["Avg Attendance", `${state.stats.averageAttendance || 0}%`],
    ["Fee Due", rupees(state.stats.totalFeeDue || 0)],
  ];
  statsEl.innerHTML = cards.map(([label, value]) => `
    <article class="stat"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></article>
  `).join("");
  dbMode.textContent = state.stats.databaseReady ? "MongoDB" : "Memory";
}

function attendanceClass(value) {
  if (value >= 85) return "good";
  if (value >= 75) return "warn";
  return "bad";
}

function renderStudents() {
  const query = state.studentQuery.toLowerCase();
  const rows = state.students.filter((item) => {
    const text = [item.rollNo, item.name, item.department, item.year, item.phone, item.email, item.status].join(" ").toLowerCase();
    return !query || text.includes(query);
  });
  studentRows.innerHTML = rows.map((item) => `
    <tr>
      <td><strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.rollNo)} | ${escapeHtml(item.phone)}<br>${escapeHtml(item.email)}</td>
      <td>${escapeHtml(item.department)}<br>${escapeHtml(item.year)}</td>
      <td><span class="meter ${attendanceClass(item.attendance)}"><i style="width:${escapeHtml(item.attendance)}%"></i></span><b>${escapeHtml(item.attendance)}%</b></td>
      <td>${rupees(item.feeDue)}</td>
      <td><span class="status">${escapeHtml(item.status)}</span></td>
    </tr>
  `).join("") || `<tr><td colspan="5">No students found.</td></tr>`;
}

function renderFaculty() {
  const query = state.facultyQuery.toLowerCase();
  const items = state.faculty.filter((item) => {
    const text = [item.facultyId, item.name, item.department, item.designation, ...(item.subjects || [])].join(" ").toLowerCase();
    return !query || text.includes(query);
  });
  facultyGrid.innerHTML = items.map((item) => `
    <article class="faculty-card">
      <span>${escapeHtml(item.department)}</span>
      <strong>${escapeHtml(item.name)}</strong>
      <p>${escapeHtml(item.designation)} | ${escapeHtml(item.facultyId)}</p>
      <div class="chips">${(item.subjects || []).map((subject) => `<em>${escapeHtml(subject)}</em>`).join("") || "<em>No subjects</em>"}</div>
      <small>${escapeHtml(item.email)} | ${escapeHtml(item.status)}</small>
    </article>
  `).join("") || `<article class="faculty-card"><strong>No faculty found</strong><p>Try another search.</p></article>`;
}

function renderCourses() {
  courseGrid.innerHTML = state.courses.map((item) => `
    <article class="course-card">
      <span>${escapeHtml(item.code)}</span>
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(item.department)} | ${escapeHtml(item.year)} | ${escapeHtml(item.credits)} credits</p>
      <div class="course-meta"><b>${escapeHtml(item.faculty)}</b><small>${escapeHtml(item.enrolled)} students</small></div>
    </article>
  `).join("");
}

function renderNotices() {
  noticeList.innerHTML = state.notices.map((item) => `
    <article class="notice ${String(item.priority).toLowerCase()}">
      <span>${escapeHtml(item.priority)} | ${escapeHtml(item.audience)}</span>
      <strong>${escapeHtml(item.title)}</strong>
      <p>${escapeHtml(item.message)}</p>
    </article>
  `).join("") || `<article class="notice"><strong>No notices</strong><p>Publish a new announcement.</p></article>`;
}

async function refresh() {
  const [statsData, studentsData, facultyData, coursesData, noticesData] = await Promise.all([
    api("/api/stats"),
    api("/api/students"),
    api("/api/faculty"),
    api("/api/courses"),
    api("/api/notices"),
  ]);
  state.stats = statsData.stats || {};
  state.students = studentsData.students || [];
  state.faculty = facultyData.faculty || [];
  state.courses = coursesData.courses || [];
  state.notices = noticesData.notices || [];
  renderStats();
  renderStudents();
  renderFaculty();
  renderCourses();
  renderNotices();
}

async function submitForm(form, path, messageEl, successText) {
  messageEl.textContent = "Saving...";
  messageEl.className = "form-message";
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    await api(path, { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    messageEl.textContent = successText;
    messageEl.className = "form-message ok";
    await refresh();
  } catch (error) {
    messageEl.textContent = error.message;
    messageEl.className = "form-message bad";
  }
}

studentForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitForm(studentForm, "/api/students", studentMessage, "Student saved successfully.");
});

facultyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitForm(facultyForm, "/api/faculty", facultyMessage, "Faculty saved successfully.");
});

noticeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitForm(noticeForm, "/api/notices", noticeMessage, "Notice published successfully.");
});

studentSearch.addEventListener("input", () => {
  state.studentQuery = studentSearch.value;
  renderStudents();
});

facultySearch.addEventListener("input", () => {
  state.facultyQuery = facultySearch.value;
  renderFaculty();
});

refresh().catch((error) => {
  statsEl.innerHTML = `<article class="stat"><strong>!</strong><span>${escapeHtml(error.message)}</span></article>`;
});
