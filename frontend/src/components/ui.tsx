import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink as ExternalIcon,
  Inbox,
  Loader2,
  XCircle,
} from "lucide-react";
import type { ScoreStatus } from "../api/types";
import { formatScore, humanize } from "../lib/format";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-navy-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-slate-600">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function Card({ title, actions, children, className = "", bodyClass = "p-4" }: {
  title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; bodyClass?: string;
}) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
          {title && <h2 className="text-sm font-semibold text-navy-800">{title}</h2>}
          {actions}
        </header>
      )}
      <div className={bodyClass}>{children}</div>
    </section>
  );
}

export function StatTile({ label, value, icon, to }: { label: string; value: ReactNode; icon?: ReactNode; to?: string }) {
  const body = (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-navy-200">
      {icon && <div className="rounded-lg bg-navy-50 p-2 text-navy-700">{icon}</div>}
      <div className="min-w-0">
        <div className="text-2xl font-semibold text-navy-900">{value}</div>
        <div className="truncate text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      </div>
    </div>
  );
  return to ? <Link to={to} className="block">{body}</Link> : body;
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> {label}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-800">
      <AlertCircle className="h-5 w-5" aria-hidden />
      <p>{message}</p>
      <p className="text-xs text-red-700">Check that the backend API is running on port 8000.</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-1 rounded-md border border-red-300 bg-white px-3 py-1 text-xs font-medium hover:bg-red-100">
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = "No matching records." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 py-10 text-sm text-slate-500">
      <Inbox className="h-6 w-6" aria-hidden /> {message}
    </div>
  );
}

/** Wraps a data section with the standard loading / error / empty states. */
export function AsyncBlock<T>({ state, children, isEmpty }: {
  state: { data: T | null; loading: boolean; error: string | null; reload?: () => void };
  children: (data: T) => ReactNode;
  isEmpty?: (data: T) => boolean;
}) {
  if (state.loading && !state.data) return <Loading />;
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />;
  if (!state.data) return null;
  if (isEmpty?.(state.data)) return <EmptyState />;
  return <>{children(state.data)}</>;
}

const ROLE_STYLES: Record<string, string> = {
  diagnostic: "bg-sky-50 text-sky-800 ring-sky-200",
  prognostic: "bg-violet-50 text-violet-800 ring-violet-200",
  predictive: "bg-teal-50 text-teal-800 ring-teal-200",
  risk: "bg-amber-50 text-amber-800 ring-amber-200",
  monitoring: "bg-slate-100 text-slate-700 ring-slate-200",
};

