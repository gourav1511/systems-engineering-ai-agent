"""PDF proposal builder using reportlab."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


DISCLAIMER_TEXT = (
    "This document is an AI-assisted Phase 0 concept draft. All technical values, cost estimates, "
    "procurement options, and requirements must be reviewed and validated by a qualified spacecraft "
    "systems engineer before use in design, procurement, proposal submission, or mission decision-making."
)
MVP_SCOPE_1 = (
    "This MVP report is generated for a single-satellite mission concept. It does not analyze constellation "
    "deployment, multi-satellite phasing, revisit optimization, inter-satellite links, or multi-plane architectures."
)
MVP_SCOPE_2 = (
    "This MVP report assumes an Earth Observation payload concept. Payload-specific analysis is limited to "
    "high-level swath, resolution, mass, and power assumptions where provided."
)


def build_pdf_proposal(all_outputs: dict, output_path: str) -> str:
    """Build and save a PDF proposal from pipeline outputs."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    mission_context = all_outputs.get("mission_context", {})
    mission = all_outputs.get("mission", {})
    mass = all_outputs.get("mass", {})
    power = all_outputs.get("power", {})
    cost = all_outputs.get("cost", {})
    procurement = all_outputs.get("procurement", {})

    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=1.8 * cm, leftMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, spaceAfter=8)
    normal = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=13)

    story = []
    story.append(Paragraph(mission_context.get("mission_name", "Unnamed Mission"), h1))
    story.append(Paragraph("Phase 0 Mission Proposal", styles["Title"]))
    story.append(Paragraph(f"Date: {date.today().isoformat()}", normal))
    story.append(Paragraph("Version: MVP Draft", normal))
    story.append(Spacer(1, 18))

    story.append(Paragraph("Executive Summary", h1))
    story.append(Paragraph((mission.get("conops_summary") or "Executive summary unavailable."), normal))

    story.append(Paragraph("MVP Scope and Limitations", h1))
    story.append(Paragraph(f"1. {MVP_SCOPE_1}", normal))
    story.append(Paragraph(f"2. {MVP_SCOPE_2}", normal))

    story.append(Paragraph("Mission Overview", h1))
    for obj in mission.get("objectives", []):
        story.append(Paragraph(f"- {obj}", normal))

    story.append(Paragraph("Mission Requirements", h1))
    req_data = [["ID", "Requirement", "Rationale"]]
    for req in mission.get("requirements", []):
        req_data.append([str(req.get("id", "")), str(req.get("text", "")), str(req.get("rationale", ""))])
    story.append(_styled_table(req_data, [2.2 * cm, 9.0 * cm, 6.0 * cm]))

    story.append(Paragraph("Mass Budget", h1))
    story.append(Paragraph(f"Status: {mass.get('status', 'UNKNOWN')}", normal))
    mass_data = [["Subsystem", "Mass (kg)", "Margin %", "Notes"]]
    for s in mass.get("subsystems", []):
        mass_data.append([str(s.get("name", "")), str(s.get("mass_kg", "")), str(s.get("margin_pct", "")), str(s.get("notes", ""))])
    story.append(_styled_table(mass_data, [4.0 * cm, 3.0 * cm, 3.0 * cm, 7.2 * cm]))

    story.append(Paragraph("Power Budget", h1))
    story.append(Paragraph(f"Status: {power.get('status', 'UNKNOWN')}", normal))
    power_data = [["Mode", "Total W"]]
    for mode, values in power.get("modes", {}).items():
        power_data.append([mode, str(values.get("total_W", ""))])
    story.append(_styled_table(power_data, [8.0 * cm, 4.0 * cm]))

    story.append(Paragraph("Cost Estimate", h1))
    cost_data = [["Category", "Cost (kEUR)", "Basis"]]
    for c in cost.get("cost_breakdown", []):
        cost_data.append([str(c.get("category", "")), str(c.get("cost_kEUR", "")), str(c.get("basis", ""))])
    story.append(_styled_table(cost_data, [7.0 * cm, 3.5 * cm, 5.0 * cm]))

    story.append(Paragraph("Component Alternatives", h1))
    for search in procurement.get("component_searches", []):
        story.append(Paragraph(f"Category: {search.get('category', '')}", normal))
        p_data = [["Rank", "Product", "Vendor", "URL", "Price", "Lead wks"]]
        for a in search.get("alternatives", []):
            p_data.append([
                str(a.get("rank", "")),
                str(a.get("product_name", "")),
                str(a.get("vendor", "")),
                str(a.get("source_url", "")),
                str(a.get("unit_price_kEUR", "")),
                str(a.get("lead_time_weeks", "")),
            ])
        story.append(_styled_table(p_data, [1.4 * cm, 3.2 * cm, 2.6 * cm, 5.3 * cm, 2.0 * cm, 2.0 * cm]))
        for w in search.get("warnings", []):
            story.append(Paragraph(f"Warning: {w}", normal))

    story.append(Paragraph("Assumptions and Open Items", h1))
    for a in mission.get("assumptions", []):
        story.append(Paragraph(f"Assumption: {a}", normal))
    for q in mission.get("open_questions", []):
        story.append(Paragraph(f"Open question: {q}", normal))

    story.append(Paragraph("Disclaimer", h1))
    story.append(Paragraph(DISCLAIMER_TEXT, normal))

    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return str(output)


def _styled_table(data: list[list[str]], col_widths: list[float]) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table


def _page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()
