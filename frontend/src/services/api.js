import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getAlerts() {
  const response = await api.get("/alerts/");
  return response.data;
}

export async function getEmployees() {
  const response = await api.get("/employees/");
  return response.data;
}

export async function getDevices() {
  const response = await api.get("/devices/");
  return response.data;
}

export async function getInvestigation(alertId) {
  const response = await api.get(`/alerts/${alertId}/investigation`);
  return response.data;
}

export async function reviewAlert(
  alertId,
  status,
  analystNotes
) {
  const response = await api.patch(
    `/alerts/${alertId}/review`,
    {
      status,
      analyst_notes: analystNotes || null,
    }
  );

  return response.data;
}

/* =========================================================
   EXCEPTIONS
   ========================================================= */

export async function getEmployeeExceptions(
  employeeId
) {
  const response = await api.get(
    `/exceptions/employee/${employeeId}`
  );

  return response.data;
}

export async function createException(exceptionData) {
  const response = await api.post(
    "/exceptions/",
    exceptionData
  );

  return response.data;
}

export async function updateExceptionStatus(
  exceptionId,
  status
) {
  const response = await api.patch(
    `/exceptions/${exceptionId}/status`,
    {
      status,
    }
  );

  return response.data;
}

export async function getBehavioralWindows(
  deviceId = null
) {
  const params = {};

  if (deviceId !== null) {
    params.device_id = deviceId;
  }

  const response = await api.get(
    "/behavior/windows",
    {
      params,
    }
  );

  return response.data;
}