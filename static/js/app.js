// NCCR Rehabilitation Platform - Main JavaScript

// API Base URL
const API_BASE = 'http://localhost:8000/api';

// Utility Functions
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"></div>';
    }
}

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} fade-in`;
    alertDiv.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; cursor: pointer; font-size: 1.2rem;">&times;</button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        setTimeout(() => alertDiv.remove(), 5000);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

// Dashboard Functions
async function loadDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        
        document.getElementById('total-patients').textContent = data.total_patients || 0;
        document.getElementById('total-assessments').textContent = data.total_assessments || 0;
        document.getElementById('emg-sessions').textContent = data.emg_sessions || 0;
        document.getElementById('balance-tests').textContent = data.balance_tests || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
        // Silently fail - don't show alert for stats
    }
}

async function loadRecentPatients() {
    try {
        showLoading('recent-patients');
        const response = await fetch(`${API_BASE}/patients/?limit=5`);
        if (!response.ok) throw new Error('Failed to fetch patients');
        const patients = await response.json();
        
        const tbody = document.querySelector('#recent-patients tbody');
        if (!tbody) return;
        
        if (!patients || patients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-gray);">No patients found. Upload data to get started!</td></tr>';
            return;
        }
        
        tbody.innerHTML = patients.map(patient => `
            <tr>
                <td><strong>${patient.patient_id}</strong></td>
                <td>${patient.name}</td>
                <td>${formatDate(patient.date_of_birth)}</td>
                <td><span class="badge badge-info">GMFCS ${patient.gmfcs_level || 'N/A'}</span></td>
                <td>
                    <button onclick="viewPatient('${patient.patient_id}')" class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.875rem;">
                        View Details
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading patients:', error);
        const tbody = document.querySelector('#recent-patients tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-gray);">Loading patients...</td></tr>';
        }
    }
}

// Patient Functions
async function loadAllPatients() {
    try {
        showLoading('all-patients');
        const response = await fetch(`${API_BASE}/patients/`);
        if (!response.ok) throw new Error('Failed to fetch patients');
        const patients = await response.json();
        
        const tbody = document.querySelector('#all-patients tbody');
        if (!tbody) return;
        
        if (!patients || patients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-gray);">No patients found. Upload clinical data or EMG files to create patient records!</td></tr>';
            return;
        }
        
        tbody.innerHTML = patients.map(patient => `
            <tr>
                <td><strong>${patient.patient_id}</strong></td>
                <td>${patient.name}</td>
                <td>${patient.sex || 'N/A'}</td>
                <td>${formatDate(patient.date_of_birth)}</td>
                <td><span class="badge badge-info">GMFCS ${patient.gmfcs_level || 'N/A'}</span></td>
                <td>
                    <button onclick="viewPatient('${patient.patient_id}')" class="btn btn-primary" style="padding: 0.5rem 1rem; font-size: 0.875rem;">
                        👁️ View
                    </button>
                    <button onclick="editPatient('${patient.patient_id}', ${patient.id})" class="btn" style="padding: 0.5rem 1rem; font-size: 0.875rem; background: #f59e0b; color: white;">
                        ✏️ Edit
                    </button>
                    <button onclick="deletePatient('${patient.patient_id}', ${patient.id})" class="btn" style="padding: 0.5rem 1rem; font-size: 0.875rem; background: #ef4444; color: white;">
                        🗑️ Delete
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading patients:', error);
        const tbody = document.querySelector('#all-patients tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-danger);">Unable to load patients. Please refresh the page.</td></tr>';
        }
    }
}

async function viewPatient(patientId) {
    window.location.href = `patient-details.html?id=${patientId}`;
}

async function editPatient(patientId, id) {
    // For now, show an alert. Can be expanded to show edit modal
    const newName = prompt(`Edit patient name for ${patientId}:`, patientId);
    if (!newName || newName === patientId) return;
    
    try {
        const response = await fetch(`${API_BASE}/patients/${patientId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: newName
            })
        });
        
        if (!response.ok) throw new Error('Failed to update patient');
        
        showAlert(`Patient ${patientId} updated successfully!`, 'success');
        loadAllPatients(); // Refresh the list
    } catch (error) {
        console.error('Error updating patient:', error);
        showAlert('Failed to update patient. Please try again.', 'danger');
    }
}

