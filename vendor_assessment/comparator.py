from __future__ import annotations

from .scorecard import ComparisonReport


class VendorComparator:
    """Generate formatted comparison reports."""

    @staticmethod
    def to_markdown_table(report: ComparisonReport) -> str:
        """Generate markdown comparison table."""
        lines = [
            f"# {report.title}",
            f"*Assessment date: {report.assessment_date}*",
            "",
        ]

        # Overall scores table
        lines.append("## Overall Scores")
        lines.append("")
        header = (
            "| Dimension | "
            + " | ".join(
                sc.model_name for sc in report.scorecards
            )
            + " | Winner |"
        )
        sep = (
            "|---|"
            + "|".join("---" for _ in report.scorecards)
            + "|---|"
        )
        lines.extend([header, sep])

        dim_names = [
            "accuracy", "latency", "cost_efficiency",
            "safety_robustness", "domain_expertise", "consistency",
        ]
        for dim in dim_names:
            row_vals: list[str] = []
            for sc in report.scorecards:
                for ds in sc.dimension_scores:
                    if ds.dimension.value == dim:
                        row_vals.append(
                            f"{ds.score:.0f} ({ds.level.value})"
                        )
                        break
                else:
                    row_vals.append("N/A")
            winner = report.dimension_winners.get(dim, "")
            label = dim.replace("_", " ").title()
            lines.append(
                f"| {label} | "
                + " | ".join(row_vals)
                + f" | {winner} |"
            )

        # Overall row
        overall_vals = [
            f"**{sc.overall_score:.0f}**"
            for sc in report.scorecards
        ]
        lines.append(
            "| **Overall** | "
            + " | ".join(overall_vals)
            + f" | **{report.overall_winner}** |"
        )
        lines.append("")

        # Strengths/weaknesses per vendor
        lines.append("## Vendor Profiles")
        lines.append("")
        for sc in report.scorecards:
            lines.append(
                f"### {sc.model_name} ({sc.vendor_name})"
            )
            if sc.strengths:
                lines.append(
                    f"**Strengths:** {', '.join(sc.strengths)}"
                )
            if sc.weaknesses:
                lines.append(
                    f"**Weaknesses:** "
                    f"{', '.join(sc.weaknesses)}"
                )
            if sc.use_case_fit:
                lines.append("**Use Case Fit:**")
                for uc, fit in sc.use_case_fit.items():
                    label = uc.replace("_", " ").title()
                    lines.append(f"- {label}: {fit}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_summary(report: ComparisonReport) -> str:
        """Generate a short text summary."""
        if not report.scorecards:
            return "No vendors assessed."

        best = max(
            report.scorecards, key=lambda s: s.overall_score,
        )
        n = len(report.scorecards)
        return (
            f"Assessed {n} AI model(s) for financial use cases. "
            f"Top overall: {best.model_name} "
            f"({best.vendor_name}) "
            f"with score {best.overall_score:.0f}/100."
        )