export function Badge({ children, className = "bg-slate-100 text-slate-700 ring-slate-200", title }: {
  children: ReactNode; className?: string; title?: string;
}) {
  return (
    <span title={title} className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${className}`}>
      {children}
    </span>
  );
}

export function RoleBadge({ role }: { role: string }) {
  return <Badge className={ROLE_STYLES[role] ?? undefined}>{humanize(role)}</Badge>;
}

const SOURCE_STATUS_STYLES: Record<string, { cls: string; hint: string }> = {
  curated_literature: { cls: "bg-emerald-50 text-emerald-800 ring-emerald-200", hint: "Manually curated from cited literature" },
  database_annotation: { cls: "bg-blue-50 text-blue-800 ring-blue-200", hint: "Derived from a public database annotation" },
  computational_prediction: { cls: "bg-purple-50 text-purple-800 ring-purple-200", hint: "Computational prediction, not experimental evidence" },
  synthetic_demo: { cls: "bg-orange-50 text-orange-800 ring-orange-300", hint: "Synthetic demonstration record, not scientific evidence" },
  pending_curation: { cls: "bg-slate-100 text-slate-700 ring-slate-300", hint: "Association recorded; supporting evidence not yet curated" },
};

export function SourceStatusBadge({ status }: { status: string }) {
  const s = SOURCE_STATUS_STYLES[status];
  return <Badge className={s?.cls} title={s?.hint}>{humanize(status)}</Badge>;
}

const SCORE_STATUS: Record<ScoreStatus, { icon: typeof CheckCircle2; color: string; label: string; hint: string }> = {
  complete: { icon: CheckCircle2, color: "text-status-good", label: "Complete", hint: "All four components observed" },
  provisional: { icon: AlertTriangle, color: "text-amber-600", label: "Provisional", hint: "Some components unknown; renormalised over observed weight" },
  insufficient: { icon: XCircle, color: "text-status-critical", label: "Insufficient", hint: "Too little evidence metadata to compute a score" },
};

/** Status is always shown as icon + label, never colour alone. */
export function ScoreStatusLabel({ status }: { status: ScoreStatus | null | undefined }) {
  if (!status) return <span className="text-xs text-slate-400">not scored</span>;
  const s = SCORE_STATUS[status];
  const Icon = s.icon;
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-700" title={s.hint}>
      <Icon className={`h-3.5 w-3.5 ${s.color}`} aria-hidden /> {s.label}
    </span>
  );
}

export function ScorePill({ score, status }: { score: number | null | undefined; status?: ScoreStatus | null }) {
  const dashed = status === "provisional" ? "border-dashed" : "border-solid";
  return (
    <span
      className={`tabular inline-flex min-w-12 justify-center rounded-md border ${dashed} border-navy-200 bg-navy-50 px-1.5 py-0.5 text-xs font-semibold text-navy-800`}
      title={status === "provisional" ? "Provisional score (incomplete evidence)" : undefined}
    >
      {formatScore(score)}
      {status === "provisional" && <span aria-label="provisional">*</span>}
    </span>
  );
}

export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-teal-brand hover:underline">
      {children}
      <ExternalIcon className="h-3 w-3" aria-hidden />
      <span className="sr-only">(opens in new tab)</span>
    </a>
  );
}

export function Pagination({ page, pages, total, onPage }: { page: number; pages: number; total: number; onPage: (p: number) => void }) {
  return (
    <div className="flex items-center justify-between gap-2 border-t border-slate-100 px-4 py-3 text-sm text-slate-600">
      <span className="tabular">{total} record{total === 1 ? "" : "s"}</span>
      <div className="flex items-center gap-2">
        <button aria-label="Previous page" disabled={page <= 1} onClick={() => onPage(page - 1)}
          className="rounded-md border border-slate-200 p-1 disabled:opacity-40 enabled:hover:bg-slate-50">
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="tabular">Page {page} of {pages}</span>
        <button aria-label="Next page" disabled={page >= pages} onClick={() => onPage(page + 1)}
          className="rounded-md border border-slate-200 p-1 disabled:opacity-40 enabled:hover:bg-slate-50">
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function ExportButton({ href, label = "Export CSV" }: { href: string; label?: string }) {
  return (
    <a href={href} download className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-navy-800 shadow-sm hover:bg-slate-50">
      <Download className="h-4 w-4" aria-hidden /> {label}
    </a>
  );
}

export function Select({ label, value, onChange, options, allLabel = "All" }: {
  label: string; value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[]; allLabel?: string | null;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-1 text-xs font-medium text-slate-600">
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm">
        {allLabel !== null && <option value="">{allLabel}</option>}
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

export function Disclaimer() {
  return (
    <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
      <strong>Research and education use only.</strong> Evidence-support scores summarise the evidence recorded in
      this database. They are not probabilities of clinical validity and do not indicate that a biomarker is
      clinically approved, safe or effective.
    </p>
  );
}

export function KeyValue({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-[max-content_1fr]">
      {items.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="font-medium text-slate-500">{k}</dt>
          <dd className="min-w-0 break-words text-slate-900">{v ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Table({ head, children, caption }: { head: ReactNode[]; children: ReactNode; caption?: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>{head.map((h, i) => <th key={i} scope="col" className="px-3 py-2 font-semibold">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100">{children}</tbody>
      </table>
    </div>
  );
}
