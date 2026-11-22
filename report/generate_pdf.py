"""
Generates publication-quality IEEE-style two-column PDF Research Report using ReportLab:
report/report.pdf.
Uses the latest report/report.tex as the authoritative source of truth.
Preserves all research content, equations, numerical results, references, and tables.
Embeds Figure 8 (figures/fig8_sensitivity_rho.png) cleanly.
Ensures Tables III, IV, and V fit strictly within the 258 pt IEEE column width.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, FrameBreak, NextPageTemplate, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class IEEENumberedCanvas(canvas.Canvas):
    """Two-pass canvas for IEEE running header and footer with total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 7.5)
        self.setFillColor(colors.HexColor("#333333"))

        # Running header on page 2+
        if self._pageNumber > 1:
            if self._pageNumber % 2 == 0:
                self.drawString(36, 756, "ADVANCED ALGORITHMS RESEARCH REPORT")
            else:
                self.drawRightString(576, 756, "ADVANCED ALGORITHMS RESEARCH REPORT")
            self.setStrokeColor(colors.HexColor("#999999"))
            self.setLineWidth(0.4)
            self.line(36, 751, 576, 751)

        # Running footer on all pages
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.4)
        self.line(36, 42, 576, 42)
        self.drawString(36, 32, "ADVANCED ALGORITHMS RESEARCH REPORT")
        page_text = f"{self._pageNumber}"
        self.drawRightString(576, 32, page_text)

        self.restoreState()