async function deletePatient(patientId, id) {
    if (!confirm(`⚠️ Are you sure you want to delete patient "${patientId}"?\n\nThis will permanently delete:\n- Patient record\n- All EMG sessions\n- All balance tests\n- All assessments\n- All recommendations\n\nThis action CANNOT be undone!`)) {
        return;
    }
    
    // Double confirmation for safety
    if (!confirm(`FINAL CONFIRMATION: Delete patient "${patientId}" and ALL associated data?`)) {
        return;
    }
    
    try {
        showAlert(`Deleting patient ${patientId}...`, 'info');
        
        const response = await fetch(`${API_BASE}/patients/${patientId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete patient');
        
        showAlert(`Patient ${patientId} deleted successfully!`, 'success');
        loadAllPatients(); // Refresh the list
    } catch (error) {
        console.error('Error deleting patient:', error);
        showAlert('Failed to delete patient. Please try again.', 'danger');
    }
}

async function deleteAllPatients() {
    if (!confirm(`⚠️⚠️⚠️ DANGER ⚠️⚠️⚠️\n\nAre you ABSOLUTELY SURE you want to DELETE ALL PATIENTS?\n\nThis will permanently delete:\n- ALL patient records\n- ALL EMG sessions\n- ALL balance tests\n- ALL assessments\n- ALL recommendations\n- EVERYTHING in the database\n\nThis action CANNOT be undone!`)) {
        return;
    }
    
    // Triple confirmation for safety
    const confirmation = prompt('Type "DELETE ALL" to confirm (case sensitive):');
    if (confirmation !== 'DELETE ALL') {
        showAlert('Deletion cancelled', 'info');
        return;
    }
    
    try {
        showAlert('Deleting all patients...', 'info');
        
        // Get all patients first
        const response = await fetch(`${API_BASE}/patients/`);
        if (!response.ok) throw new Error('Failed to fetch patients');
        const patients = await response.json();
        
        // Delete each patient
        let deleted = 0;
        for (const patient of patients) {
            try {
                const delResponse = await fetch(`${API_BASE}/patients/${patient.patient_id}`, {
                    method: 'DELETE'
                });
                if (delResponse.ok) deleted++;
            } catch (err) {
                console.error(`Failed to delete ${patient.patient_id}:`, err);
            }
        }
        
        showAlert(`Successfully deleted ${deleted} patient(s)!`, 'success');
        loadAllPatients(); // Refresh the list
    } catch (error) {
        console.error('Error deleting all patients:', error);
        showAlert('Failed to delete all patients. Please try again.', 'danger');
    }
}

// File Upload Functions
function setupFileUpload(uploadAreaId, fileInputId, fileType) {
    const uploadArea = document.getElementById(uploadAreaId);
    const fileInput = document.getElementById(fileInputId);
    
    if (!uploadArea || !fileInput) return;
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        handleFileUpload(files, fileType);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFileUpload(e.target.files, fileType);
    });
}

async function handleFileUpload(files, fileType) {
    if (files.length === 0) return;
    
    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    const endpoints = {
        'emg': '/import/emg/pdf',
        'balance': '/import/balance/pdf',
        'clinical': '/import/clinical/excel'
    };
    
    try {
        showAlert(`Uploading ${file.name}...`, 'info');
        
        const response = await fetch(`${API_BASE}${endpoints[fileType]}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const result = await response.json();
        showAlert(`Successfully uploaded ${file.name}!`, 'success');
        
        // Refresh data if on relevant page
        if (typeof loadAllPatients === 'function') {
            setTimeout(loadAllPatients, 1000);
        }
        if (typeof loadDashboardStats === 'function') {
            setTimeout(loadDashboardStats, 1000);
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert(`Failed to upload ${file.name}. Please try again.`, 'danger');
    }
}

// Assessment Functions
async function generateAssessment(patientId) {
    if (!confirm(`Generate AI assessment for patient ${patientId}?`)) return;
    
    try {
        showAlert('Generating assessment... This may take 15-30 seconds.', 'info');
        
        const response = await fetch(`${API_BASE}/assessments/${patientId}/generate`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Assessment generation failed');
        }
        
        const result = await response.json();
        showAlert('Assessment generated successfully!', 'success');
        
        // Redirect to assessment view
        setTimeout(() => {
            window.location.href = `assessment-details.html?patient=${patientId}&assessment=${result.id}`;
        }, 1500);
    } catch (error) {
        console.error('Assessment error:', error);
        showAlert('Failed to generate assessment. Ensure patient has data imported.', 'danger');
    }
}

async function loadPatientAssessments(patientId) {
    try {
        const response = await fetch(`${API_BASE}/assessments/${patientId}`);
        const assessments = await response.json();
        
        const container = document.getElementById('assessments-list');
        if (!assessments || assessments.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-gray);">No assessments found for this patient.</p>';
            return;
        }
        
        container.innerHTML = assessments.map(assessment => `
            <div class="card">
                <div class="card-header">
                    <div>
                        <h3 class="card-title">Assessment - ${formatDate(assessment.assessment_date)}</h3>
                        <p style="color: var(--text-gray); margin-top: 0.5rem;">
                            Disability Index: <strong>${assessment.disability_index?.toFixed(2) || 'N/A'}</strong>
                        </p>
                    </div>
                    <span class="badge ${getSeverityBadge(assessment.disability_severity)}">${assessment.disability_severity || 'N/A'}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div>
                        <p class="stat-label">Motor Function</p>
                        <p class="stat-value" style="font-size: 1.5rem;">${assessment.motor_function_score?.toFixed(1) || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="stat-label">Balance Score</p>
                        <p class="stat-value" style="font-size: 1.5rem;">${assessment.balance_score?.toFixed(1) || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="stat-label">Cognitive Function</p>
                        <p class="stat-value" style="font-size: 1.5rem;">${assessment.cognitive_function_score?.toFixed(1) || 'N/A'}</p>
                    </div>
                    <div>
                        <p class="stat-label">Fall Risk</p>
                        <p class="stat-value" style="font-size: 1.5rem;">${assessment.fall_risk_level || 'N/A'}</p>
                    </div>
                </div>
                <div style="margin-top: 1.5rem;">
                    <button onclick="viewAssessmentDetails(${assessment.id})" class="btn btn-primary">
                        View Full Report
                    </button>
                    <button onclick="generateRecommendations('${patientId}', ${assessment.id})" class="btn btn-success">
                        Generate Recommendations
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading assessments:', error);
        showAlert('Failed to load assessments', 'danger');
    }
}

function getSeverityBadge(severity) {
    const badges = {
        'Mild': 'badge-success',
        'Moderate': 'badge-warning',
        'Severe': 'badge-danger',
        'Profound': 'badge-danger'
    };
    return badges[severity] || 'badge-info';
}

// Recommendations
async function generateRecommendations(patientId, assessmentId) {
    if (!confirm('Generate rehabilitation recommendations?')) return;
    
    try {
        showAlert('Generating personalized rehabilitation plan...', 'info');
        
        const response = await fetch(`${API_BASE}/recommendations/${patientId}/generate`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Recommendation generation failed');
        }
        
        showAlert('Recommendations generated successfully!', 'success');
        setTimeout(() => location.reload(), 1500);
    } catch (error) {
        console.error('Recommendation error:', error);
        showAlert('Failed to generate recommendations', 'danger');
    }
}

// Navigation
function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setActiveNav();
    
    // Dashboard
    if (document.getElementById('total-patients')) {
        loadDashboardStats();
        loadRecentPatients();
    }
    
    // Patients page
    if (document.getElementById('all-patients')) {
        loadAllPatients();
    }
    
    // Import page
    setupFileUpload('emg-upload-area', 'emg-file-input', 'emg');
    setupFileUpload('balance-upload-area', 'balance-file-input', 'balance');
    setupFileUpload('clinical-upload-area', 'clinical-file-input', 'clinical');
    
    // Patient details page
    const urlParams = new URLSearchParams(window.location.search);
    const patientId = urlParams.get('id');
    if (patientId && document.getElementById('assessments-list')) {
        loadPatientAssessments(patientId);
    }
});
