import {
    ArrowLeft,
    AlertTriangle,
    Brain,
    FileWarning,
    ShieldCheck,
    Clock,
    Database,
    Sparkles,
    CheckCircle2,
    XCircle,
} from "lucide-react";

import { useEffect, useState } from "react";
import { getInvestigation, reviewAlert } from "../services/api";

function Section({ icon: Icon, title, children }) {
    return (
        <section className="rounded-xl border border-slate-800 bg-[#0a0f18]">
            <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-4 sm:px-5">
                <div className="rounded-lg bg-cyan-500/10 p-2">
                    <Icon size={17} className="text-cyan-400" />
                </div>

                <h2 className="font-semibold text-white">{title}</h2>
            </div>

            <div className="p-4 sm:p-5">{children}</div>
        </section>
    );
}

export default function Investigation({ alert, onBack, onAlertUpdated }) {
    const [investigation, setInvestigation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [analystNotes, setAnalystNotes] = useState("");
    const [submittingDecision, setSubmittingDecision] = useState(false);
    const [decisionError, setDecisionError] = useState("");
    const [decisionSuccess, setDecisionSuccess] = useState("");

    useEffect(() => {
        if (!alert?.id) {
            return;
        }

        let cancelled = false;

        async function loadInvestigation() {
            try {
                setLoading(true);
                setError("");

                const data = await getInvestigation(alert.id);

                if (!cancelled) {
                    setInvestigation(data);
                }
            } catch (err) {
                if (!cancelled) {
                    setError(
                        err.response?.data?.detail ||
                        "Failed to load investigation data."
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        loadInvestigation();

        return () => {
            cancelled = true;
        };
    }, [alert?.id]);

    async function handleDecision(status) {
        try {
            setSubmittingDecision(true);
            setDecisionError("");
            setDecisionSuccess("");

            const updatedAlert = await reviewAlert(
                alert.id,
                status,
                analystNotes
            );
            onAlertUpdated?.(updatedAlert);

            setInvestigation((current) => {
                if (!current) {
                    return current;
                }

                return {
                    ...current,
                    alert: {
                        ...current.alert,
                        ...updatedAlert,
                    },
                };
            });

            setDecisionSuccess(
                `Alert ${status.toLowerCase()} successfully.`
            );
        } catch (err) {
            setDecisionError(
                err.response?.data?.detail ||
                "Failed to submit analyst decision."
            );
        } finally {
            setSubmittingDecision(false);
        }
    }

    if (!alert) {
        return (
            <div className="flex min-h-[60vh] items-center justify-center">
                <div className="text-center">
                    <AlertTriangle
                        size={32}
                        className="mx-auto text-yellow-400"
                    />

                    <p className="mt-3 text-sm text-slate-400">
                        No alert selected.
                    </p>

                    <button
                        onClick={onBack}
                        className="mt-4 rounded-lg border border-slate-700 px-4 py-2 text-xs text-slate-300 transition hover:bg-slate-800"
                    >
                        Return to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex min-h-[60vh] items-center justify-center">
                <div className="text-center">
                    <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-cyan-400/30 border-t-cyan-400" />

                    <p className="mt-4 text-sm text-slate-400">
                        Loading investigation intelligence...
                    </p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex min-h-[60vh] items-center justify-center">
                <div className="max-w-md text-center">
                    <AlertTriangle
                        size={32}
                        className="mx-auto text-red-400"
                    />

                    <p className="mt-3 text-sm text-red-400">
                        {error}
                    </p>

                    <button
                        onClick={onBack}
                        className="mt-4 rounded-lg border border-slate-700 px-4 py-2 text-xs text-slate-300 transition hover:bg-slate-800"
                    >
                        Return to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    if (!investigation) {
        return (
            <div className="flex min-h-[60vh] items-center justify-center">
                <div className="text-center">
                    <AlertTriangle
                        size={32}
                        className="mx-auto text-yellow-400"
                    />

                    <p className="mt-3 text-sm text-slate-400">
                        Investigation data is unavailable.
                    </p>

                    <button
                        onClick={onBack}
                        className="mt-4 rounded-lg border border-slate-700 px-4 py-2 text-xs text-slate-300 transition hover:bg-slate-800"
                    >
                        Return to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const risk = investigation.risk || {};
    const anomaly = investigation.anomaly || {};
    const window = investigation.window || {};
    const policy = investigation.policy || {};
    const authorization = investigation.authorization;
    const rag = investigation.rag || {};

    const highRisk = risk.risk_level === "HIGH";
    const mediumRisk = risk.risk_level === "MEDIUM";

    const riskColor = highRisk
        ? "text-red-400"
        : mediumRisk
            ? "text-yellow-400"
            : "text-emerald-400";

    const riskBorder = highRisk
        ? "border-red-500/20 bg-red-500/5"
        : mediumRisk
            ? "border-yellow-500/20 bg-yellow-500/5"
            : "border-emerald-500/20 bg-emerald-500/5";

    const employeeCode =
        investigation.employee?.employee_code ||
        `EMP_${String(alert.employee_id).padStart(3, "0")}`;

    const deviceCode =
        investigation.device?.device_code ||
        `DEVICE-${String(alert.device_id).padStart(3, "0")}`;

    return (
        <div className="space-y-5">

            {/* Back */}
            <button
                onClick={onBack}
                className="flex items-center gap-2 text-sm text-slate-500 transition hover:text-white"
            >
                <ArrowLeft size={16} />
                Back to Dashboard
            </button>

            {/* Threat Header */}
            <div
                className={`rounded-xl border p-5 sm:p-6 ${riskBorder}`}
            >
                <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

                    <div className="flex min-w-0 gap-4">

                        <div className="hidden shrink-0 rounded-xl bg-red-500/10 p-4 sm:block">
                            <AlertTriangle
                                size={28}
                                className="text-red-400"
                            />
                        </div>

                        <div className="min-w-0">

                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-xs font-medium uppercase tracking-widest text-cyan-400">
                                    Investigation
                                </span>

                                <span className="text-xs text-slate-600">
                                    #{alert.id}
                                </span>
                            </div>

                            <h1 className="mt-2 text-2xl font-bold text-white sm:text-3xl">
                                Insider Threat Alert
                            </h1>

                            <p className="mt-2 text-sm leading-6 text-slate-400">
                                Employee{" "}
                                <span className="text-white">
                                    {employeeCode}
                                </span>{" "}
                                triggered a behavioral security alert.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">

                        <div>
                            <p className="text-[10px] uppercase tracking-widest text-slate-600">
                                Risk Score
                            </p>

                            <p
                                className={`mt-1 text-4xl font-bold ${riskColor}`}
                            >
                                {risk.risk_score ?? alert.risk_score}
                            </p>
                        </div>

                        <div className="h-12 w-px bg-slate-800" />

                        <div>
                            <p className="text-[10px] uppercase tracking-widest text-slate-600">
                                Severity
                            </p>

                            <span
                                className={`mt-2 inline-flex rounded-md px-3 py-1 text-xs font-bold ${highRisk
                                    ? "bg-red-500/10 text-red-400"
                                    : mediumRisk
                                        ? "bg-yellow-500/10 text-yellow-400"
                                        : "bg-emerald-500/10 text-emerald-400"
                                    }`}
                            >
                                {risk.risk_level || alert.risk_level}
                            </span>
                        </div>

                    </div>
                </div>
            </div>

            {/* Evidence Overview */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

                <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
                    <div className="flex items-center gap-3">
                        <Database
                            size={18}
                            className="text-cyan-400"
                        />

                        <span className="text-xs text-slate-500">
                            Behavioral Window
                        </span>
                    </div>

                    <p className="mt-3 text-xl font-bold text-white">
                        #{alert.behavioral_window_id}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
                    <div className="flex items-center gap-3">
                        <ShieldCheck
                            size={18}
                            className="text-cyan-400"
                        />

                        <span className="text-xs text-slate-500">
                            Device
                        </span>
                    </div>

                    <p className="mt-3 text-xl font-bold text-white">
                        {deviceCode}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
                    <div className="flex items-center gap-3">
                        <Clock
                            size={18}
                            className="text-cyan-400"
                        />

                        <span className="text-xs text-slate-500">
                            Status
                        </span>
                    </div>

                    <p className="mt-3 text-xl font-bold text-yellow-400">
                        {alert.status}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-800 bg-[#0a0f18] p-4">
                    <div className="flex items-center gap-3">
                        <FileWarning
                            size={18}
                            className="text-cyan-400"
                        />

                        <span className="text-xs text-slate-500">
                            Indicators
                        </span>
                    </div>

                    <p className="mt-3 text-xl font-bold text-white">
                        {risk.reasons?.length || alert.reasons?.length || 0}
                    </p>
                </div>

            </div>

            {/* Detection + Policy */}
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">

                {/* Detection Evidence */}
                <Section
                    icon={Brain}
                    title="Detection Evidence"
                >
                    <div className="space-y-4">

                        {/* ML Detection */}
                        <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-4">

                            <div className="flex items-center justify-between gap-4">

                                <div>
                                    <p className="text-[10px] uppercase tracking-widest text-slate-600">
                                        Machine Learning Detection
                                    </p>

                                    <p className="mt-1 text-sm font-medium text-white">
                                        Isolation Forest Analysis
                                    </p>
                                </div>

                                <span
                                    className={`rounded-md px-2.5 py-1 text-[10px] font-bold ${anomaly.is_anomaly
                                        ? "bg-red-500/10 text-red-400"
                                        : "bg-emerald-500/10 text-emerald-400"
                                        }`}
                                >
                                    {anomaly.is_anomaly
                                        ? "ANOMALOUS"
                                        : "NORMAL"}
                                </span>

                            </div>

                            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Anomaly Score
                                    </p>

                                    <p className="mt-1 text-lg font-bold text-red-400">
                                        {Number(
                                            anomaly.anomaly_score ?? 0
                                        ).toFixed(4)}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Raw Model Score
                                    </p>

                                    <p className="mt-1 text-lg font-bold text-slate-300">
                                        {Number(
                                            anomaly.raw_score ?? 0
                                        ).toFixed(4)}
                                    </p>
                                </div>

                            </div>
                        </div>

                        {/* Behavioral Evidence */}
                        <div>
                            <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-cyan-400">
                                Behavioral Evidence
                            </p>

                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Total Events
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {window.total_events ?? 0}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Created
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {window.files_created ?? 0}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Modified
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {window.files_modified ?? 0}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Deleted
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-red-400">
                                        {window.files_deleted ?? 0}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Moved
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {window.files_moved ?? 0}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Sensitive Events
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-yellow-400">
                                        {window.sensitive_events ?? 0}
                                    </p>
                                </div>

                            </div>
                        </div>

                        {/* Activity Metrics */}
                        <div>
                            <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-cyan-400">
                                Activity Metrics
                            </p>

                            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Sensitive Ratio
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-yellow-400">
                                        {(Number(
                                            window.sensitive_ratio ?? 0
                                        ) * 100).toFixed(1)}%
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Data Volume
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {(
                                            Number(
                                                window.total_data_volume ?? 0
                                            ) /
                                            (1024 * 1024)
                                        ).toFixed(1)}{" "}
                                        MB
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        Activity Rate
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-white">
                                        {Number(
                                            window.activity_rate ?? 0
                                        ).toFixed(2)}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-slate-900/30 p-3">
                                    <p className="text-[10px] text-slate-600">
                                        After Hours
                                    </p>

                                    <p
                                        className={`mt-1 text-sm font-semibold ${window.after_hours
                                            ? "text-red-400"
                                            : "text-emerald-400"
                                            }`}
                                    >
                                        {window.after_hours
                                            ? "YES"
                                            : "NO"}
                                    </p>
                                </div>

                            </div>
                        </div>

                        {/* Risk Indicators */}
                        {risk.reasons?.length > 0 && (
                            <div>
                                <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-cyan-400">
                                    Risk Indicators
                                </p>

                                <div className="space-y-3">
                                    {risk.reasons.map((reason, index) => (
                                        <div
                                            key={index}
                                            className="flex gap-3 rounded-lg border border-slate-800 bg-slate-900/30 p-3"
                                        >
                                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />

                                            <p className="text-sm leading-6 text-slate-400">
                                                {reason}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                    </div>
                </Section>

                {/* Policy Analysis */}
                <Section
                    icon={FileWarning}
                    title="Policy Analysis"
                >
                    <div className="space-y-4">

                        <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-4">

                            <div className="flex items-center justify-between gap-4">

                                <div>
                                    <p className="text-sm font-medium text-white">
                                        {policy.role || "Unknown"} Role Policy
                                    </p>

                                    <p className="mt-1 text-xs text-slate-500">
                                        {policy.description ||
                                            "No role-policy description available."}
                                    </p>
                                </div>

                                <span
                                    className={`rounded-md px-2.5 py-1 text-[10px] font-bold ${policy.violated
                                        ? "bg-red-500/10 text-red-400"
                                        : "bg-emerald-500/10 text-emerald-400"
                                        }`}
                                >
                                    {policy.violated
                                        ? "VIOLATED"
                                        : "COMPLIANT"}
                                </span>

                            </div>
                        </div>

                        {policy.violations?.length > 0 ? (
                            <div className="space-y-3">

                                <p className="text-[10px] font-semibold uppercase tracking-widest text-red-400">
                                    Policy Violations
                                </p>

                                {policy.violations.map(
                                    (violation, index) => (
                                        <div
                                            key={index}
                                            className="flex gap-3 rounded-lg border border-red-500/10 bg-red-500/5 p-3"
                                        >
                                            <XCircle
                                                size={17}
                                                className="mt-0.5 shrink-0 text-red-400"
                                            />

                                            <p className="text-sm leading-6 text-slate-400">
                                                {violation}
                                            </p>
                                        </div>
                                    )
                                )}

                            </div>
                        ) : (
                            <div className="flex items-center gap-3 rounded-lg border border-emerald-500/10 bg-emerald-500/5 p-4">
                                <CheckCircle2
                                    size={18}
                                    className="text-emerald-400"
                                />

                                <p className="text-sm text-slate-400">
                                    No role-policy violations were detected.
                                </p>
                            </div>
                        )}

                    </div>
                </Section>

            </div>

            {/* Authorization */}
            <Section
                icon={ShieldCheck}
                title="Authorization Context"
            >
                {authorization ? (
                    <div className="space-y-4">

                        {/* Authorization status */}
                        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4 sm:p-5">

                            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                                <div>
                                    <p className="text-sm font-medium text-white">
                                        Authorization verification
                                    </p>

                                    <p className="mt-1 text-xs leading-5 text-slate-500">
                                        Authorization is evaluated alongside behavioral
                                        anomaly detection and role-policy compliance.
                                    </p>
                                </div>

                                <div
                                    className={`flex items-center gap-2 text-sm font-medium ${authorization.scope_match
                                        ? "text-emerald-400"
                                        : "text-red-400"
                                        }`}
                                >
                                    {authorization.scope_match ? (
                                        <>
                                            <CheckCircle2 size={17} />
                                            Scope Matched
                                        </>
                                    ) : (
                                        <>
                                            <XCircle size={17} />
                                            Scope Not Matched
                                        </>
                                    )}
                                </div>

                            </div>

                            {/* Authorization details */}
                            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Status
                                    </p>

                                    <p className="mt-1 text-sm font-medium text-emerald-400">
                                        {authorization.status}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Allowed Activity
                                    </p>

                                    <p className="mt-1 text-sm text-white">
                                        {authorization.allowed_activity}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Observed Activity
                                    </p>

                                    <p className="mt-1 text-sm text-white">
                                        {authorization.observed_activity}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Authorized By
                                    </p>

                                    <p className="mt-1 text-sm text-white">
                                        {authorization.authorized_by}
                                    </p>
                                </div>

                            </div>

                            {/* Reason */}
                            <div className="mt-3 rounded-lg bg-[#070b12] p-3">
                                <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                    Authorization Reason
                                </p>

                                <p className="mt-1 text-sm leading-6 text-slate-300">
                                    {authorization.reason}
                                </p>
                            </div>

                            {/* Validity */}
                            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Valid From
                                    </p>

                                    <p className="mt-1 text-xs text-slate-300">
                                        {new Date(
                                            authorization.start_time
                                        ).toLocaleString()}
                                    </p>
                                </div>

                                <div className="rounded-lg bg-[#070b12] p-3">
                                    <p className="text-[10px] uppercase tracking-wider text-slate-600">
                                        Valid Until
                                    </p>

                                    <p className="mt-1 text-xs text-slate-300">
                                        {new Date(
                                            authorization.end_time
                                        ).toLocaleString()}
                                    </p>
                                </div>

                            </div>

                        </div>

                        {/* Important interpretation */}
                        <div className="rounded-xl border border-cyan-500/10 bg-cyan-500/5 p-4">

                            <div className="flex gap-3">

                                <ShieldCheck
                                    size={18}
                                    className="mt-0.5 shrink-0 text-cyan-400"
                                />

                                <div>
                                    <p className="text-sm font-medium text-cyan-300">
                                        Authorization interpretation
                                    </p>

                                    <p className="mt-1 text-xs leading-6 text-slate-400">
                                        The authorization exception is evaluated separately
                                        from the employee's normal role policy and ML anomaly
                                        score. A matched authorization does not disable
                                        monitoring or anomaly detection.
                                    </p>
                                </div>

                            </div>

                        </div>

                    </div>
                ) : (
                    <div className="flex items-center gap-3 rounded-lg border border-yellow-500/10 bg-yellow-500/5 p-4">

                        <AlertTriangle
                            size={18}
                            className="text-yellow-400"
                        />

                        <p className="text-sm text-slate-400">
                            No active authorization exception was identified for
                            this alert.
                        </p>

                    </div>
                )}
            </Section>

            {/* RAG Hero */}
            <section className="overflow-hidden rounded-xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 via-[#0a0f18] to-[#0a0f18]">

                <div className="border-b border-cyan-500/10 px-4 py-5 sm:px-6">

                    <div className="flex items-center gap-3">

                        <div className="rounded-xl bg-cyan-500/10 p-3">
                            <Sparkles
                                size={21}
                                className="text-cyan-400"
                            />
                        </div>

                        <div>

                            <div className="flex items-center gap-2">

                                <h2 className="font-semibold text-white">
                                    RAG Threat Intelligence
                                </h2>

                                <span className="rounded-full bg-cyan-500/10 px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-cyan-400">
                                    AI Assisted
                                </span>

                            </div>

                            <p className="mt-1 text-xs text-slate-500">
                                Contextual explanation using organizational security policies
                            </p>

                        </div>

                    </div>

                </div>

                <div className="grid grid-cols-1 gap-6 p-4 sm:p-6 xl:grid-cols-3">

                    {/* Explanation */}
                    <div className="xl:col-span-2">

                        <p className="text-[10px] font-semibold uppercase tracking-widest text-cyan-400">
                            Threat Explanation
                        </p>

                        <div className="mt-3 rounded-xl border border-slate-800 bg-black/10 p-5">

                            {rag.threat_explanation ? (
                                <p className="whitespace-pre-line text-sm leading-7 text-slate-400">
                                    {rag.threat_explanation}
                                </p>
                            ) : (
                                <p className="text-sm leading-7 text-slate-500">
                                    No RAG threat explanation is available for this
                                    investigation.
                                </p>
                            )}

                        </div>

                    </div>

                    {/* Policies */}
                    <div>

                        <p className="text-[10px] font-semibold uppercase tracking-widest text-cyan-400">
                            Retrieved Policies
                        </p>

                        <div className="mt-3 space-y-2">

                            {rag.retrieved_policies?.length > 0 ? (
                                rag.retrieved_policies.map(
                                    (policyItem, index) => (
                                        <div
                                            key={`${policyItem.title}-${index}`}
                                            className="rounded-lg border border-slate-800 bg-black/10 p-3"
                                        >

                                            <p className="text-xs font-medium text-slate-300">
                                                {policyItem.title}
                                            </p>

                                            <p className="mt-1 text-[10px] text-slate-600">
                                                Source: {policyItem.source}
                                            </p>

                                            <p className="mt-2 text-[11px] leading-5 text-slate-500">
                                                {policyItem.content}
                                            </p>

                                            <p className="mt-2 text-[10px] text-cyan-500/70">
                                                Retrieval distance:{" "}
                                                {Number(
                                                    policyItem.distance ?? 0
                                                ).toFixed(3)}
                                            </p>

                                        </div>
                                    )
                                )
                            ) : (
                                <p className="text-xs text-slate-500">
                                    No relevant security policies were retrieved.
                                </p>
                            )}

                        </div>

                    </div>

                </div>

            </section>

            {/* Analyst Decision */}
            <Section
                icon={ShieldCheck}
                title="Analyst Decision"
            >
                <div className="space-y-4">

                    <textarea
                        value={analystNotes}
                        onChange={(event) => {
                            setAnalystNotes(event.target.value);
                            setDecisionError("");
                        }}
                        placeholder="Enter analyst notes..."
                        rows={4}
                        disabled={submittingDecision}
                        className="w-full resize-none rounded-lg border border-slate-800 bg-[#070b12] p-4 text-sm text-white outline-none placeholder:text-slate-600 focus:border-cyan-500/40 disabled:cursor-not-allowed disabled:opacity-50"
                    />

                    {decisionError && (
                        <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
                            {decisionError}
                        </div>
                    )}

                    {decisionSuccess && (
                        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-4 py-3 text-sm text-emerald-400">
                            {decisionSuccess}
                        </div>
                    )}

                    <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">

                        <button
                            onClick={() => handleDecision("DISMISSED")}
                            disabled={submittingDecision}
                            className="flex items-center justify-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 px-5 py-2.5 text-sm font-medium text-red-400 transition hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <XCircle size={17} />

                            {submittingDecision
                                ? "Submitting..."
                                : "Reject Alert"}
                        </button>

                        <button
                            onClick={() => handleDecision("CONFIRMED")}
                            disabled={submittingDecision}
                            className="flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <CheckCircle2 size={17} />

                            {submittingDecision
                                ? "Submitting..."
                                : "Approve Alert"}
                        </button>

                    </div>

                </div>
            </Section>

        </div>
    );
}