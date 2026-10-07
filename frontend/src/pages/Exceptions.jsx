import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Plus,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import {
  createException,
  getEmployeeExceptions,
  getEmployees,
  updateExceptionStatus,
} from "../services/api";

const ACTIVITY_OPTIONS = [
  "create",
  "modify",
  "delete",
  "move",
];

const STATUS_FILTERS = [
  "ALL",
  "ACTIVE",
  "REVOKED",
  "EXPIRED",
];

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function getStatusClasses(status) {
  switch (status) {
    case "ACTIVE":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";

    case "REVOKED":
      return "border-red-500/20 bg-red-500/10 text-red-400";

    case "EXPIRED":
      return "border-slate-500/20 bg-slate-500/10 text-slate-400";

    default:
      return "border-slate-700 bg-slate-900 text-slate-400";
  }
}

function getEmployeeLabel(employee) {
  if (!employee) {
    return "Unknown employee";
  }

  return (
    employee.employee_code ||
    `Employee #${employee.id}`
  );
}

function toIsoDateTime(localValue) {
  if (!localValue) {
    return null;
  }

  const date = new Date(localValue);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toISOString();
}

export default function Exceptions() {
  const [employees, setEmployees] = useState([]);
  const [exceptions, setExceptions] = useState([]);

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [showCreateForm, setShowCreateForm] =
    useState(false);

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [updatingId, setUpdatingId] =
    useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    employee_id: "",
    reason: "",
    authorized_by: "",
    start_time: "",
    end_time: "",
    allowed_activity: "delete",
  });

  async function loadExceptions() {
    try {
      setLoading(true);
      setError("");

      const employeeData = await getEmployees();

      const employeeList = Array.isArray(employeeData)
        ? employeeData
        : [];

      setEmployees(employeeList);

      const results = await Promise.all(
        employeeList.map(async (employee) => {
          try {
            const data =
              await getEmployeeExceptions(
                employee.id
              );

            return Array.isArray(data)
              ? data
              : [];
          } catch (employeeError) {
            console.error(
              `Failed to load exceptions for employee ${employee.id}:`,
              employeeError
            );

            return [];
          }
        })
      );

      const flattened = results.flat();

      flattened.sort(
        (a, b) =>
          new Date(b.created_at) -
          new Date(a.created_at)
      );

      setExceptions(flattened);
    } catch (err) {
      console.error(
        "Failed to load exceptions:",
        err
      );

      setError(
        "Unable to load exception authorizations from the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadExceptions();
  }, []);

  const employeeMap = useMemo(() => {
    return new Map(
      employees.map((employee) => [
        employee.id,
        employee,
      ])
    );
  }, [employees]);

  const filteredExceptions = useMemo(() => {
    if (statusFilter === "ALL") {
      return exceptions;
    }

    return exceptions.filter(
      (exception) =>
        exception.status === statusFilter
    );
  }, [exceptions, statusFilter]);

  const counts = useMemo(() => {
    return {
      all: exceptions.length,

      active: exceptions.filter(
        (exception) =>
          exception.status === "ACTIVE"
      ).length,

      revoked: exceptions.filter(
        (exception) =>
          exception.status === "REVOKED"
      ).length,

      expired: exceptions.filter(
        (exception) =>
          exception.status === "EXPIRED"
      ).length,
    };
  }, [exceptions]);

  function handleFormChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function resetForm() {
    setForm({
      employee_id: "",
      reason: "",
      authorized_by: "",
      start_time: "",
      end_time: "",
      allowed_activity: "delete",
    });
  }

  async function handleCreateException(event) {
    event.preventDefault();

    try {
      setCreating(true);
      setError("");
      setSuccess("");

      if (!form.employee_id) {
        throw new Error(
          "Please select an employee."
        );
      }

      if (!form.reason.trim()) {
        throw new Error(
          "Please provide an authorization reason."
        );
      }

      if (!form.authorized_by.trim()) {
        throw new Error(
          "Please provide the approving authority."
        );
      }

      if (!form.start_time || !form.end_time) {
        throw new Error(
          "Please provide the authorization time window."
        );
      }

      const startTime = toIsoDateTime(
        form.start_time
      );

      const endTime = toIsoDateTime(
        form.end_time
      );

      if (!startTime || !endTime) {
        throw new Error(
          "Invalid start or end time."
        );
      }

      if (
        new Date(endTime) <= new Date(startTime)
      ) {
        throw new Error(
          "End time must be later than start time."
        );
      }

      await createException({
        employee_id: Number(form.employee_id),
        reason: form.reason.trim(),
        authorized_by: form.authorized_by.trim(),
        start_time: startTime,
        end_time: endTime,
        allowed_activity:
          form.allowed_activity,
      });

      resetForm();
      setShowCreateForm(false);

      setSuccess(
        "Authorization exception created successfully."
      );

      await loadExceptions();
    } catch (err) {
      console.error(
        "Failed to create exception:",
        err
      );

      setError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to create exception."
      );
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(exceptionId) {
    const confirmed = window.confirm(
      "Revoke this authorization exception?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setUpdatingId(exceptionId);
      setError("");
      setSuccess("");

      await updateExceptionStatus(
        exceptionId,
        "REVOKED"
      );

      setSuccess(
        "Authorization exception revoked."
      );

      await loadExceptions();
    } catch (err) {
      console.error(
        "Failed to revoke exception:",
        err
      );

      setError(
        err.response?.data?.detail ||
          "Failed to revoke exception."
      );
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400">
            Authorization Control
          </p>

          <h1 className="mt-2 text-2xl font-bold sm:text-3xl">
            Exceptions
          </h1>

          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Manage approved activity windows without
            disabling behavioral anomaly detection.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={loadExceptions}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs text-slate-400 transition hover:border-slate-700 hover:text-white disabled:opacity-50"
          >
            <RefreshCw
              size={14}
              className={
                loading ? "animate-spin" : ""
              }
            />
            Refresh
          </button>

          <button
            onClick={() => {
              setShowCreateForm(
                (current) => !current
              );
              setError("");
              setSuccess("");
            }}
            className="flex items-center gap-2 rounded-lg bg-cyan-500 px-3 py-2 text-xs font-medium text-slate-950 transition hover:bg-cyan-400"
          >
            <Plus size={15} />
            Create Exception
          </button>
        </div>
      </div>

      {/* Important system note */}
      <div className="mb-5 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
        <div className="flex gap-3">
          <ShieldCheck
            size={19}
            className="mt-0.5 shrink-0 text-cyan-400"
          />

          <div>
            <p className="text-sm font-medium text-cyan-300">
              Authorization does not disable ML detection
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              An approved exception provides authorization
              context to the risk engine. The activity
              remains observable and can still be anomalous
              or require analyst review.
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <div className="flex items-center gap-3">
            <AlertTriangle
              size={18}
              className="text-red-400"
            />

            <p className="text-sm text-red-400">
              {error}
            </p>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
          <div className="flex items-center gap-3">
            <CheckCircle2
              size={18}
              className="text-emerald-400"
            />

            <p className="text-sm text-emerald-400">
              {success}
            </p>
          </div>
        </div>
      )}

      {/* Create form */}
      {showCreateForm && (
        <section className="mb-5 rounded-xl border border-slate-800 bg-[#0a0f18]">
          <div className="border-b border-slate-800 px-5 py-4">
            <h2 className="font-semibold text-white">
              Create Authorization Exception
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Define exactly which employee activity is
              authorized and for how long.
            </p>
          </div>

          <form
            onSubmit={handleCreateException}
            className="p-5"
          >
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {/* Employee */}
              <div>
                <label className="text-xs font-medium text-slate-400">
                  Employee
                </label>

                <select
                  name="employee_id"
                  value={form.employee_id}
                  onChange={handleFormChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500/40"
                >
                  <option value="">
                    Select employee
                  </option>

                  {employees
                    .filter(
                      (employee) =>
                        employee.is_active !== false
                    )
                    .map((employee) => (
                      <option
                        key={employee.id}
                        value={employee.id}
                      >
                        {getEmployeeLabel(employee)}
                        {employee.role
                          ? ` — ${employee.role}`
                          : ""}
                      </option>
                    ))}
                </select>
              </div>

              {/* Activity */}
              <div>
                <label className="text-xs font-medium text-slate-400">
                  Allowed Activity
                </label>

                <select
                  name="allowed_activity"
                  value={form.allowed_activity}
                  onChange={handleFormChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500/40"
                >
                  {ACTIVITY_OPTIONS.map(
                    (activity) => (
                      <option
                        key={activity}
                        value={activity}
                      >
                        {activity.toUpperCase()}
                      </option>
                    )
                  )}
                </select>
              </div>

              {/* Reason */}
              <div className="md:col-span-2">
                <label className="text-xs font-medium text-slate-400">
                  Authorization Reason
                </label>

                <textarea
                  name="reason"
                  value={form.reason}
                  onChange={handleFormChange}
                  required
                  rows={3}
                  placeholder="Example: Approved data migration including deletion of obsolete files"
                  className="mt-2 w-full resize-none rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-700 focus:border-cyan-500/40"
                />
              </div>

              {/* Authorized by */}
              <div>
                <label className="text-xs font-medium text-slate-400">
                  Authorized By
                </label>

                <input
                  name="authorized_by"
                  value={form.authorized_by}
                  onChange={handleFormChange}
                  required
                  placeholder="Security Admin"
                  className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-700 focus:border-cyan-500/40"
                />
              </div>

              {/* Start */}
              <div>
                <label className="text-xs font-medium text-slate-400">
                  Start Time
                </label>

                <input
                  type="datetime-local"
                  name="start_time"
                  value={form.start_time}
                  onChange={handleFormChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500/40"
                />
              </div>

              {/* End */}
              <div>
                <label className="text-xs font-medium text-slate-400">
                  End Time
                </label>

                <input
                  type="datetime-local"
                  name="end_time"
                  value={form.end_time}
                  onChange={handleFormChange}
                  required
                  className="mt-2 w-full rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-500/40"
                />
              </div>
            </div>

            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => {
                  resetForm();
                  setShowCreateForm(false);
                }}
                className="rounded-lg border border-slate-800 px-4 py-2.5 text-xs text-slate-400 transition hover:text-white"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={creating}
                className="flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2.5 text-xs font-medium text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
              >
                {creating && (
                  <RefreshCw
                    size={14}
                    className="animate-spin"
                  />
                )}

                {creating
                  ? "Creating..."
                  : "Create Authorization"}
              </button>
            </div>
          </form>
        </section>
      )}

      {/* Status filters */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          ["ALL", "All", counts.all],
          ["ACTIVE", "Active", counts.active],
          ["REVOKED", "Revoked", counts.revoked],
          ["EXPIRED", "Expired", counts.expired],
        ].map(([value, label, count]) => (
          <button
            key={value}
            onClick={() =>
              setStatusFilter(value)
            }
            className={`rounded-xl border p-4 text-left transition ${
              statusFilter === value
                ? "border-cyan-500/30 bg-cyan-500/5"
                : "border-slate-800 bg-[#0a0f18] hover:border-slate-700"
            }`}
          >
            <p className="text-xs text-slate-500">
              {label}
            </p>

            <p className="mt-1 text-xl font-semibold text-white">
              {count}
            </p>
          </button>
        ))}
      </div>

      {/* Exception list */}
      <section className="rounded-xl border border-slate-800 bg-[#0a0f18]">
        <div className="border-b border-slate-800 px-5 py-4">
          <h2 className="font-semibold text-white">
            Authorization Records
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Approved activity windows used by the risk
            engine during investigation.
          </p>
        </div>

        {loading ? (
          <div className="flex min-h-[300px] items-center justify-center">
            <div className="text-center">
              <RefreshCw
                size={25}
                className="mx-auto animate-spin text-cyan-400"
              />

              <p className="mt-3 text-sm text-slate-500">
                Loading authorization records...
              </p>
            </div>
          </div>
        ) : filteredExceptions.length === 0 ? (
          <div className="flex min-h-[300px] items-center justify-center p-6">
            <div className="text-center">
              <ShieldCheck
                size={32}
                className="mx-auto text-slate-700"
              />

              <p className="mt-3 text-sm text-slate-400">
                No exception records found.
              </p>

              <p className="mt-1 text-xs text-slate-600">
                Create an authorization when legitimate
                activity needs temporary approval.
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/70">
            {filteredExceptions.map(
              (exception) => {
                const employee =
                  employeeMap.get(
                    exception.employee_id
                  );

                const canRevoke =
                  exception.status === "ACTIVE";

                return (
                  <div
                    key={exception.id}
                    className="p-5 transition hover:bg-slate-900/20"
                  >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-white">
                            Exception #
                            {exception.id}
                          </span>

                          <span
                            className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${getStatusClasses(
                              exception.status
                            )}`}
                          >
                            {exception.status}
                          </span>
                        </div>

                        <p className="mt-2 text-sm text-cyan-400">
                          {getEmployeeLabel(
                            employee
                          )}
                        </p>

                        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                          {exception.reason}
                        </p>
                      </div>

                      {canRevoke && (
                        <button
                          onClick={() =>
                            handleRevoke(
                              exception.id
                            )
                          }
                          disabled={
                            updatingId ===
                            exception.id
                          }
                          className="flex w-fit shrink-0 items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs text-red-400 transition hover:bg-red-500/10 disabled:opacity-50"
                        >
                          {updatingId ===
                          exception.id ? (
                            <RefreshCw
                              size={14}
                              className="animate-spin"
                            />
                          ) : (
                            <XCircle size={14} />
                          )}

                          Revoke
                        </button>
                      )}
                    </div>

                    <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Allowed Activity
                        </p>

                        <p className="mt-1 text-sm font-medium text-white">
                          {exception.allowed_activity.toUpperCase()}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Authorized By
                        </p>

                        <p className="mt-1 text-sm text-slate-300">
                          {exception.authorized_by}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Valid From
                        </p>

                        <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                          <Clock3 size={13} />
                          {formatDate(
                            exception.start_time
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Valid Until
                        </p>

                        <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                          <Clock3 size={13} />
                          {formatDate(
                            exception.end_time
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 border-t border-slate-800/70 pt-3">
                      <p className="text-[10px] text-slate-600">
                        Created{" "}
                        {formatDate(
                          exception.created_at
                        )}
                      </p>
                    </div>
                  </div>
                );
              }
            )}
          </div>
        )}
      </section>
    </div>
  );
}