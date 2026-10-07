import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Monitor,
  RefreshCw,
  Search,
  ShieldAlert,
  XCircle,
} from "lucide-react";

import { getDevices, getEmployees } from "../services/api";

function formatDate(value) {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function getEmployeeName(employeeId, employees) {
  const employee = employees.find(
    (item) => item.id === employeeId
  );

  if (!employee) {
    return `Employee #${employeeId}`;
  }

  return employee.employee_code;
}

function StatusBadge({ active }) {
  if (active) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-400">
        <CheckCircle2 size={12} />
        ACTIVE
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-[10px] font-medium text-red-400">
      <XCircle size={12} />
      INACTIVE
    </span>
  );
}

function StatCard({ label, value, icon: Icon, tone = "cyan" }) {
  const tones = {
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    green:
      "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    red: "text-red-400 bg-red-500/10 border-red-500/20",
    slate:
      "text-slate-300 bg-slate-500/10 border-slate-500/20",
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500">
            {label}
          </p>

          <p className="mt-1 text-2xl font-semibold text-white">
            {value}
          </p>
        </div>

        <div
          className={`rounded-lg border p-2 ${tones[tone]}`}
        >
          <Icon size={17} />
        </div>
      </div>
    </div>
  );
}

export default function Endpoints() {
  const [devices, setDevices] = useState([]);
  const [employees, setEmployees] = useState([]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadEndpoints() {
    try {
      setLoading(true);
      setError("");

      const [deviceData, employeeData] =
        await Promise.all([
          getDevices(),
          getEmployees(),
        ]);

      setDevices(
        Array.isArray(deviceData)
          ? deviceData
          : []
      );

      setEmployees(
        Array.isArray(employeeData)
          ? employeeData
          : []
      );
    } catch (err) {
      console.error(
        "Failed to load endpoints:",
        err
      );

      setError(
        "Unable to load endpoint information from the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEndpoints();
  }, []);

  const statistics = useMemo(() => {
    const active = devices.filter(
      (device) => device.is_active
    ).length;

    const inactive = devices.filter(
      (device) => !device.is_active
    ).length;

    const seen = devices.filter(
      (device) => device.last_seen
    ).length;

    return {
      total: devices.length,
      active,
      inactive,
      seen,
    };
  }, [devices]);

  const filteredDevices = useMemo(() => {
    const query = search.trim().toLowerCase();

    return devices.filter((device) => {
      const matchesStatus =
        statusFilter === "ALL" ||
        (statusFilter === "ACTIVE" &&
          device.is_active) ||
        (statusFilter === "INACTIVE" &&
          !device.is_active);

      const employeeCode =
        getEmployeeName(
          device.employee_id,
          employees
        ).toLowerCase();

      const matchesSearch =
        !query ||
        device.device_code
          ?.toLowerCase()
          .includes(query) ||
        device.operating_system
          ?.toLowerCase()
          .includes(query) ||
        employeeCode.includes(query);

      return matchesStatus && matchesSearch;
    });
  }, [
    devices,
    employees,
    search,
    statusFilter,
  ]);

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400">
            Endpoint Security
          </p>

          <h1 className="mt-2 text-2xl font-bold sm:text-3xl">
            Endpoints
          </h1>

          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Monitor registered devices and endpoint agent
            health across the organization.
          </p>
        </div>

        <button
          onClick={loadEndpoints}
          disabled={loading}
          className="flex w-fit items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs text-slate-400 transition hover:border-slate-700 hover:text-white disabled:opacity-50"
        >
          <RefreshCw
            size={14}
            className={
              loading ? "animate-spin" : ""
            }
          />

          Refresh
        </button>
      </div>

      {/* Security note */}
      <div className="mb-5 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
        <div className="flex gap-3">
          <ShieldAlert
            size={19}
            className="mt-0.5 shrink-0 text-cyan-400"
          />

          <div>
            <p className="text-sm font-medium text-cyan-300">
              Endpoint identity
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Devices authenticate to the backend using
              securely generated credentials. Only device
              metadata is displayed here; credentials and
              credential hashes are never exposed.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <div className="flex items-center gap-3">
            <ShieldAlert
              size={18}
              className="text-red-400"
            />

            <p className="text-sm text-red-400">
              {error}
            </p>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Registered Devices"
          value={statistics.total}
          icon={Monitor}
        />

        <StatCard
          label="Active"
          value={statistics.active}
          icon={CheckCircle2}
          tone="green"
        />

        <StatCard
          label="Inactive"
          value={statistics.inactive}
          icon={XCircle}
          tone="red"
        />

        <StatCard
          label="Reported Last Seen"
          value={statistics.seen}
          icon={ShieldAlert}
          tone="slate"
        />
      </div>

      {/* Filters */}
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-slate-800 bg-[#0a0f18] px-3 py-2 sm:max-w-sm">
          <Search
            size={16}
            className="text-slate-600"
          />

          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search device, OS, employee..."
            className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
        </div>

        <div className="flex rounded-lg border border-slate-800 bg-[#0a0f18] p-1">
          {["ALL", "ACTIVE", "INACTIVE"].map(
            (status) => (
              <button
                key={status}
                onClick={() =>
                  setStatusFilter(status)
                }
                className={`rounded-md px-3 py-1.5 text-[10px] font-medium transition ${
                  statusFilter === status
                    ? "bg-cyan-500/10 text-cyan-400"
                    : "text-slate-500 hover:text-white"
                }`}
              >
                {status}
              </button>
            )
          )}
        </div>
      </div>

      {/* Endpoint table */}
      <section className="overflow-hidden rounded-xl border border-slate-800 bg-[#0a0f18]">
        <div className="border-b border-slate-800 px-5 py-4">
          <h2 className="font-semibold">
            Registered Endpoints
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            {filteredDevices.length} endpoint
            {filteredDevices.length === 1
              ? ""
              : "s"} shown
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
                Loading endpoints...
              </p>
            </div>
          </div>
        ) : filteredDevices.length === 0 ? (
          <div className="flex min-h-[300px] items-center justify-center p-6">
            <div className="text-center">
              <Monitor
                size={32}
                className="mx-auto text-slate-700"
              />

              <p className="mt-3 text-sm text-slate-400">
                No endpoints found.
              </p>

              <p className="mt-1 text-xs text-slate-600">
                Try changing the search or status filter.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Desktop */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left">
                <thead className="border-b border-slate-800 bg-slate-900/30">
                  <tr className="text-[10px] uppercase tracking-wider text-slate-600">
                    <th className="px-5 py-3 font-medium">
                      Endpoint
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Employee
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Operating System
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Agent
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Last Seen
                    </th>

                    <th className="px-5 py-3 font-medium">
                      Status
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800/70">
                  {filteredDevices.map(
                    (device) => (
                      <tr
                        key={device.id}
                        className="transition hover:bg-slate-900/30"
                      >
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900">
                              <Monitor
                                size={16}
                                className="text-cyan-400"
                              />
                            </div>

                            <div>
                              <p className="text-sm font-medium text-white">
                                {device.device_code}
                              </p>

                              <p className="text-[10px] text-slate-600">
                                ID #{device.id}
                              </p>
                            </div>
                          </div>
                        </td>

                        <td className="px-5 py-4 text-sm text-slate-400">
                          {getEmployeeName(
                            device.employee_id,
                            employees
                          )}
                        </td>

                        <td className="px-5 py-4 text-sm text-slate-400">
                          {device.operating_system}
                        </td>

                        <td className="px-5 py-4">
                          <span className="rounded-md bg-slate-900 px-2 py-1 text-xs text-slate-400">
                            v{device.agent_version}
                          </span>
                        </td>

                        <td className="px-5 py-4 text-xs text-slate-500">
                          {formatDate(
                            device.last_seen
                          )}
                        </td>

                        <td className="px-5 py-4">
                          <StatusBadge
                            active={
                              device.is_active
                            }
                          />
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>

            {/* Mobile */}
            <div className="divide-y divide-slate-800/70 md:hidden">
              {filteredDevices.map(
                (device) => (
                  <div
                    key={device.id}
                    className="p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900">
                          <Monitor
                            size={16}
                            className="text-cyan-400"
                          />
                        </div>

                        <div>
                          <p className="text-sm font-medium text-white">
                            {device.device_code}
                          </p>

                          <p className="text-[10px] text-slate-600">
                            ID #{device.id}
                          </p>
                        </div>
                      </div>

                      <StatusBadge
                        active={device.is_active}
                      />
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Employee
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          {getEmployeeName(
                            device.employee_id,
                            employees
                          )}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          OS
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          {device.operating_system}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Agent
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          v{device.agent_version}
                        </p>
                      </div>

                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-600">
                          Last Seen
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          {formatDate(
                            device.last_seen
                          )}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}