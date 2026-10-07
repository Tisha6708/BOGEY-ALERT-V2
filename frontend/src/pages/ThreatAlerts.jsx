import { useEffect, useMemo, useRef, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileSearch,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from "lucide-react";

import { getAlerts } from "../services/api";


export default function ThreatAlerts({ onInvestigate }) {
  // =========================================================
  // STATE
  // =========================================================

  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [connectionStatus, setConnectionStatus] =
    useState("CONNECTING");

  const websocketRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const stoppedRef = useRef(false);


  // =========================================================
  // LOAD ALERTS FROM REST API
  // =========================================================

  const loadAlerts = async (showRefreshState = false) => {
    try {
      if (showRefreshState) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const data = await getAlerts();

      setAlerts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(
        "[ThreatAlerts] Failed to load alerts:",
        error
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  // =========================================================
  // INITIAL ALERT LOAD
  // =========================================================

  useEffect(() => {
    loadAlerts();
  }, []);


  // =========================================================
  // REAL-TIME WEBSOCKET CONNECTION
  // =========================================================

  useEffect(() => {
    stoppedRef.current = false;

    const apiBaseUrl =
      import.meta.env.VITE_API_BASE_URL ||
      "http://127.0.0.1:8000";

    const websocketBaseUrl = apiBaseUrl
      .replace(/^http:/, "ws:")
      .replace(/^https:/, "wss:")
      .replace(/\/$/, "");

    const websocketUrl =
      `${websocketBaseUrl}/ws/alerts`;


    const connectWebSocket = () => {
      if (stoppedRef.current) {
        return;
      }

      setConnectionStatus("CONNECTING");

      console.log(
        "[WebSocket] Connecting to:",
        websocketUrl
      );

      const websocket =
        new WebSocket(websocketUrl);

      websocketRef.current = websocket;


      // -------------------------------------------------------
      // CONNECTED
      // -------------------------------------------------------

      websocket.onopen = () => {
        console.log(
          "[WebSocket] Connected to alert stream."
        );

        setConnectionStatus("CONNECTED");
      };


      // -------------------------------------------------------
      // MESSAGE RECEIVED
      // -------------------------------------------------------

      websocket.onmessage = (event) => {
        try {
          const message =
            JSON.parse(event.data);

          console.log(
            "[WebSocket] Message received:",
            message
          );


          // Ignore connection/heartbeat messages.
          if (
            message?.type !==
              "SECURITY_ALERT" ||
            !message.alert
          ) {
            return;
          }


          const incomingAlert =
            message.alert;


          setAlerts((currentAlerts) => {
            const existingIndex =
              currentAlerts.findIndex(
                (alert) =>
                  alert.id ===
                  incomingAlert.id
              );


            // -------------------------------------------------
            // NEW ALERT
            // -------------------------------------------------

            if (existingIndex === -1) {
              return [
                incomingAlert,
                ...currentAlerts,
              ];
            }


            // -------------------------------------------------
            // EXISTING ALERT UPDATED
            // -------------------------------------------------

            const updatedAlerts = [
              ...currentAlerts,
            ];

            updatedAlerts[existingIndex] =
              incomingAlert;

            return updatedAlerts;
          });
        } catch (error) {
          console.error(
            "[WebSocket] Invalid message:",
            error
          );
        }
      };


      // -------------------------------------------------------
      // ERROR
      // -------------------------------------------------------

      websocket.onerror = (error) => {
        console.error(
          "[WebSocket] Connection error:",
          error
        );

        setConnectionStatus(
          "DISCONNECTED"
        );
      };


      // -------------------------------------------------------
      // CLOSED
      // -------------------------------------------------------

      websocket.onclose = () => {
        console.log(
          "[WebSocket] Connection closed."
        );

        setConnectionStatus(
          "DISCONNECTED"
        );

        websocketRef.current = null;


        // Automatically reconnect after 3 seconds.
        if (!stoppedRef.current) {
          reconnectTimerRef.current =
            setTimeout(() => {
              connectWebSocket();
            }, 3000);
        }
      };
    };


    connectWebSocket();


    // ---------------------------------------------------------
    // CLEANUP
    // ---------------------------------------------------------

    return () => {
      stoppedRef.current = true;

      if (reconnectTimerRef.current) {
        clearTimeout(
          reconnectTimerRef.current
        );

        reconnectTimerRef.current = null;
      }

      if (websocketRef.current) {
        websocketRef.current.close();

        websocketRef.current = null;
      }
    };
  }, []);


  // =========================================================
  // FILTER ALERTS
  // =========================================================

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const statusMatches =
        statusFilter === "ALL" ||
        alert.status === statusFilter;

      const riskMatches =
        riskFilter === "ALL" ||
        alert.risk_level === riskFilter;

      return (
        statusMatches &&
        riskMatches
      );
    });
  }, [
    alerts,
    statusFilter,
    riskFilter,
  ]);


  // =========================================================
  // ALERT COUNTS
  // =========================================================

  const totalAlerts = alerts.length;

  const highRiskCount = alerts.filter(
    (alert) =>
      alert.risk_level === "HIGH"
  ).length;

  const mediumRiskCount = alerts.filter(
    (alert) =>
      alert.risk_level === "MEDIUM"
  ).length;

  const pendingCount = alerts.filter(
    (alert) =>
      alert.status === "PENDING"
  ).length;


  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (value) => {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  };


  // =========================================================
  // RISK BADGE
  // =========================================================

  const getRiskBadge = (riskLevel) => {
    if (riskLevel === "HIGH") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-1 text-xs font-semibold text-red-300">
          <ShieldAlert size={13} />
          HIGH
        </span>
      );
    }

    if (riskLevel === "MEDIUM") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-yellow-400/30 bg-yellow-500/10 px-2.5 py-1 text-xs font-semibold text-yellow-300">
          <AlertTriangle size={13} />
          MEDIUM
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-green-400/30 bg-green-500/10 px-2.5 py-1 text-xs font-semibold text-green-300">
        <CheckCircle2 size={13} />
        LOW
      </span>
    );
  };


  // =========================================================
  // STATUS BADGE
  // =========================================================

  const getStatusBadge = (status) => {
    if (status === "PENDING") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-orange-400/30 bg-orange-500/10 px-2.5 py-1 text-xs font-semibold text-orange-300">
          <Clock3 size={13} />
          PENDING
        </span>
      );
    }

    if (status === "UNDER_REVIEW") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-blue-400/30 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-300">
          <FileSearch size={13} />
          UNDER REVIEW
        </span>
      );
    }

    if (status === "CONFIRMED") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-red-400/30 bg-red-500/10 px-2.5 py-1 text-xs font-semibold text-red-300">
          <ShieldAlert size={13} />
          CONFIRMED
        </span>
      );
    }

    if (status === "DISMISSED") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-gray-400/30 bg-gray-500/10 px-2.5 py-1 text-xs font-semibold text-gray-300">
          <XCircle size={13} />
          DISMISSED
        </span>
      );
    }

    return (
      <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-gray-300">
        {status || "UNKNOWN"}
      </span>
    );
  };


  // =========================================================
  // WEBSOCKET STATUS UI
  // =========================================================

  const getConnectionStatus = () => {
    if (connectionStatus === "CONNECTED") {
      return (
        <div className="flex items-center gap-2 rounded-full border border-green-400/20 bg-green-500/10 px-3 py-1.5">
          <span className="h-2 w-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]" />
          <span className="text-xs font-medium text-green-300">
            LIVE
          </span>
        </div>
      );
    }

    if (connectionStatus === "CONNECTING") {
      return (
        <div className="flex items-center gap-2 rounded-full border border-yellow-400/20 bg-yellow-500/10 px-3 py-1.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-yellow-400" />
          <span className="text-xs font-medium text-yellow-300">
            CONNECTING
          </span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 rounded-full border border-red-400/20 bg-red-500/10 px-3 py-1.5">
        <span className="h-2 w-2 rounded-full bg-red-400" />
        <span className="text-xs font-medium text-red-300">
          DISCONNECTED
        </span>
      </div>
    );
  };


  // =========================================================
  // LOADING STATE
  // =========================================================

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="flex items-center gap-3 text-gray-400">
          <RefreshCw
            size={18}
            className="animate-spin"
          />
          Loading security alerts...
        </div>
      </div>
    );
  }


  // =========================================================
  // MAIN UI
  // =========================================================

  return (
    <div className="space-y-6">


      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-white">
              Threat Alerts
            </h1>

            {getConnectionStatus()}
          </div>

          <p className="mt-1 text-sm text-gray-400">
            Monitor and investigate detected
            insider-threat activity.
          </p>
        </div>


        <button
          type="button"
          onClick={() =>
            loadAlerts(true)
          }
          disabled={refreshing}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            size={16}
            className={
              refreshing
                ? "animate-spin"
                : ""
            }
          />

          Refresh
        </button>
      </div>


      {/* =====================================================
          STAT CARDS
      ===================================================== */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        {/* Total */}

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Total Alerts
            </span>

            <AlertTriangle
              size={18}
              className="text-gray-400"
            />
          </div>

          <p className="mt-3 text-2xl font-semibold text-white">
            {totalAlerts}
          </p>
        </div>


        {/* High */}

        <div className="rounded-xl border border-red-400/10 bg-red-500/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              High Risk
            </span>

            <ShieldAlert
              size={18}
              className="text-red-400"
            />
          </div>

          <p className="mt-3 text-2xl font-semibold text-red-300">
            {highRiskCount}
          </p>
        </div>


        {/* Medium */}

        <div className="rounded-xl border border-yellow-400/10 bg-yellow-500/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Medium Risk
            </span>

            <AlertTriangle
              size={18}
              className="text-yellow-400"
            />
          </div>

          <p className="mt-3 text-2xl font-semibold text-yellow-300">
            {mediumRiskCount}
          </p>
        </div>


        {/* Pending */}

        <div className="rounded-xl border border-orange-400/10 bg-orange-500/[0.03] p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Pending Review
            </span>

            <Clock3
              size={18}
              className="text-orange-400"
            />
          </div>

          <p className="mt-3 text-2xl font-semibold text-orange-300">
            {pendingCount}
          </p>
        </div>

      </div>


      {/* =====================================================
          FILTERS
      ===================================================== */}

      <div className="flex flex-col gap-4 rounded-xl border border-white/10 bg-white/[0.03] p-4 lg:flex-row lg:items-center lg:justify-between">

        {/* Status filters */}

        <div className="flex flex-wrap items-center gap-2">

          <span className="mr-1 text-xs font-medium uppercase tracking-wide text-gray-500">
            Status
          </span>

          {[
            "ALL",
            "PENDING",
            "UNDER_REVIEW",
            "CONFIRMED",
            "DISMISSED",
          ].map((status) => (
            <button
              key={status}
              type="button"
              onClick={() =>
                setStatusFilter(status)
              }
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                statusFilter === status
                  ? "bg-white text-black"
                  : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
              }`}
            >
              {status === "UNDER_REVIEW"
                ? "UNDER REVIEW"
                : status}
            </button>
          ))}

        </div>


        {/* Risk filters */}

        <div className="flex flex-wrap items-center gap-2">

          <span className="mr-1 text-xs font-medium uppercase tracking-wide text-gray-500">
            Risk
          </span>

          {[
            "ALL",
            "HIGH",
            "MEDIUM",
            "LOW",
          ].map((risk) => (
            <button
              key={risk}
              type="button"
              onClick={() =>
                setRiskFilter(risk)
              }
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                riskFilter === risk
                  ? "bg-white text-black"
                  : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
              }`}
            >
              {risk}
            </button>
          ))}

        </div>

      </div>


      {/* =====================================================
          DESKTOP TABLE
      ===================================================== */}

      <div className="hidden overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] lg:block">

        <div className="overflow-x-auto">

          <table className="w-full text-left">

            <thead className="border-b border-white/10 bg-white/[0.02]">

              <tr>

                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Alert
                </th>

                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Employee
                </th>

                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Risk
                </th>

                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Status
                </th>

                <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Created
                </th>

                <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Action
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-white/5">

              {filteredAlerts.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-sm text-gray-500"
                  >
                    No alerts match the selected
                    filters.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className="transition hover:bg-white/[0.025]"
                  >

                    {/* Alert */}

                    <td className="px-5 py-4">

                      <div className="flex items-center gap-3">

                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/10">
                          <ShieldAlert
                            size={17}
                            className="text-red-400"
                          />
                        </div>

                        <div>
                          <p className="font-medium text-white">
                            Alert #{alert.id}
                          </p>

                          <p className="mt-0.5 text-xs text-gray-500">
                            Window #
                            {
                              alert.behavioral_window_id
                            }
                          </p>
                        </div>

                      </div>

                    </td>


                    {/* Employee */}

                    <td className="px-5 py-4">

                      <p className="text-sm text-gray-200">
                        Employee #
                        {alert.employee_id}
                      </p>

                      <p className="mt-0.5 text-xs text-gray-500">
                        Device #
                        {alert.device_id}
                      </p>

                    </td>


                    {/* Risk */}

                    <td className="px-5 py-4">

                      <div className="space-y-1">

                        {getRiskBadge(
                          alert.risk_level
                        )}

                        <p className="text-xs text-gray-500">
                          Score:{" "}
                          <span className="text-gray-300">
                            {alert.risk_score}
                          </span>
                        </p>

                      </div>

                    </td>


                    {/* Status */}

                    <td className="px-5 py-4">
                      {getStatusBadge(
                        alert.status
                      )}
                    </td>


                    {/* Created */}

                    <td className="px-5 py-4">

                      <p className="text-sm text-gray-300">
                        {formatDate(
                          alert.created_at
                        )}
                      </p>

                    </td>


                    {/* Action */}

                    <td className="px-5 py-4 text-right">

                      <button
                        type="button"
                        onClick={() =>
                          onInvestigate?.(
                            alert
                          )
                        }
                        className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-gray-200 transition hover:bg-white/10 hover:text-white"
                      >
                        <FileSearch
                          size={15}
                        />
                        Investigate
                      </button>

                    </td>

                  </tr>
                ))
              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* =====================================================
          MOBILE CARDS
      ===================================================== */}

      <div className="space-y-3 lg:hidden">

        {filteredAlerts.length === 0 ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.03] px-5 py-12 text-center text-sm text-gray-500">
            No alerts match the selected
            filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-xl border border-white/10 bg-white/[0.03] p-4"
            >

              {/* Card header */}

              <div className="flex items-start justify-between gap-3">

                <div className="flex items-center gap-3">

                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
                    <ShieldAlert
                      size={18}
                      className="text-red-400"
                    />
                  </div>

                  <div>
                    <p className="font-medium text-white">
                      Alert #{alert.id}
                    </p>

                    <p className="text-xs text-gray-500">
                      Window #
                      {
                        alert.behavioral_window_id
                      }
                    </p>
                  </div>

                </div>

                {getRiskBadge(
                  alert.risk_level
                )}

              </div>


              {/* Card details */}

              <div className="mt-4 grid grid-cols-2 gap-3">

                <div>
                  <p className="text-xs text-gray-500">
                    Employee
                  </p>

                  <p className="mt-1 text-sm text-gray-200">
                    #{alert.employee_id}
                  </p>
                </div>


                <div>
                  <p className="text-xs text-gray-500">
                    Device
                  </p>

                  <p className="mt-1 text-sm text-gray-200">
                    #{alert.device_id}
                  </p>
                </div>


                <div>
                  <p className="text-xs text-gray-500">
                    Risk Score
                  </p>

                  <p className="mt-1 text-sm font-medium text-gray-200">
                    {alert.risk_score}
                  </p>
                </div>


                <div>
                  <p className="text-xs text-gray-500">
                    Status
                  </p>

                  <div className="mt-1">
                    {getStatusBadge(
                      alert.status
                    )}
                  </div>
                </div>

              </div>


              {/* Created */}

              <div className="mt-4 border-t border-white/5 pt-3">

                <p className="text-xs text-gray-500">
                  Created
                </p>

                <p className="mt-1 text-sm text-gray-300">
                  {formatDate(
                    alert.created_at
                  )}
                </p>

              </div>


              {/* Investigate */}

              <button
                type="button"
                onClick={() =>
                  onInvestigate?.(
                    alert
                  )
                }
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:bg-white/10 hover:text-white"
              >
                <FileSearch size={16} />
                Investigate Alert
              </button>

            </div>
          ))
        )}

      </div>


      {/* =====================================================
          LIVE MONITORING MESSAGE
      ===================================================== */}

      {connectionStatus ===
        "CONNECTED" && (
        <div className="flex items-center gap-2 rounded-lg border border-green-400/10 bg-green-500/[0.03] px-4 py-3 text-xs text-gray-400">
          <span className="h-1.5 w-1.5 rounded-full bg-green-400" />

          Real-time monitoring is active.
          New security alerts will appear
          automatically.
        </div>
      )}

    </div>
  );
}