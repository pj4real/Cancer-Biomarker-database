import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { buildQuery } from "../api/client";
import type { NetworkData, Score } from "../api/types";
import { layout, routeFor } from "../components/NetworkGraph";
import { ScoreBreakdown } from "../components/ScoreBreakdown";
import { ScoreStatusLabel } from "../components/ui";
import { formatScore, humanize } from "../lib/format";

describe("formatting helpers", () => {
  it("humanizes vocabulary values", () => {
    expect(humanize("randomized_clinical_trial")).toBe("Randomized clinical trial");
    expect(humanize("gene_fusion")).toBe("Gene fusion");
    expect(humanize(null)).toBe("—");
  });
  it("never renders a missing score as zero", () => {
    expect(formatScore(null)).toBe("n/a");
    expect(formatScore(0)).toBe("0.0");
  });
});

describe("buildQuery", () => {
  it("drops empty filters so the backend receives only active ones", () => {
    expect(buildQuery({ q: "KRAS", cancer_id: "", role: undefined, page: 2 })).toBe("?q=KRAS&page=2");
    expect(buildQuery({})).toBe("");
  });
});

const provisional: Score = {
  publication_support: 61.31, source_diversity: 50, evidence_type: 58, consistency: null,
  overall_score: 56.2, evidence_coverage: 0.85, score_status: "provisional",
  missing_components: ["consistency"], n_publications: 2, n_sources: 1, scoring_version: "1.0.0",
};

describe("ScoreBreakdown", () => {
  it("shows unknown components as unknown and warns that the score is provisional", () => {
    render(<ScoreBreakdown score={provisional} />);
    expect(screen.getByText(/unknown$/i)).toBeInTheDocument();
    expect(screen.getByText(/Not equivalent to a fully observed score/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Evidence consistency: unknown" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Publication support: 61.3" })).toBeInTheDocument();
  });
  it("handles an insufficient score with no overall value", () => {
    render(<ScoreBreakdown score={{ ...provisional, overall_score: null, score_status: "insufficient", evidence_coverage: 0 }} />);
    expect(screen.getByText(/Insufficient evidence metadata/)).toBeInTheDocument();
    expect(screen.getByText("n/a")).toBeInTheDocument();
  });
  it("status is conveyed by text, not colour alone", () => {
    render(<ScoreStatusLabel status="complete" />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });
});

describe("network layout", () => {
  const data: NetworkData = {
    nodes: [
      { id: "b1", label: "HER2", type: "biomarker", entity_id: 1 },
      { id: "c1", label: "Breast cancer", type: "cancer", entity_id: 1 },
      { id: "g1", label: "ERBB2", type: "gene", entity_id: 7 },
      { id: "p9", label: "PMID 3798106", type: "publication", entity_id: 9 },
    ],
    edges: [{ source: "b1", target: "c1", label: "predictive" }, { source: "b1", target: "g1", label: "gene" },
      { source: "c1", target: "p9", label: "evidence" }],
  };
  it("is deterministic and keeps the focus node centred", () => {
    const a = layout(data, 900, 460);
    const b = layout(data, 900, 460);
    expect(a).toEqual(b);
    expect(a.b1).toEqual({ x: 450, y: 230 });
  });
  it("routes nodes to their entity pages", () => {
    expect(routeFor(data.nodes[2])).toBe("/genes/7");
    expect(routeFor(data.nodes[3])).toBe("/publications?q=3798106");
  });
  it("renders inside a router", () => {
    // smoke test: ScoreBreakdown has no router dependency, network routes are pure functions
    render(<MemoryRouter><ScoreStatusLabel status="provisional" /></MemoryRouter>);
    expect(screen.getByText("Provisional")).toBeInTheDocument();
  });
});
