const employeeForm = document.getElementById('employee-form');
const attendanceForm = document.getElementById('attendance-form');
const registerMessage = document.getElementById('register-message');
const attendanceMessage = document.getElementById('attendance-message');
const summaryElement = document.getElementById('summary');
const tableBody = document.getElementById('attendance-table-body');

async function loadSummary() {
    const response = await fetch('/attendance/summary');
    const data = await response.json();
    summaryElement.innerHTML = `
        <p><strong>Total records:</strong> ${data.total_records}</p>
        <p><strong>Unique employees:</strong> ${data.unique_employees}</p>
        <p><strong>Latest event:</strong> ${data.latest_record.employee_id ?? 'N/A'} / ${data.latest_record.mode ?? 'N/A'}</p>
    `;
}

async function loadAttendance() {
    const response = await fetch('/attendance');
    const data = await response.json();
    tableBody.innerHTML = data.map(record => `
        <tr>
            <td>${record.employee_id}</td>
            <td>${record.mode}</td>
            <td>${record.confidence.toFixed(4)}</td>
            <td>${new Date(record.created_at).toLocaleString()}</td>
        </tr>
    `).join('');
}

employeeForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(employeeForm);
    const response = await fetch('/employees/register', {
        method: 'POST',
        body: formData,
    });
    const result = await response.json();
    registerMessage.textContent = result.status === 'success' ? 'Employee registered successfully.' : result.error;
    registerMessage.className = 'message ' + (result.status === 'success' ? 'success' : 'error');
    employeeForm.reset();
    await loadAttendance();
    await loadSummary();
});

attendanceForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(attendanceForm);
    const response = await fetch('/attendance/check', {
        method: 'POST',
        body: formData,
    });
    const result = await response.json();
    attendanceMessage.textContent = `${result.status} - ${result.employee_id ?? 'Unknown'} - confidence ${result.confidence?.toFixed?.(4) ?? '0.0000'}`;
    attendanceMessage.className = 'message ' + (result.status === 'success' ? 'success' : 'error');
    attendanceForm.reset();
    await loadAttendance();
    await loadSummary();
});

loadSummary();
loadAttendance();
