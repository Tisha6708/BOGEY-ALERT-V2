import { useEffect, useMemo, useState } from "react";

import {
  ShieldAlert,
  AlertTriangle,
  Activity,
  Monitor,
  RefreshCw,
  FileSearch,
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/TopBar";
import StatCard from "./components/StatCard";
import AlertCard from "./components/AlertCard";

import Investigation from "./pages/Investigation";
import ThreatAlerts from "./pages/ThreatAlerts";
import Exceptions from "./pages/Exceptions";
import BehaviorAnalysis from "./pages/BehaviorAnalysis";
import Endpoints from "./pages/Endpoints";

import { getAlerts } from "./services/api";

function App() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [activePage, setActivePage] =
    useState("dashboard");

  const [selectedAlert, setSelectedAlert] =
    useState(null);

  async function loadAlerts() {
    try {
      setLoading(true);
      setError("");

      const data = await getAlerts();

      setAlerts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(
        "Failed to load alerts:",
        err
      );

      setError(
        "Unable to connect to the BOGEY-ALERT backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, []);

  const statistics = useMemo(() => {
    const high = alerts.filter(
      (alert) => alert.risk_level === "HIGH"
    ).length;

    const medium = alerts.filter(
      (alert) => alert.risk_level === "MEDIUM"
    ).length;

    const pending = alerts.filter(
      (alert) => alert.status === "PENDING"
    ).length;

    return {
      total: alerts.length,
      high,
      medium,
      pending,
    };
  }, [alerts]);

  function handleNavigate(page) {
    setSelectedAlert(null);
    setActivePage(page);
  }

  function handleInvestigate(alert) {
    setSelectedAlert(alert);
    setActivePage("investigations");
  }

  function handleAlertUpdated(updatedAlert) {
    setAlerts((currentAlerts) =>
      currentAlerts.map((alert) =>
        alert.id === updatedAlert.id
          ? updatedAlert
          : alert
      )
    );

    setSelectedAlert(updatedAlert);
  }

  function renderDashboard() {
    return (
      <>
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 sm:mb-8 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400">
              Command Center
            </p>

            <h1 className="mt-2 text-2xl font-bold sm:text-3xl">
              Threat Overview
            </h1>

            <p className="mt-2 max-w-2xl text-sm text-slate-500">
              Real-time employee behavior and insider
              threat monitoring.
            </p>
          </div>

          <button
            onClick={loadAlerts}
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

        {/* Stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Alerts"
            value={statistics.total}
            description="Detected security events"
            icon={ShieldAlert}
          />

          <StatCard
            label="High Risk"
            value={statistics.high}
            description="Requires immediate review"
            icon={AlertTriangle}
            danger={statistics.high > 0}
          />

          <StatCard
            label="Medium Risk"
            value={statistics.medium}
            description="Requires investigation"
            icon={Activity}
          />

          <StatCard
            label="Pending Review"
            value={statistics.pending}
            description="Awaiting analyst decision"
            icon={Monitor}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/5 p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle
                size={18}
                className="text-red-400"
              />

              <div>
                <p className="text-sm font-medium text-red-400">
                  Backend Connection Error
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {error}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main content */}
        <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
          {/* Alerts */}
          <section className="rounded-xl border border-slate-800 bg-[#0a0f18] xl:col-span-2">
            <div className="flex flex-col gap-3 border-b border-slate-800 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
              <div>
                <h2 className="font-semibold">
                  Active Threats
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Live alerts from the detection pipeline
                </p>
              </div>

              <span className="w-fit rounded-full bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400">
                {statistics.high} High Risk
              </span>
            </div>

            <div className="space-y-4 p-4 sm:p-5">
              {loading && alerts.length === 0 ? (
                <div className="flex items-center justify-center py-16">
                  <div className="text-center">
                    <RefreshCw
                      size={24}
                      className="mx-auto animate-spin text-cyan-400"
                    />

                    <p className="mt-3 text-sm text-slate-500">
                      Loading security alerts...
                    </p>
                  </div>
                </div>
              ) : alerts.length === 0 ? (
                <div className="py-16 text-center">
                  <ShieldAlert
                    size={32}
                    className="mx-auto text-slate-700"
                  />

                  <p className="mt-3 text-sm text-slate-500">
                    No security alerts detected.
                  </p>
                </div>
              ) : (
                alerts.map((alert) => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    onInvestigate={handleInvestigate}
                  />
                ))
              )}
            </div>
          </section>

          {/* Pipeline */}
          <section className="h-fit rounded-xl border border-slate-800 bg-[#0a0f18]">
            <div className="border-b border-slate-800 px-4 py-4 sm:px-5">
              <h2 className="font-semibold">
                Detection Pipeline
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                Current system status
              </p>
            </div>

            <div className="space-y-4 p-4 sm:p-5">
              {[
                ["Endpoint Agent", "Operational"],
                ["Policy Engine", "Operational"],
                ["ML Detection", "Operational"],
                ["Risk Engine", "Operational"],
                ["RAG Engine", "Operational"],
                ["AI Assistant", "Operational"],
              ].map(([name, status]) => (
                <div
                  key={name}
                  className="flex items-center justify-between gap-3"
                >
                  <span className="text-sm text-slate-400">
                    {name}
                  </span>

                  <div className="flex shrink-0 items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                    <span className="text-xs text-emerald-400">
                      {status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </>
    );
  }

  function renderCurrentPage() {
    switch (activePage) {
      case "dashboard":
        return renderDashboard();

      case "alerts":
        return (
          <ThreatAlerts
            onInvestigate={handleInvestigate}
          />
        );

      case "exceptions":
        return <Exceptions />;

      case "behavior":
        return <BehaviorAnalysis />;

      case "endpoints":
        return <Endpoints />;

      case "investigations":
        return (
          <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-8 text-center">
            <FileSearch
              size={32}
              className="mx-auto text-cyan-400"
            />

            <h1 className="mt-4 text-xl font-semibold">
              Investigations
            </h1>

            <p className="mx-auto mt-2 max-w-lg text-sm text-slate-500">
              Select an alert from the Dashboard or
              Threat Alerts page to open its full
              investigation.
            </p>
          </div>
        );

      default:
        return renderDashboard();
    }
  }

  return (
    <div className="min-h-screen bg-[#070b12] text-white">
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
      />

      <Topbar />

      <main className="pt-20 lg:ml-64">
        <div className="p-4 sm:p-6 lg:p-8">
          {selectedAlert ? (
            <Investigation
              alert={selectedAlert}
              onBack={() => {
                setSelectedAlert(null);
                setActivePage("alerts");
              }}
              onAlertUpdated={handleAlertUpdated}
            />
          ) : (
            renderCurrentPage()
          )}
        </div>
      </main>
    </div>
  );
}

export default App;