def build_pdf_report(pdf_path: str = "report/report.pdf"):
    # Geometry: Letter (612 x 792 pt), margins = 36 pt (0.5 in). Usable width = 540 pt.
    # Two columns: col_width = 258 pt, gutter = 24 pt (36 + 258 + 24 + 258 = 576 pt).
    doc = BaseDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    # 1. Page Template: First Page (Top banner for Title + Authors, 2 columns below for Abstract + Body)
    top_h = 135
    f_top = Frame(36, 792 - 36 - top_h, 540, top_h, id='top_banner',
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f_c1_p1 = Frame(36, 46, 258, 710 - top_h - 10, id='c1_p1',
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f_c2_p1 = Frame(318, 46, 258, 710 - top_h - 10, id='c2_p1',
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    pt_first = PageTemplate(id='first_page', frames=[f_top, f_c1_p1, f_c2_p1])

    # 2. Page Template: Standard Two-Column Body
    f_c1 = Frame(36, 46, 258, 700, id='col1',
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f_c2 = Frame(318, 46, 258, 700, id='col2',
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    pt_two = PageTemplate(id='two_col', frames=[f_c1, f_c2])

    # 3. Page Template: Full-Width Table Page
    f_full = Frame(36, 46, 540, 700, id='full_col',
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    pt_full = PageTemplate(id='full_page', frames=[f_full])

    doc.addPageTemplates([pt_first, pt_two, pt_full])

    # Typography styles (strictly IEEE-aligned using Times-Roman)
    styles = getSampleStyleSheet()

    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=17,
        leading=20,
        alignment=1,  # Center
        textColor=colors.HexColor("#000000"),
        spaceAfter=6,
    )

    authors_style = ParagraphStyle(
        "Authors",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9.5,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#111111"),
        spaceAfter=2,
    )

    affiliation_style = ParagraphStyle(
        "Affiliation",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=8,
        leading=10.5,
        alignment=1,
        textColor=colors.HexColor("#444444"),
        spaceAfter=6,
    )

    sec_h1 = ParagraphStyle(
        "SecH1",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9.5,
        leading=12,
        alignment=1,  # Centered uppercase like IEEE
        textColor=colors.HexColor("#000000"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    subsec_h2 = ParagraphStyle(
        "SubSecH2",
        parent=styles["Normal"],
        fontName="Times-BoldItalic",
        fontSize=8.5,
        leading=11,
        alignment=0,  # Left
        textColor=colors.HexColor("#000000"),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.2,
        leading=10.2,
        alignment=4,  # Justified
        textColor=colors.HexColor("#111111"),
        spaceAfter=3.5,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Times-Bold",
    )

    abstract_style = ParagraphStyle(
        "AbstractText",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=7.8,
        leading=9.8,
        alignment=4,
        textColor=colors.HexColor("#111111"),
        spaceAfter=4,
    )

    callout_box_style = ParagraphStyle(
        "CalloutBoxText",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#111111"),
    )

    eq_style = ParagraphStyle(
        "Equation",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=7.8,
        leading=10,
        alignment=1,
        spaceBefore=2,
        spaceAfter=3,
    )

    caption_style = ParagraphStyle(
        "Caption",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=7.2,
        leading=9,
        alignment=1,
        spaceBefore=4,
        spaceAfter=3,
        keepWithNext=True,
    )

    tbl_cell = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=6.5,
        leading=8,
        alignment=1,
        textColor=colors.black,
    )

    tbl_cell_left = ParagraphStyle(
        "TblCellLeft",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=6.5,
        leading=8,
        alignment=0,
        textColor=colors.black,
    )

    tbl_cell_bold = ParagraphStyle(
        "TblCellBold",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=6.5,
        leading=8,
        alignment=1,
        textColor=colors.black,
    )

    tbl_cell_bold_left = ParagraphStyle(
        "TblCellBoldLeft",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=6.5,
        leading=8,
        alignment=0,
        textColor=colors.black,
    )

    tbl_hdr_cell = ParagraphStyle(
        "TblHdrCell",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=6.5,
        leading=8,
        alignment=1,
        textColor=colors.white,
    )

    tbl_hdr_cell_left = ParagraphStyle(
        "TblHdrCellLeft",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=6.5,
        leading=8,
        alignment=0,
        textColor=colors.white,
    )

    ref_style = ParagraphStyle(
        "Reference",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=7.2,
        leading=9,
        alignment=4,
        leftIndent=14,
        firstLineIndent=-14,
        spaceAfter=2.5,
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE BANNER (TOP FRAME)
    # =========================================================================
    story.append(Paragraph("Adaptive Large Neighborhood Search with Exact Window Dynamic Programming for Single-Machine Scheduling with Sequence-Dependent Setups and Release Dates", doc_title_style))
    story.append(Paragraph("Advanced Algorithms Research Group", authors_style))
    story.append(Paragraph("Department of Computer Science & Engineering, University Research Report -- Advanced Design and Analysis of Algorithms", affiliation_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#000000"), spaceAfter=4))
    
    # Break out of the top banner into the left column of page 1
    story.append(FrameBreak())
    story.append(NextPageTemplate('two_col'))

    # =========================================================================
    # ABSTRACT & INDEX TERMS (IN COLUMN 1)
    # =========================================================================
    abstract_p1 = (
        "<b><i>Abstract</i>—Single-machine makespan minimization (1 || C_max) is trivial: additive completion yields "
        "C_max = sum(p_j) (14 for 4-job benchmark) in O(n) time. Adding setups s_ij and release dates r_j "
        "(1 | r_j, s_ij | C_max) is strongly NP-hard via ATSP/TSPTW.</b>"
    )
    abstract_p2 = (
        "<b>We evaluate ALNS-WDP (destroy-repair, sliding-window Held-Karp DP k in [6, 10], adaptive bandit weighting whose "
        "benefit was not demonstrated). On 20 benchmark instances (n in [4, 200], alpha in {0, 0.3, 0.6}, 30 seeds) under "
        "matched budgets (within 6%; ablation up to 1.15x), ALNS-WDP achieves lower mean gap to dual lower bound (5.47%) "
        "than SA (6.65%), GA (7.70%), and MultiStart_LS (14.89%). Differences are significant only vs GA (Holm p = 0.0146), "
        "not SA or MultiStart_LS (p = 0.128). Exploratory split: ALNS-WDP excels on asymmetric setups (9/9 wins vs GA, "
        "+2.7% vs SA), but trails on symmetric setups (vs SA: 3W/4T/4L; GA beats ALNS on n100_a30_sym). Controlled setup dominance "
        "tests (rho_s in [0.06, 4.30], 2,400 runs) confirm ALNS-WDP widens its edge on asymmetric matrices (Holm p &lt; 0.0001), "
        "while reversal-based local search appears competitive on symmetric setups, although the underlying mechanism remains a hypothesis requiring further investigation. n=200 is singular.</b>"
    )
    abstract_p3 = (
        "<b>Ablation shows window-DP beats No_WindowDP at n=100 (Holm p &lt; 0.05); no benefit n &lt;= 50; adaptive weights show no "
        "gain (Holm p = 1.000). On 11 small instances (n &lt;= 20), gap to optimum ranks MultiStart_LS 0.27% &lt; SA 0.40% &lt; ALNS-WDP 0.45% &lt; GA 1.97%. "
        "Bi-objective tests show ALNS-WDP achieves lower IGD on 3/6 instances (Holm-significant on 1/6), while NSGA-II attains higher "
        "hypervolume on 5/6 (Holm-significant on 5/6) because Window-DP optimizes makespan only.</b>"
    )
    story.append(Paragraph(abstract_p1, abstract_style))
    story.append(Paragraph(abstract_p2, abstract_style))
    story.append(Paragraph(abstract_p3, abstract_style))
    story.append(Spacer(1, 2))

    keywords_text = (
        "<b><i>Index Terms</i>—Single-Machine Scheduling, Sequence-Dependent Setup Times, Release Dates, "
        "Adaptive Large Neighborhood Search, Sliding Window Dynamic Programming, Setup-Time Dominance, Multi-Objective Optimization.</b>"
    )
    story.append(Paragraph(keywords_text, abstract_style))
    story.append(Spacer(1, 4))

    # =========================================================================
    # SECTION I: INTRODUCTION AND RESEARCH QUESTIONS
    # =========================================================================
    story.append(Paragraph("I. INTRODUCTION AND RESEARCH QUESTIONS", sec_h1))
    story.append(Paragraph(
        "Scheduling theory forms an essential foundation for operations research, automated manufacturing, high-performance computing, "
        "and semiconductor supply chains [1]. Within classical scheduling theory, single-machine environments serve as the canonical building block "
        "for complex multi-stage architectures, including flow shops, job shops, and flexible manufacturing cells.",
        body_style
    ))
    story.append(Paragraph(
        "In Practical Problem 4 of the curriculum, students encounter an elementary single-machine scheduling scenario: a single machine must "
        "process four independent jobs A, B, C, D with deterministic processing times p_A = 3, p_B = 5, p_C = 2, p_D = 4, with zero release dates "
        "and no setups. The target objective is makespan minimization (min C_max). As proven formally in Section III, this baseline problem "
        "(1 || C_max) is degenerate: <i>every</i> feasible permutation yields the identical makespan C_max = sum(p_j) = 14 in O(n) time, "
        "locating it firmly within the polynomial class <b>P</b>.",
        body_style
    ))
    story.append(Paragraph(
        "However, practical production environments rarely satisfy such idealized conditions:<br/>"
        "• <b>Sequence-Dependent Setup Times (s_ij):</b> Re-tooling, thermal stabilization, chemical purging, or mechanical calibration between distinct "
        "jobs depend directly upon both preceding job i and succeeding job j. This introduces routing costs isomorphic to the Traveling Salesperson Problem (TSP) [3].<br/>"
        "• <b>Release Dates (r_j):</b> Materials, upstream parts, or external buffers arrive intermittently, introducing arrival-time constraints that induce "
        "idle waiting times unless sequence order is carefully optimized.",
        body_style
    ))
    story.append(Paragraph(
        "Coupling sequence-dependent setups and release dates yields the strongly NP-hard problem denoted in Graham notation as "
        "1 | r_j, s_ij | C_max [2, 11]. This generalizes the Asymmetric Traveling Salesperson Problem with Time Windows (TSPTW). Exact techniques, "
        "such as branch-and-cut and integer linear programming, encounter combinatorial bottlenecks on moderate instances (n &gt;= 30).",
        body_style
    ))
    story.append(Paragraph(
        "To investigate the structural behavior of this problem and evaluate hybrid metaheuristics, we formulate three concrete Research Questions:<br/>"
        "• <b>RQ1 (Exact Subproblem Polishing):</b> Does embedding an exact sliding-window Held-Karp dynamic programming polisher (k in [6, 10]) "
        "within an Adaptive Large Neighborhood Search framework yield statistically significant makespan reductions compared to pure destruction-repair metaheuristics?<br/>"
        "• <b>RQ2 (Setup Topology and Operator Design):</b> How does the algebraic structure of the setup matrix (asymmetric vs. symmetric Euclidean) "
        "interact with operator choice, and could reversal-based descent (2-opt) help explain the observed competitive performance on symmetric setups?<br/>"
        "• <b>RQ3 (Controlled Setup-Time Dominance):</b> When the ratio of transition setup duration to job processing time (rho_s = s_bar / p_bar) "
        "is systematically varied, does the relative performance advantage of ALNS-WDP expand as setup routing costs dominate?",
        body_style
    ))

    # =========================================================================
    # SECTION II: RELATED WORK AND RESEARCH GAP
    # =========================================================================
    story.append(Paragraph("II. RELATED WORK AND RESEARCH GAP", sec_h1))
    story.append(Paragraph("A. Exact and Restricted Dynamic Programming Neighborhoods", subsec_h2))
    story.append(Paragraph(
        "Dynamic programming for sequencing problems originates with the seminal Held-Karp algorithm [7], which evaluates subset states in O(n^2 2^n) time. "
        "To circumvent exponential complexity on large instances, Balas and Simonetti [8] introduced linear-time dynamic programming over restricted permutation graphs "
        "where jobs cannot shift more than k positions (|i - pi(i)| &lt;= k), solving restricted TSPs and single-machine scheduling with setups and release dates "
        "in O(n k^2 2^{k-1}) time. Congram, Potts, and van de Velde [9] developed Dynasearch for 1 || sum(w_j T_j), evaluating an exponential neighborhood of independent "
        "pairwise exchanges in polynomial time using dynamic programming. Sourd [10] extended Dynasearch to handle setup times and release dates in earliness-tardiness "
        "scheduling by structuring moves into non-interacting blocks.",
        body_style
    ))
    story.append(Paragraph("B. Adaptive Large Neighborhood Search in Scheduling and Routing", subsec_h2))
    story.append(Paragraph(
        "Large Neighborhood Search (LNS) was proposed by Shaw [6] using constraint programming to re-insert related customers. Ropke and Pisinger [4] extended LNS "
        "into Adaptive Large Neighborhood Search (ALNS) for pickup and delivery problems with time windows, introducing adaptive roulette-wheel operator selection. "
        "Pisinger and Ropke [5] formalized the general principles of destruction and construction heuristics across vehicle routing and scheduling domains. "
        "Archetti and Speranza [12] classified ALNS within the broader taxonomy of matheuristics, emphasizing the hybridization of mathematical programming "
        "subproblems with metaheuristic search.",
        body_style
    ))
    story.append(Paragraph("C. Sequence-Dependent Setup Times and ATSP Formulations", subsec_h2))
    story.append(Paragraph(
        "Scheduling problems with sequence-dependent setup times have been surveyed extensively by Allahverdi [11]. The reduction of single-machine makespan "
        "minimization with setups (1 | s_ij | C_max) to ATSP was established early in computational complexity theory [3]. When release dates are introduced "
        "(1 | r_j, s_ij | C_max), machine idling couples with sequence-dependent routing, making the search landscape multimodal and challenging.",
        body_style
    ))
    story.append(Paragraph("D. Multi-Objective Combinatorial Scheduling", subsec_h2))
    story.append(Paragraph(
        "Multi-objective scheduling addresses trade-offs between competing shop-floor objectives, notably makespan (C_max) and Total Weighted Tardiness (sum w_j T_j). "
        "Deb et al. [13] introduced NSGA-II, an elitist non-dominated sorting genetic algorithm that establishes high-quality Pareto frontiers without requiring arbitrary scalarization weights.",
        body_style
    ))
    story.append(Paragraph("E. Research Gap and Contribution", subsec_h2))
    story.append(Paragraph(
        "Prior exact dynamic programming neighborhoods (such as Dynasearch [9, 10] or Balas-Simonetti networks [8]) assume either non-interacting moves or "
        "bandwidth-limited permutations (|i - pi(i)| &lt;= k). In contrast, 1 | r_j, s_ij | C_max involves non-linear release date jumps max(r_j, C + s_mj) + p_j "
        "and arbitrary transition matrices. This paper addresses this gap by coupling global ALNS destruction-repair heuristics with exact physical sliding-window "
        "Held-Karp dynamic programming re-optimization (k in [6, 10]).",
        body_style
    ))

    # =========================================================================
    # SECTION III: PROBLEM UNDERSTANDING AND THEORETICAL ANALYSIS
    # =========================================================================
    story.append(Paragraph("III. PROBLEM UNDERSTANDING AND THEORETICAL ANALYSIS", sec_h1))
    story.append(Paragraph("A. Formal Specification of Base Problem (1 || C_max)", subsec_h2))
    story.append(Paragraph(
        "Let J = {1, 2, ..., n} be a set of n independent, non-preemptive jobs to process on a single machine. For each job j in J, let p_j in Z^+ denote "
        "its deterministic processing time. A schedule is defined by a permutation pi = (pi(1), ..., pi(n)). Start time S_pi(k) and completion C_pi(k) satisfy: "
        "S_pi(1) = 0, C_pi(1) = p_pi(1); S_pi(k) = C_pi(k-1), C_pi(k) = S_pi(k) + p_pi(k). The makespan is C_max(pi) = C_pi(n).",
        body_style
    ))

    thm1_box = [
        [Paragraph(
            "<b>Theorem 1 (Permutation Invariance of Base Makespan):</b><br/>"
            "<i>For any instance of 1 || C_max with p_j &gt;= 0, every semi-active schedule achieves identical makespan:</i><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>C_max(pi) = sum_{j=1}^n p_j &nbsp;&nbsp; for all pi in Pi_n</b><br/>"
            "<i>Proof:</i> Since machine idling is unforced, S_pi(1) = 0 and S_pi(k) = C_pi(k-1). Telescoping yields "
            "C_max(pi) = sum_{k=1}^n p_pi(k). Because real addition is commutative and associative, the summation over set J "
            "is invariant to ordering pi. All 4! = 24 permutations in Problem 4 yield C_max = 3 + 5 + 2 + 4 = 14. [Q.E.D.]",
            callout_box_style
        )]
    ]
    t1 = Table(thm1_box, colWidths=[256])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(t1)
    story.append(Spacer(1, 3))

    story.append(Paragraph("B. Complexity Ladder: From Trivial Base to NP-Hard Extensions", subsec_h2))
    story.append(Paragraph(
        "• <b>Release Dates Alone (1 | r_j | C_max):</b> Solved to proven optimality in O(n log n) time by ordering jobs via Earliest Release Date (ERD).<br/>"
        "• <b>Sequence-Dependent Setups (1 | s_ij | C_max):</b> Makespan becomes sum(p_j) + s_0,pi(1) + sum s_pi(k-1),pi(k). "
        "Minimizing makespan is strictly isomorphic to finding a minimum-weight directed Hamiltonian path originating at depot 0 (ATSP), which is strongly NP-hard [3].<br/>"
        "• <b>Combined Problem (1 | r_j, s_ij | C_max):</b> S_pi(k) = max(r_pi(k), C_pi(k-1) + s_pi(k-1),pi(k)), C_pi(k) = S_pi(k) + p_pi(k). "
        "Couples ATSP tour routing with arrival-time synchronization, rendering it strongly NP-hard.",
        body_style
    ))

    story.append(Paragraph("C. Worked 4-Job Numerical Example", subsec_h2))
    story.append(Paragraph(
        "Consider the 4 jobs of Problem 4 (p=[3, 5, 2, 4]) endowed with depot setups s_0=[2, 4, 1, 3] and asymmetric setup matrix S with transitions:<br/>"
        "&nbsp;&nbsp;pi_1 = (C, B, D, A): C_max = 1 + 2 + 2 + 5 + 1 + 4 + 1 + 3 = 19.<br/>"
        "&nbsp;&nbsp;pi_2 = (A, B, C, D): C_max = 2 + 3 + 8 + 5 + 6 + 2 + 7 + 4 = 37.<br/>"
        "The makespan varies by nearly a factor of two (19 vs 37), demonstrating the acute combinatorial sensitivity of the generalized problem.",
        body_style
    ))

    # =========================================================================
    # SECTION IV: MATHEMATICAL FORMULATIONS
    # =========================================================================
    story.append(Paragraph("IV. MATHEMATICAL FORMULATIONS", sec_h1))
    story.append(Paragraph("A. Mixed-Integer Linear Programming (MTZ Formulation)", subsec_h2))
    story.append(Paragraph(
        "We model 1 | r_j, s_ij | C_max on directed graph G = (V_0, A) where V_0 = {0} union {1, ..., n}. "
        "Binary x_ij in {0, 1} indicate immediate succession; continuous S_j &gt;= 0 denote start times:<br/>"
        "&nbsp;&nbsp;<b>min C_max</b><br/>"
        "&nbsp;&nbsp;s.t. sum_{j=1}^n x_0j = 1, &nbsp; sum_{i=1}^n x_i0 = 1 &nbsp;&nbsp; (Depot flow)<br/>"
        "&nbsp;&nbsp;sum_{j=0, j!=k}^n x_kj = 1, &nbsp; sum_{i=0, i!=k}^n x_ik = 1 &nbsp; for all k in V<br/>"
        "&nbsp;&nbsp;u_j - u_i + n x_ij &lt;= n - 1 &nbsp; for all i, j in V, i != j &nbsp;&nbsp; (MTZ subtour)<br/>"
        "&nbsp;&nbsp;S_j &gt;= r_j &nbsp;&nbsp; for all j in V &nbsp;&nbsp; (Release dates)<br/>"
        "&nbsp;&nbsp;S_j &gt;= s_0j - M(1 - x_0j) &nbsp;&nbsp; for all j in V &nbsp;&nbsp; (Initial setup)<br/>"
        "&nbsp;&nbsp;S_j &gt;= S_i + p_i + s_ij - M(1 - x_ij) &nbsp;&nbsp; for all i, j in V &nbsp;&nbsp; (Precedence)<br/>"
        "&nbsp;&nbsp;C_max &gt;= S_j + p_j &nbsp;&nbsp; for all j in V &nbsp;&nbsp; (Makespan)",
        body_style
    ))

    story.append(Paragraph("B. Valid Dual Anchor Lower Bound Formulation", subsec_h2))
    thm2_box = [
        [Paragraph(
            "<b>Theorem 2 (Validity of the Dual Anchor Lower Bound):</b><br/>"
            "<i>Let S_a = {k in J : r_k &gt;= r_a} denote jobs released at or after r_a. The dual bound:</i><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>LB_dual = max(LB_AP, LB_Release, max_{a in J} LB_Anchor(a))</b><br/>"
            "<i>where LB_AP = sum(p_j) + C_AP(J), LB_Release = max_j(r_j + p_j), and:</i><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<b>LB_Anchor(a) = r_a + sum_{k in S_a} p_k</b><br/>"
            "<i>is a valid lower bound on C_max* for any feasible schedule.</i><br/>"
            "<i>Proof:</i> Machine processing sum(p_j) and transition setups C_AP(J) (via Hungarian Assignment [14]) must both be satisfied. "
            "No job j can finish before r_j + p_j. For any anchor a in J, all jobs in S_a are released &gt;= r_a; non-concurrency requires "
            "at least sum_{k in S_a} p_k duration after r_a. Taking the maximum preserves validity.<br/>"
            "<b>Remark on Invalidity of Subset Assignment Setups:</b> Appending internal setups C_AP(S_a) to r_a is invalid for general matrices: "
            "earlier-released jobs can interleave between subset jobs, bypassing internal transitions. Counterexample: p=[1,1,1], r=[0,1,1], "
            "s_12=s_21=100 gives C_max*=4, but subset setup bound yields 103 &gt; 4. Thus the anchor bound must remain processing-only. [Q.E.D.]",
            callout_box_style
        )]
    ]
    t2 = Table(thm2_box, colWidths=[256])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(t2)
    story.append(Spacer(1, 3))

    # =========================================================================
    # SECTION V: PROPOSED ALGORITHM: ALNS-WDP
    # =========================================================================
    story.append(Paragraph("V. PROPOSED ALGORITHM: ALNS-WDP", sec_h1))
    story.append(Paragraph(
        "ALNS-WDP combines global destruction-repair exploration with localized exact combinatorial re-optimization:",
        body_style
    ))

    alg_box = [
        [Paragraph(
            "<b>Algorithm 1: ALNS-WDP Core Framework</b><br/>"
            "<b>Require:</b> Instance I = (p, r, S, s_0), budget T_max, window k=8, floor w_floor=0.05<br/>"
            "1: pi_inc &lt;- HeuristicInitialization(I); &nbsp; pi* &lt;- pi_inc, C* &lt;- C_max(pi*)<br/>"
            "2: Initialize operator weights w_d &lt;- 1.0, w_r &lt;- 1.0<br/>"
            "3: <b>while</b> ElapsedTime() &lt; T_max <b>do</b><br/>"
            "4: &nbsp;&nbsp;&nbsp;&nbsp;Select destroy d and repair r via bandit scores<br/>"
            "5: &nbsp;&nbsp;&nbsp;&nbsp;pi_partial &lt;- Destroy(pi_inc, d, q)<br/>"
            "6: &nbsp;&nbsp;&nbsp;&nbsp;pi_cand &lt;- Repair(pi_partial, r)<br/>"
            "7: &nbsp;&nbsp;&nbsp;&nbsp;<b>if</b> rand() &lt; p_DP <b>then</b><br/>"
            "8: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pi_cand &lt;- SlidingWindowDP(pi_cand, k)<br/>"
            "9: &nbsp;&nbsp;&nbsp;&nbsp;Update incumbent via simulated annealing acceptance<br/>"
            "10: &nbsp;&nbsp;&nbsp;Update bandit weights with exploration floor w_floor = 0.05<br/>"
            "11: <b>return</b> pi*, C*",
            callout_box_style
        )]
    ]
    t_alg = Table(alg_box, colWidths=[256])
    t_alg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(t_alg)
    story.append(Spacer(1, 3))

    story.append(Paragraph("A. Destroy and Repair Neighborhood Operators", subsec_h2))
    story.append(Paragraph(
        "Four destroy operators remove q in [2, min(15, 0.4n)] jobs: (i) Random; (ii) Worst-Setup; (iii) Cluster; (iv) Shaw-Relatedness. "
        "Two repair operators reinsert removed jobs: (i) Greedy Best-Fit; (ii) Regret-2 Insertion (maximizes opportunity cost c2 - c1).",
        body_style
    ))
    story.append(Paragraph("B. Exact Sliding-Window Dynamic Programming Polisher", subsec_h2))
    story.append(Paragraph(
        "For subsegment pi[i : i+k-1] of size k in [6, 10], we solve the exact Held-Karp recurrence:<br/>"
        "&nbsp;&nbsp;DP(mask, j) = min_{m in mask\\{j}} { max(r_j, DP(mask\\{j}, m) + s_mj) + p_j }<br/>"
        "respecting prefix completion C_pred and exit setup s_j,succ. Because the identity ordering belongs to the state space, "
        "Sliding-Window DP guarantees monotonic non-deterioration: C_max(pi_opt) &lt;= C_max(pi_orig).",
        body_style
    ))
        # =========================================================================
    # SWITCH TO FULL-WIDTH TEMPLATE FOR PAGE 3 (V-C, VI, TABLE I, TABLE II, VI-A, VI-B)
    # =========================================================================
    story.append(NextPageTemplate('full_page'))
    story.append(PageBreak())

    story.append(Paragraph("C. Stateless Bandit Operator Scoring", subsec_h2))
    story.append(Paragraph(
        "Operator weights are updated adaptively via exponential moving average: w_op &lt;- (1 - rho) w_op + rho R with floor w_op &gt;= 0.05. "
        "(We note that factorial ablation testing in Section VII yielded no statistically significant improvement over static uniform weights, Holm p = 1.000).",
        body_style
    ))

    story.append(Paragraph("VI. EXPERIMENTAL RESULTS AND EMPIRICAL ANALYSIS", sec_h1))
    story.append(Paragraph(
        "We benchmarked 20 problem instances (n in [4, 200], alpha in {0.0, 0.3, 0.6}, asymmetric and symmetric setups, "
        "TSPLIB instances bayg29 and berlin52) across 30 independent stochastic seeds under strictly matched wall-clock budgets "
        "(within 6% runtime parity per instance size).",
        body_style
    ))
    story.append(Spacer(1, 3))

    # TABLE I: BENCHMARKS (FULL WIDTH 540 pt)
    story.append(Paragraph("TABLE I: Benchmark Results across 20 Problem Instances (30 Seeds per Stochastic Method)", caption_style))
    bench_data = [
        [Paragraph("<b>Algorithm</b>", tbl_hdr_cell_left),
         Paragraph("<b>Runs</b>", tbl_hdr_cell),
         Paragraph("<b>Mean Gap to LB (%)</b>", tbl_hdr_cell),
         Paragraph("<b>Std Gap (%)</b>", tbl_hdr_cell),
         Paragraph("<b>Mean Runtime (s)</b>", tbl_hdr_cell),
         Paragraph("<b>Friedman Rank</b>", tbl_hdr_cell)]
    ]
    bench_rows = [
        ("Exact Held-Karp DP* (n <= 20)", "11", "4.00", "3.86", "10.26", "N/A"),
        ("Brute Force* (n <= 10)", "5", "3.68", "5.26", "1.44", "N/A"),
        ("CP-SAT Matheuristic* (n <= 20)", "11", "4.19", "3.89", "0.66", "N/A"),
        ("ALNS-WDP (Proposed)", "600", "5.47", "3.84", "1.39", "1.98"),
        ("Simulated Annealing (SA)", "600", "6.65", "4.44", "1.37", "2.38"),
        ("Multi-Start Local Search", "600", "14.89", "16.75", "1.42", "2.52"),
        ("Genetic Algorithm (GA)", "600", "7.70", "4.51", "1.37", "3.12"),
        ("Nearest-Setup Greedy", "20", "17.03", "12.63", "<0.001", "N/A"),
        ("ECT Dispatching Rule", "20", "20.86", "8.33", "<0.001", "N/A"),
        ("ERD Dispatching Rule", "20", "46.27", "17.49", "<0.001", "N/A"),
        ("SPT Dispatching Rule", "20", "59.92", "23.17", "<0.001", "N/A"),
    ]
    for row in bench_rows:
        is_alns = "ALNS-WDP" in row[0]
        bench_data.append([
            Paragraph(row[0], tbl_cell_bold_left if is_alns else tbl_cell_left),
            Paragraph(row[1], tbl_cell),
            Paragraph(row[2], tbl_cell_bold if is_alns else tbl_cell),
            Paragraph(row[3], tbl_cell),
            Paragraph(row[4], tbl_cell),
            Paragraph(row[5], tbl_cell_bold if is_alns else tbl_cell),
        ])
    t_bench = Table(bench_data, colWidths=[170, 45, 85, 75, 85, 80])
    t_bench.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 2.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_bench)
    story.append(Paragraph("<font size=6>*Note: Exact DP (n <= 20), Brute Force (n <= 10), and CP-SAT (n <= 20) cover small instances only. Gap to LB reflects the duality gap of integer solutions, not sub-optimality.</font>", body_style))
    story.append(Spacer(1, 6))

    # TABLE II: SMALL INSTANCES (FULL WIDTH 540 pt)
    story.append(Paragraph("TABLE II: Per-Instance Optimality Breakdown on Small Instances (n <= 20, 11 Instances, 30 Seeds per Metaheuristic)", caption_style))
    small_data = [
        [Paragraph("<b>Instance</b>", tbl_hdr_cell_left),
         Paragraph("<b>n</b>", tbl_hdr_cell),
         Paragraph("<b>Opt</b>", tbl_hdr_cell),
         Paragraph("<b>LB</b>", tbl_hdr_cell),
         Paragraph("<b>ALNS Gap</b>", tbl_hdr_cell),
         Paragraph("<b>Hit%</b>", tbl_hdr_cell),
         Paragraph("<b>MS-LS Gap</b>", tbl_hdr_cell),
         Paragraph("<b>Hit%</b>", tbl_hdr_cell),
         Paragraph("<b>SA Gap</b>", tbl_hdr_cell),
         Paragraph("<b>Hit%</b>", tbl_hdr_cell)]
    ]
    small_rows = [
        ("base_4job", "4", "14", "14", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n8_a30_asym_s1803", "8", "124", "118", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n8_a0_sym_s1801", "8", "101", "100", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n10_a0_asym_s2000", "10", "105", "105", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n10_a60_sym_s2007", "10", "137", "122", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n12_a30_asym_s2203", "12", "139", "135", "1.08%", "46.7", "0.29%", "80.0", "0.77%", "46.7"),
        ("n12_a30_sym_s2204", "12", "177", "168", "1.49%", "3.3", "0.00%", "100.0", "0.00%", "100.0"),
        ("n15_a60_asym_s2506", "15", "265", "246", "0.21%", "83.3", "0.33%", "56.7", "0.82%", "16.7"),
        ("n15_a0_sym_s2501", "15", "183", "177", "0.00%", "100.0", "0.00%", "100.0", "0.00%", "100.0"),
        ("n20_a0_asym_s3000", "20", "220", "220", "1.74%", "10.0", "2.35%", "0.0", "2.79%", "6.7"),
        ("n20_a30_sym_s3004", "20", "274", "258", "0.40%", "3.3", "0.00%", "100.0", "0.00%", "100.0"),
        ("Average (n <= 20)", "--", "--", "--", "0.45%", "67.9", "0.27%", "85.2", "0.40%", "79.1"),
    ]
    for row in small_rows:
        is_avg = "Average" in row[0]
        small_data.append([
            Paragraph(row[0], tbl_cell_bold_left if is_avg else tbl_cell_left),
            Paragraph(row[1], tbl_cell),
            Paragraph(row[2], tbl_cell),
            Paragraph(row[3], tbl_cell),
            Paragraph(row[4], tbl_cell_bold if is_avg else tbl_cell),
            Paragraph(row[5], tbl_cell),
            Paragraph(row[6], tbl_cell_bold if is_avg else tbl_cell),
            Paragraph(row[7], tbl_cell),
            Paragraph(row[8], tbl_cell_bold if is_avg else tbl_cell),
            Paragraph(row[9], tbl_cell),
        ])
    t_small = Table(small_data, colWidths=[120, 24, 34, 34, 55, 45, 55, 45, 55, 45])
    t_small.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_small)
    story.append(Spacer(1, 4))

    story.append(Paragraph("A. Overall Benchmark and Statistical Analysis", subsec_h2))
    story.append(Paragraph(
        "Table I summarizes performance across all 20 benchmark instances. ALNS-WDP achieves the lowest mean gap to the valid dual lower bound "
        "(5.47%) among all metaheuristics, compared to Simulated Annealing (6.65%), Genetic Algorithm (7.70%), and MultiStart Local Search (14.89%). "
        "Friedman rank testing across the four metaheuristics confirms significant overall differences (chi^2 = 10.50, df = 3, p = 0.0148). "
        "However, paired Wilcoxon signed-rank tests with step-down Holm-Bonferroni correction reveal that ALNS-WDP is statistically significantly "
        "superior <b>only against GA</b> (Holm p = 0.0146); differences against SA (p = 0.1281) and MultiStart_LS (p = 0.1281) fail to achieve "
        "statistical significance at alpha = 0.05.",
        body_style
    ))
    story.append(Paragraph("B. Small-Instance Optimality Comparison (n <= 20)", subsec_h2))
    story.append(Paragraph(
        "On the 11 small benchmark instances where global optima C_max* were computed via exact Held-Karp bitmask DP, Table II compares exact gap to optimum. "
        "The performance hierarchy ranks: MultiStart_LS (0.27%) &lt; SA (0.40%) &lt; ALNS-WDP (0.45%) &lt; GA (1.97%). ALNS-WDP hits the global optimum "
        "in 100% of runs for n &lt;= 10, dropping to 10% on n20_a0_asym and 3.3% on symmetric n12_a30_sym and n20_a30_sym.",
        body_style
    ))

    # =========================================================================
    # SWITCH BACK TO TWO-COLUMN TEMPLATE FOR BODY SECTIONS & TABLES III, IV, V
    # =========================================================================
    story.append(NextPageTemplate('two_col'))
    story.append(PageBreak())

    # TABLE III: STRATIFIED TOPOLOGY (FITS 258 pt COLUMN WIDTH)
    story.append(Paragraph("TABLE III: Stratified Performance: Asymmetric vs Symmetric Topologies", caption_style))
    strat_data = [
        [Paragraph("<b>Topology</b>", tbl_hdr_cell_left),
         Paragraph("<b>Algorithm</b>", tbl_hdr_cell_left),
         Paragraph("<b>Gap (%)</b>", tbl_hdr_cell),
         Paragraph("<b>C_max</b>", tbl_hdr_cell),
         Paragraph("<b>W/T/L</b>", tbl_hdr_cell),
         Paragraph("<b>Imprv</b>", tbl_hdr_cell)]
    ]
    strat_rows = [
        ("Asym (9)", "ALNS_WDP", "4.38", "612.6", "--", "--"),
        ("Asym (9)", "SA", "7.38", "653.8", "6W/2T/1L", "+2.69%"),
        ("Asym (9)", "GA", "9.15", "652.5", "9W/0T/0L", "+4.34%"),
        ("Asym (9)", "MultiStart_LS", "19.24", "830.7", "6W/2T/1L", "+10.12%"),
        ("Sym (11)", "ALNS_WDP", "6.37", "415.5", "--", "--"),
        ("Sym (11)", "SA", "6.06", "415.3", "3W/4T/4L", "-0.29%"),
        ("Sym (11)", "GA", "6.52", "415.6", "6W/3T/2L", "+0.13%"),
        ("Sym (11)", "MultiStart_LS", "11.32", "467.3", "3W/4T/4L", "+3.75%"),
    ]
    for row in strat_rows:
        is_alns = row[1] == "ALNS_WDP"
        strat_data.append([
            Paragraph(row[0], tbl_cell_left),
            Paragraph(row[1], tbl_cell_bold_left if is_alns else tbl_cell_left),
            Paragraph(row[2], tbl_cell_bold if is_alns else tbl_cell),
            Paragraph(row[3], tbl_cell),
            Paragraph(row[4], tbl_cell),
            Paragraph(row[5], tbl_cell),
        ])
    t_strat = Table(strat_data, colWidths=[44, 58, 38, 36, 44, 38])
    t_strat.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_strat)
    story.append(Spacer(1, 4))

    story.append(Paragraph("C. Stratified Setup Topology Analysis (Exploratory)", subsec_h2))
    story.append(Paragraph(
        "Table III reports an exploratory post-hoc breakdown between asymmetric (9 instances) and symmetric Euclidean (11 instances) setups. "
        "ALNS-WDP decisively sweeps asymmetric instances (9/9 wins vs GA, +2.69% mean makespan improvement vs SA, +10.12% vs MultiStart_LS). "
        "Conversely, on symmetric instances with alpha = 0.3, MultiStart_LS and SA slightly outperform ALNS-WDP (-0.29% vs SA; 3 wins, 4 ties, 4 losses; "
        "GA beats ALNS-WDP on n100_a30_sym).",
        body_style
    ))

    story.append(Paragraph("D. Bi-Objective Frontier Evaluation", subsec_h2))
    story.append(Paragraph(
        "We benchmarked the bi-objective extension (C_max, sum w_j T_j) against NSGA-II across 6 instances over 15 seeds per method. "
        "Evaluated via Hypervolume (HV) and Inverted Generational Distance (IGD), ALNS-WDP achieves lower IGD on 3/6 instances (statistically significant "
        "on 1/6, Holm p = 0.0018), whereas NSGA-II achieves higher Hypervolume on 5/6 instances (all 5 Holm p &lt;= 0.0018).<br/>"
        "<i>Algorithmic Mechanism:</i> While the outer loop of ALNS-WDP optimizes a scalarized objective f_lambda(pi), the internal sliding-window DP subroutine "
        "minimizes <b>makespan only</b>. For lambda &lt;= 0.5, DP window moves frequently reduce makespan at the expense of weighted tardiness and are subsequently "
        "rejected by the outer scalarized filter. In contrast, NSGA-II optimizes Pareto dominance directly over both criteria.",
        body_style
    ))

    # =========================================================================
    # SECTION VII: SENSITIVITY ANALYSIS AND ABLATION
    # =========================================================================
    story.append(Paragraph("VII. SENSITIVITY ANALYSIS AND ABLATION", sec_h1))
    story.append(Paragraph("A. Component Factorial Ablation", subsec_h2))
    story.append(Paragraph(
        "We conducted a factorial ablation across 8 problem instances x 5 variants x 15 seeds = 600 runs under matched budgets (Table IV).",
        body_style
    ))

    # TABLE IV: COMPONENT ABLATION (FITS 258 pt COLUMN WIDTH)
    story.append(Paragraph("TABLE IV: Component Ablation Results (600 Runs across 8 Instances)", caption_style))
    ablation_data = [
        [Paragraph("<b>Variant</b>", tbl_hdr_cell_left),
         Paragraph("<b>Gap (%)</b>", tbl_hdr_cell),
         Paragraph("<b>Makespan</b>", tbl_hdr_cell),
         Paragraph("<b>DP Imp</b>", tbl_hdr_cell),
         Paragraph("<b>Time (s)</b>", tbl_hdr_cell)]
    ]
    ablation_rows = [
        ("ALNS_WDP_Full", "5.06", "559.51", "3.53", "1.73"),
        ("WindowDP_FinalPolishOnly", "5.03", "559.93", "0.00", "1.60"),
        ("ALNS_No_AdaptWeights", "5.13", "559.67", "3.97", "1.73"),
        ("Plain_ALNS", "5.20", "561.91", "0.00", "1.73"),
        ("ALNS_No_WindowDP", "5.31", "562.35", "0.00", "1.73"),
    ]
    for row in ablation_rows:
        is_full = row[0] == "ALNS_WDP_Full"
        ablation_data.append([
            Paragraph(row[0], tbl_cell_bold_left if is_full else tbl_cell_left),
            Paragraph(row[1], tbl_cell_bold if is_full else tbl_cell),
            Paragraph(row[2], tbl_cell),
            Paragraph(row[3], tbl_cell),
            Paragraph(row[4], tbl_cell),
        ])
    t_ablation = Table(ablation_data, colWidths=[106, 38, 42, 38, 34])
    t_ablation.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_ablation)
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "Key ablation statistical findings:<br/>"
        "1. <b>Window DP Significance at Large Scale:</b> Comparing ALNS_WDP_Full against ALNS_No_WindowDP reveals statistically significant makespan "
        "reductions at n=100 (asymmetric: Holm p = 0.0086; symmetric: Holm p = 0.0157).<br/>"
        "2. <b>Terminal vs. Iterative DP:</b> No statistically significant difference was detected between ALNS_WDP_Full (gap 5.06%) and WindowDP_FinalPolishOnly (gap 5.03%).<br/>"
        "3. <b>Small-Scale Insensitivity:</b> For n &lt;= 50, differences between DP variants are not statistically significant (p &gt; 0.05).<br/>"
        "4. <b>Adaptive Bandit Weights:</b> Comparing ALNS_WDP_Full against ALNS_No_AdaptWeights yielded Holm p = 1.000 across all tested instances, "
        "demonstrating that adaptive operator weighting provided no measurable benefit over static uniform weights.",
        body_style
    ))

    story.append(Paragraph("B. Controlled Setup-Time Dominance Sensitivity", subsec_h2))
    story.append(Paragraph(
        "To rigorously evaluate RQ3 without confounding variables, we conducted a controlled setup-dominance experiment scaling setup matrices by "
        "beta in {0.1, 0.5, 1.0, 2.0, 5.0}, yielding rho_s in [0.06, 4.30] across four representative base instances (n=30 and n=50, asymmetric and symmetric, alpha=0.3) "
        "while holding p_j, r_j, s0_j strictly invariant. All four algorithms were evaluated across 30 paired random seeds under nominal budgets "
        "(0.90 s for n=30, 1.50 s for n=50, totaling 2,400 runs, Table V and Figure 8).<br/>"
        "<b>Computational Budget Audit:</b> ALNS-WDP, SA, and GA adhere strictly to nominal limits (0.89 s / 1.50 s). MultiStart_LS exhibited an average +6.6% overrun "
        "(0.96 s / 1.60 s) because active 2-opt descent iterations run to completion without interruption.<br/>"
        "<b>Discretization Effects:</b> For beta &gt;= 1.0, 0% of arcs were zero. At beta=0.1, integer rounding produced 27.8% to 42.4% zero-setup arcs, shifting the landscape toward arrival bottlenecks.",
        body_style
    ))

    # TABLE V: SETUP DOMINANCE (FITS 258 pt COLUMN WIDTH)
    story.append(Paragraph("TABLE V: Controlled Setup Dominance Sensitivity: Mean Gap to Lower Bound (%) across Scaling Factors beta in [0.1, 5.0] (30 Seeds/Cell)", caption_style))
    rho_data = [
        [Paragraph("<b>Scale (beta)</b>", tbl_hdr_cell_left),
         Paragraph("<b>Ratio (rho)</b>", tbl_hdr_cell),
         Paragraph("<b>ALNS (%)</b>", tbl_hdr_cell),
         Paragraph("<b>SA (%)</b>", tbl_hdr_cell),
         Paragraph("<b>GA (%)</b>", tbl_hdr_cell),
         Paragraph("<b>MS-LS (%)</b>", tbl_hdr_cell)]
    ]
    rho_rows = [
        ("n=30, Asym (alpha=0.3)", "--", "--", "--", "--", "--"),
        ("  0.1", "0.07", "0.65", "1.06", "1.48", "0.91"),
        ("  0.5", "0.40", "3.26", "7.34", "10.20", "8.15"),
        ("  1.0", "0.79", "4.51", "9.74", "13.26", "9.79"),
        ("  2.0", "1.58", "7.52", "14.55", "20.81", "19.42"),
        ("  5.0", "3.96", "13.49", "23.49", "30.01", "34.55"),
        ("n=30, Sym (alpha=0.3)", "--", "--", "--", "--", "--"),
        ("  0.1", "0.06", "1.36", "1.53", "1.75", "1.31"),
        ("  0.5", "0.30", "3.92", "3.77", "4.74", "3.30"),
        ("  1.0", "0.60", "6.87", "5.64", "7.49", "5.21"),
        ("  2.0", "1.21", "7.91", "8.05", "10.08", "7.44"),
        ("  5.0", "3.02", "11.72", "11.50", "14.41", "11.22"),
        ("n=50, Asym (alpha=0.3)", "--", "--", "--", "--", "--"),
        ("  0.1", "0.08", "0.76", "1.17", "1.13", "4.20"),
        ("  0.5", "0.43", "5.90", "10.94", "10.96", "24.81"),
        ("  1.0", "0.86", "7.46", "13.25", "15.21", "37.31"),
        ("  2.0", "1.72", "9.22", "21.96", "24.54", "65.17"),
        ("  5.0", "4.30", "12.87", "35.63", "43.18", "118.30"),
        ("n=50, Sym (alpha=0.3)", "--", "--", "--", "--", "--"),
        ("  0.1", "0.06", "0.62", "1.10", "1.01", "1.66"),
        ("  0.5", "0.33", "6.08", "5.99", "5.74", "12.62"),
        ("  1.0", "0.66", "7.95", "7.33", "9.00", "19.94"),
        ("  2.0", "1.32", "10.80", "9.79", "11.77", "29.07"),
        ("  5.0", "3.29", "15.34", "14.97", "16.41", "36.51"),
    ]
    for row in rho_rows:
        is_subhdr = "--" in row[1]
        rho_data.append([
            Paragraph(row[0], tbl_cell_bold_left if is_subhdr else tbl_cell_left),
            Paragraph(row[1], tbl_cell),
            Paragraph(row[2], tbl_cell_bold if not is_subhdr else tbl_cell),
            Paragraph(row[3], tbl_cell),
            Paragraph(row[4], tbl_cell),
            Paragraph(row[5], tbl_cell),
        ])
    t_rho = Table(rho_data, colWidths=[66, 38, 38, 38, 38, 40])
    t_rho.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 1.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_rho)
    story.append(Spacer(1, 4))

    # FIGURE 8 (FITS 258 pt COLUMN WIDTH, KEPT TOGETHER WITH CAPTION)
    fig8_path = Path("figures/fig8_sensitivity_rho.png")
    if fig8_path.exists():
        story.append(KeepTogether([
            Image(str(fig8_path), width=254, height=125),
            Spacer(1, 2),
            Paragraph("<b>Figure 8:</b> Controlled setup-time dominance sensitivity: Mean gap to valid lower bound (%) vs. ratio rho_s = s_bar / p_bar across four base instances under matched nominal wall-clock budgets (30 seeds per cell).", caption_style),
            Spacer(1, 4),
        ]))

    story.append(Paragraph(
        "<b>Statistical Analysis across Dual Hypothesis Families:</b> We define two distinct inferential families across the 60 pairwise comparisons:<br/>"
        "1. <b>Exploratory Family (m=3 per configuration):</b> Step-down Holm correction within each individual (base, beta) setting.<br/>"
        "2. <b>Confirmatory Family (m=60 global):</b> Global Holm-Bonferroni correction across the entire experimental suite.<br/>"
        "<i>Key Findings:</i><br/>"
        "• <b>Asymmetric Dominance of ALNS-WDP:</b> On asymmetric setups, ALNS-WDP sweeps 10/10 pairwise tests against SA, GA, MultiStart_LS under both exploratory "
        "and global corrections (all global Holm p &lt; 0.0001). As setup dominance increases from rho_s ~ 0.08 to rho_s ~ 4.30, ALNS-WDP's makespan advantage over SA "
        "expands from -0.41% to -16.78% on n=50, and from -0.41% to -8.10% on n=30.<br/>"
        "• <b>Symmetric Competitiveness of 2-Opt:</b> On symmetric setups, MultiStart_LS and SA outperform ALNS-WDP at moderate-to-high setup ratios. On n30_a30_sym "
        "at beta=1.0, MultiStart_LS achieves 28 wins, 1 tie, 1 loss vs ALNS-WDP (global Holm p &lt; 0.0001), while SA achieves 27 wins, 0 ties, 3 losses (global Holm p &lt; 0.0001).<br/>"
        "• <b>Reassessment on Large Symmetric Instances:</b> Under exploratory correction (m=3), SA appeared significantly superior to ALNS-WDP on n50_a30_sym at beta=2.0 "
        "(raw p = 0.0300, exploratory Holm p = 0.0435). However, under the confirmatory global family (m=60), global Holm p = 0.3295, failing significance.",
        body_style
    ))

    # =========================================================================
    # SECTION VIII: LIMITATIONS AND THREATS TO VALIDITY
    # =========================================================================
    story.append(Paragraph("VIII. LIMITATIONS AND THREATS TO VALIDITY", sec_h1))
    story.append(Paragraph(
        "1. <b>Single Instance at n=200:</b> The scalability evaluation at n=200 is based on a single instance (n200_a30_asym_s21003). Multi-instance distributions were tested for n &lt;= 100.<br/>"
        "2. <b>Exploratory Topology Analysis:</b> The 20-instance benchmark grid contains one instance per (n, alpha, topology) cell. While the controlled setup-dominance experiment corroborated the split on 4 base instances, broader generalizability across arbitrary arrival patterns requires qualification.<br/>"
        "3. <b>2-Opt Reversal Advantage as a Hypothesis:</b> The superior performance of 2-opt descent on symmetric Euclidean setups is an architectural hypothesis—namely, that segment reversals pi(i ... j) -&gt; pi(j ... i) untangle Euclidean crossings without changing internal transition costs (s_uv = s_vu)—supported by empirical convergence, rather than a proven causal theorem.<br/>"
        "4. <b>Bi-Objective DP Scope:</b> Window-DP optimizes makespan only, explaining why NSGA-II attains higher Hypervolume.<br/>"
        "5. <b>Ablation Runtime Overhead:</b> Due to Python interpreter overhead during operator selection, full ALNS variants ran up to 1.15x longer than WindowDP_FinalPolishOnly on small instances.<br/>"
        "6. <b>Negative Finding on Adaptive Weights:</b> Bandit operator adaptation showed no statistically significant benefit over static weights (p = 1.000).",
        body_style
    ))

    # =========================================================================
    # SECTION IX: CONCLUSION
    # =========================================================================
    story.append(Paragraph("IX. CONCLUSION", sec_h1))
    story.append(Paragraph(
        "This investigation analyzed single-machine scheduling from its polynomial base case (1 || C_max) to its strongly NP-hard generalization "
        "(1 | r_j, s_ij | C_max). We proposed and evaluated ALNS-WDP, a hybrid metaheuristic combining Adaptive Large Neighborhood Search with exact "
        "sliding-window Held-Karp dynamic programming. Empirical benchmarking across 20 instances up to n=200 demonstrated that ALNS-WDP achieves a "
        "lower mean gap to valid lower bound (5.47%) than SA (6.65%), GA (7.70%), and MultiStart_LS (14.89%), with improvements statistically significant "
        "only against GA (Holm p = 0.0146) and not significant against SA or MultiStart_LS (p = 0.1281). Controlled setup-dominance experiments "
        "demonstrated that ALNS-WDP's advantage expands dramatically on asymmetric setups as setup costs dominate (Holm p &lt; 0.0001), while reversal-based "
        "local search appears competitive on symmetric Euclidean setups, although the underlying mechanism remains a hypothesis requiring further investigation.",
        body_style
    ))

    # =========================================================================
    # REFERENCES (IN TWO COLUMNS)
    # =========================================================================
    story.append(Paragraph("REFERENCES", sec_h1))
    references = [
        "[1] M. L. Pinedo, <i>Scheduling: Theory, Algorithms, and Systems</i>, 5th ed. Springer, New York, 2016.",
        "[2] R. L. Graham, E. L. Lawler, J. K. Lenstra, and A. H. G. Rinnooy Kan, \"Optimization and approximation in deterministic sequencing and scheduling: a survey,\" <i>Annals of Discrete Mathematics</i>, vol. 5, pp. 287-326, 1979.",
        "[3] M. R. Garey and D. S. Johnson, <i>Computers and Intractability: A Guide to the Theory of NP-Completeness</i>. W. H. Freeman and Company, San Francisco, 1979.",
        "[4] S. Ropke and D. Pisinger, \"An adaptive large neighborhood search heuristic for the pickup and delivery problem with time windows,\" <i>Transportation Science</i>, vol. 40, no. 4, pp. 455-472, 2006, doi: 10.1287/trsc.1050.0135.",
        "[5] D. Pisinger and S. Ropke, \"Large neighborhood search,\" in <i>Handbook of Metaheuristics</i>, M. Gendreau and J.-Y. Potvin, Eds. Springer, Boston, MA, 2010, pp. 399-419, doi: 10.1007/978-1-4419-1665-5_13.",
        "[6] P. Shaw, \"Using constraint programming and local search methods to solve vehicle routing problems,\" in <i>Principles and Practice of Constraint Programming (CP98)</i>, LNCS 1520:417-431. Springer, 1998, doi: 10.1007/3-540-49481-2_30.",
        "[7] M. Held and R. M. Karp, \"A dynamic programming approach to sequencing problems,\" <i>Journal of the Society for Industrial and Applied Mathematics</i>, vol. 10, no. 1, pp. 196-210, 1962, doi: 10.1137/0110015.",
        "[8] E. Balas and N. Simonetti, \"Linear time dynamic-programming algorithms for new classes of restricted TSPs: A computational study,\" <i>INFORMS Journal on Computing</i>, vol. 13, no. 1, pp. 56-75, 2001, doi: 10.1287/ijoc.13.1.56.9748.",
        "[9] R. K. Congram, C. N. Potts, and S. L. van de Velde, \"An iterated dynasearch algorithm for the single-machine total weighted tardiness scheduling problem,\" <i>INFORMS Journal on Computing</i>, vol. 14, no. 1, pp. 52-67, 2002, doi: 10.1287/ijoc.14.1.52.7712.",
        "[10] F. Sourd, \"Dynasearch for the earliness-tardiness scheduling problem with release dates and setup constraints,\" <i>Operations Research Letters</i>, vol. 34, no. 5, pp. 591-598, 2006, doi: 10.1016/j.orl.2005.06.005.",
        "[11] A. Allahverdi, \"The third comprehensive review on scheduling problems with setup times/costs,\" <i>European Journal of Operational Research</i>, vol. 246, no. 2, pp. 345-378, 2015, doi: 10.1016/j.ejor.2015.04.004.",
        "[12] C. Archetti and M. G. Speranza, \"A survey on matheuristics for routing problems,\" <i>EURO Journal on Computational Optimization</i>, vol. 2, no. 4, pp. 223-246, 2014, doi: 10.1007/s13675-014-0030-7.",
        "[13] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan, \"A fast and elitist multiobjective genetic algorithm: NSGA-II,\" <i>IEEE Transactions on Evolutionary Computation</i>, vol. 6, no. 2, pp. 182-197, 2002, doi: 10.1109/4235.996017.",
        "[14] H. W. Kuhn, \"The Hungarian method for the assignment problem,\" <i>Naval Research Logistics Quarterly</i>, vol. 2, no. 1-2, pp. 83-97, 1955, doi: 10.1002/nav.3800020109.",
    ]
    for ref in references:
        story.append(Paragraph(ref, ref_style))

    # =========================================================================
    # APPENDIX: TRACEABILITY MATRIX (FULL WIDTH TEMPLATE)
    # =========================================================================
    story.append(NextPageTemplate('full_page'))
    story.append(PageBreak())

    story.append(Paragraph("APPENDIX: CLAIM-TO-EVIDENCE TRACEABILITY MATRIX", sec_h1))
    story.append(Paragraph("Table VI maps every empirical claim in this report to its exact source file in results/ and the producing script.", body_style))
    story.append(Spacer(1, 4))

    trace_data = [
        [Paragraph("<b>Claim in Report</b>", tbl_hdr_cell_left),
         Paragraph("<b>Evidence File</b>", tbl_hdr_cell_left),
         Paragraph("<b>Generating Script</b>", tbl_hdr_cell_left)]
    ]
    trace_rows = [
        ("20 benchmark instances, 30 seeds", "results/single_objective_benchmarks.csv", "src/experiments.py"),
        ("ALNS-WDP mean gap to LB = 5.47%", "results/single_objective_benchmarks.csv", "tools/rerun_budget_enforced.py"),
        ("ALNS-WDP gap to opt (n <= 20) = 0.45%", "results/single_objective_benchmarks.csv", "tools/rerun_budget_enforced.py"),
        ("Competitor gaps: SA 6.65%, GA 7.70%", "results/single_objective_benchmarks.csv", "src/experiments.py"),
        ("MultiStart_LS gap = 14.89%, rt = 1.42s", "results/single_objective_benchmarks.csv", "tools/rerun_multistart_ls.py"),
        ("Friedman test chi^2 = 10.50, p = 0.0148", "results/friedman_ranks.csv", "src/stats.py"),
        ("Wilcoxon Holm p: GA 0.0146, SA 0.1281", "results/metaheuristic_statistical_tests.csv", "src/stats.py"),
        ("Ablation: 600 runs, full gap = 5.06%", "results/ablation_results.csv", "tools/rerun_budget_enforced.py"),
        ("Sensitivity to window size k", "results/sensitivity_k.csv", "src/experiments.py"),
        ("Bi-objective HV and IGD metrics", "results/biobjective_metrics.csv", "tools/rerun_budget_enforced.py"),
        ("Stratified topology comparison", "results/stratified_topology_comparison.csv", "src/stats.py"),
        ("Bi-objective Wilcoxon + Holm tests", "results/biobjective_statistical_tests.csv", "src/stats.py"),
        ("Controlled setup dominance (2400 runs)", "results/sensitivity_rho.csv", "tools/run_rho_sensitivity.py"),
        ("Controlled setup dominance summary", "results/sensitivity_rho_summary.csv", "tools/run_rho_sensitivity.py"),
        ("Controlled setup dominance stats", "results/sensitivity_rho_statistical_tests.csv", "tools/run_rho_sensitivity.py"),
        ("Setup dominance figure", "figures/fig8_sensitivity_rho.png", "tools/run_rho_sensitivity.py"),
    ]
    for row in trace_rows:
        trace_data.append([
            Paragraph(row[0], tbl_cell_left),
            Paragraph(f"<font name='Courier'>{row[1]}</font>", tbl_cell_left),
            Paragraph(f"<font name='Courier'>{row[2]}</font>", tbl_cell_left),
        ])
    t_trace = Table(trace_data, colWidths=[170, 210, 160])
    t_trace.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("PADDING", (0, 0), (-1, -1), 2.5),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))
    story.append(t_trace)

    doc.build(story, canvasmaker=IEEENumberedCanvas)
    print(f"Research Report successfully compiled at {pdf_path}")


if __name__ == "__main__":
    build_pdf_report("report/report.pdf")
