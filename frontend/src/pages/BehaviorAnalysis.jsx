import { useEffect, useMemo, useState } from "react";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  Clock3,
  Database,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { getBehavioralWindows } from "../services/api";

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

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "—";
  }

  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(
    bytes /
    (1024 * 1024 * 1024)
  ).toFixed(1)} GB`;
}

function Metric({ label, value }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-slate-600">
        {label}
      </p>

      <p className="mt-1 text-sm font-medium text-white">
        {value}
      </p>
    </div>
  );
}

export default function BehaviorAnalysis() {
  const [windows, setWindows] = useState([]);
  const [selectedWindow, setSelectedWindow] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadWindows() {
    try {
      setLoading(true);
      setError("");

      const data = await getBehavioralWindows();

      const result = Array.isArray(data)
        ? data
        : [];

      setWindows(result);

      if (result.length > 0) {
        setSelectedWindow((current) => {
          if (!current) {
            return result[0];
          }

          return (
            result.find(
              (window) =>
                window.id === current.id
            ) || result[0]
          );
        });
      } else {
        setSelectedWindow(null);
      }
    } catch (err) {
      console.error(
        "Failed to load behavioral windows:",
        err
      );

      setError(
        "Unable to load behavioral telemetry from the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWindows();
  }, []);

  const statistics = useMemo(() => {
    const totalEvents = windows.reduce(
      (sum, window) =>
        sum + (window.total_events || 0),
      0
    );

    const sensitiveEvents = windows.reduce(
      (sum, window) =>
        sum + (window.sensitive_events || 0),
      0
    );

    const afterHours = windows.filter(
      (window) => window.after_hours
    ).length;

    const devices = new Set(
      windows.map((window) => window.device_id)
    );

    return {
      windows: windows.length,
      totalEvents,
      sensitiveEvents,
      afterHours,
      devices: devices.size,
    };
  }, [windows]);

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400">
            Behavioral Intelligence
          </p>

          <h1 className="mt-2 text-2xl font-bold sm:text-3xl">
            Behavior Analysis
          </h1>

          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Inspect endpoint behavioral windows that feed
            the anomaly detection pipeline.
          </p>
        </div>

        <button
          onClick={loadWindows}
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

      {/* Pipeline explanation */}
      <div className="mb-5 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
        <div className="flex gap-3">
          <Activity
            size={19}
            className="mt-0.5 shrink-0 text-cyan-400"
          />

          <div>
            <p className="text-sm font-medium text-cyan-300">
              Behavioral detection pipeline
            </p>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Endpoint activity is grouped into behavioral
              windows. These windows provide the telemetry
              used by the employee baseline, Isolation Forest,
              policy evaluation, and risk engine.
            </p>
          </div>
        </div>
      </div>

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

      {/* Summary */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
          <p className="text-xs text-slate-500">
            Windows
          </p>

          <p className="mt-1 text-xl font-semibold">
            {statistics.windows}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
          <p className="text-xs text-slate-500">
            Events
          </p>

          <p className="mt-1 text-xl font-semibold">
            {statistics.totalEvents}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
          <p className="text-xs text-slate-500">
            Sensitive Events
          </p>

          <p className="mt-1 text-xl font-semibold text-amber-400">
            {statistics.sensitiveEvents}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
          <p className="text-xs text-slate-500">
            After Hours
          </p>

          <p className="mt-1 text-xl font-semibold text-red-400">
            {statistics.afterHours}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
          <p className="text-xs text-slate-500">
            Devices
          </p>

          <p className="mt-1 text-xl font-semibold">
            {statistics.devices}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        {/* Window list */}
        <section className="overflow-hidden rounded-xl border border-slate-800 bg-[#0a0f18] xl:col-span-2">
          <div className="border-b border-slate-800 px-5 py-4">
            <h2 className="font-semibold">
              Behavioral Windows
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Latest telemetry submitted by registered
              endpoints.
            </p>
          </div>

          {loading ? (
            <div className="flex min-h-[350px] items-center justify-center">
              <div className="text-center">
                <RefreshCw
                  size={25}
                  className="mx-auto animate-spin text-cyan-400"
                />

                <p className="mt-3 text-sm text-slate-500">
                  Loading behavioral windows...
                </p>
              </div>
            </div>
          ) : windows.length === 0 ? (
            <div className="flex min-h-[350px] items-center justify-center p-6">
              <div className="text-center">
                <BarChart3
                  size={32}
                  className="mx-auto text-slate-700"
                />

                <p className="mt-3 text-sm text-slate-400">
                  No behavioral windows found.
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Start the endpoint agent and generate
                  activity to populate this view.
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/70">
              {windows.map((window) => {
                const active =
                  selectedWindow?.id === window.id;

                return (
                  <button
                    key={window.id}
                    onClick={() =>
                      setSelectedWindow(window)
                    }
                    className={`w-full p-5 text-left transition ${
                      active
                        ? "bg-cyan-500/5"
                        : "hover:bg-slate-900/30"
                    }`}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-semibold text-white">
                            Window #{window.id}
                          </span>

                          {window.after_hours && (
                            <span className="rounded-full border border-red-500/20 bg-red-500/10 px-2 py-1 text-[10px] text-red-400">
                              AFTER HOURS
                            </span>
                          )}
                        </div>

                        <p className="mt-1 text-xs text-slate-500">
                          Device #{window.device_id}
                          {" • "}
                          {formatDate(
                            window.window_start
                          )}
                        </p>
                      </div>

                      <span className="text-xs font-medium text-cyan-400">
                        {window.total_events} events
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                      <Metric
                        label="Created"
                        value={window.files_created}
                      />

                      <Metric
                        label="Modified"
                        value={window.files_modified}
                      />

                      <Metric
                        label="Deleted"
                        value={window.files_deleted}
                      />

                      <Metric
                        label="Moved"
                        value={window.files_moved}
                      />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        {/* Detail */}
        <section className="h-fit rounded-xl border border-slate-800 bg-[#0a0f18]">
          <div className="border-b border-slate-800 px-5 py-4">
            <h2 className="font-semibold">
              Window Evidence
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Raw behavioral features for the selected
              window.
            </p>
          </div>

          {!selectedWindow ? (
            <div className="p-6 text-center text-sm text-slate-600">
              Select a behavioral window.
            </div>
          ) : (
            <div className="space-y-5 p-5">
              <div>
                <p className="text-xs text-slate-600">
                  Window
                </p>

                <p className="mt-1 text-lg font-semibold">
                  #{selectedWindow.id}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-600">
                  Observed Activity
                </p>

                <p className="mt-1 text-sm text-cyan-400">
                  {selectedWindow.observed_activity ||
                    "None recorded"}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Metric
                  label="Total Events"
                  value={
                    selectedWindow.total_events
                  }
                />

                <Metric
                  label="Sensitive"
                  value={
                    selectedWindow.sensitive_events
                  }
                />

                <Metric
                  label="Sensitive Ratio"
                  value={`${(
                    selectedWindow.sensitive_ratio *
                    100
                  ).toFixed(1)}%`}
                />

                <Metric
                  label="Activity Rate"
                  value={
                    selectedWindow.activity_rate
                  }
                />

                <Metric
                  label="Data Volume"
                  value={formatBytes(
                    selectedWindow.total_data_volume
                  )}
                />

                <Metric
                  label="Extensions"
                  value={
                    selectedWindow.unique_extensions
                  }
                />

                <Metric
                  label="Directory Breadth"
                  value={
                    selectedWindow.directory_breadth
                  }
                />

                <Metric
                  label="After Hours"
                  value={
                    selectedWindow.after_hours
                      ? "YES"
                      : "NO"
                  }
                />
              </div>

              <div className="border-t border-slate-800 pt-4">
                <div className="flex items-center gap-2">
                  {selectedWindow.after_hours ? (
                    <AlertTriangle
                      size={16}
                      className="text-red-400"
                    />
                  ) : (
                    <ShieldCheck
                      size={16}
                      className="text-emerald-400"
                    />
                  )}

                  <span className="text-xs text-slate-400">
                    Temporal indicator
                  </span>
                </div>

                <p className="mt-2 text-xs leading-5 text-slate-600">
                  After-hours status is one behavioral
                  feature considered by the detection and
                  policy pipeline.
                </p>
              </div>

              <div className="border-t border-slate-800 pt-4">
                <div className="flex items-center gap-2">
                  <Database
                    size={15}
                    className="text-cyan-400"
                  />

                  <span className="text-xs text-slate-400">
                    Session
                  </span>
                </div>

                <p className="mt-2 break-all text-xs text-slate-600">
                  {selectedWindow.session_id ||
                    "No session ID"}
                </p>
              </div>

              <div className="border-t border-slate-800 pt-4">
                <div className="flex items-center gap-2">
                  <Clock3
                    size={15}
                    className="text-slate-500"
                  />

                  <span className="text-xs text-slate-500">
                    Window
                  </span>
                </div>

                <p className="mt-2 text-xs text-slate-600">
                  {formatDate(
                    selectedWindow.window_start
                  )}
                  {" → "}
                  {formatDate(
                    selectedWindow.window_end
                  )}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}