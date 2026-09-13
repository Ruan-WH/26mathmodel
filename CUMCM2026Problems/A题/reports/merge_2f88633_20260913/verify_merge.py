"""Audit the 2f88633 merge without executing numerical or submitted source code.

Only merge_checks.json in this report directory is written. Existing appendix
verification functions are reused; the obsolete page-by-page body comparator is
deliberately not called because the remote bibliography occupied two pages.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True
import pymupdf

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
WORKSPACE = PROJECT.parents[1]
PAPER = PROJECT / "paper/cumcm-1.1.0"
PREVIOUS = PROJECT / "reports/appendix_results_20260913"
REMOTE = "2f88633013e12143fcc6cd969fb9e38412af6b50"
LOCAL_BASELINE = "edfa9bc"
SOURCE_EXTENSIONS = {".py", ".java", ".ps1", ".sh"}
DATA_EXTENSIONS = {".json", ".csv", ".npz", ".xlsx", ".txt"}

spec = importlib.util.spec_from_file_location("appendix_verification_readonly", PREVIOUS / "verify_appendices.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(data: bytes) -> str:
    return old.normalize_newlines(data.decode("utf-8-sig"))


def git_read(revision: str, path: Path) -> bytes:
    relative = path.resolve().relative_to(WORKSPACE.resolve()).as_posix()
    return subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=WORKSPACE)


def active_tree(revision: str | None) -> dict[str, str]:
    """Resolve actual input/include calls; include appendix dependencies too."""
    seen = {}

    def visit(name):
        if name in seen:
            return
        path = PAPER / name
        data = git_read(revision, path) if revision else path.read_bytes()
        text = normalized(data)
        seen[name] = text
        for child in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", old.strip_tex_comments(text)):
            visit(child if child.endswith(".tex") else child + ".tex")
    visit("main.tex")
    return seen


def bibitems(text: str) -> list[dict]:
    pattern = r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})"
    return [{"key": m.group(1), "paragraph": " ".join(m.group(2).split())}
            for m in re.finditer(pattern, old.strip_tex_comments(text), re.S)]


def check_remote_text(report):
    before, current = active_tree(REMOTE), active_tree(None)
    checks = []
    remote_body = {n for n in before if not n.startswith("contents/appendix/")}
    current_body = {n for n in current if not n.startswith("contents/appendix/")}
    old.require(report, remote_body == current_body, "active_body_include_tree_preserved",
                missing=sorted(remote_body-current_body), extra=sorted(current_body-remote_body))
    for name in sorted(remote_body):
        if name == "contents/references.tex":
            continue
        same = before[name] == current.get(name)
        checks.append({"file": name, "normalized_content_identical": same,
                       "remote_utf8_content_sha256": sha(before[name].encode("utf-8")),
                       "current_utf8_content_sha256": sha(current.get(name, "").encode("utf-8"))})
        old.require(report, same, "remote_body_source_preserved", file=name)
    a, b = bibitems(before["contents/references.tex"]), bibitems(current["contents/references.tex"])
    old.require(report, len(a) == len(b) == 8 and a == b,
                "all_eight_remote_bibliography_paragraphs_preserved", remote=a, current=b)
    keys = [item["key"] for item in b]
    old.require(report, len(set(keys)) == 8, "unique_bibliography_keys")
    citations, references, labels = [], [], []
    for name, raw in current.items():
        text = old.strip_tex_comments(raw)
        for match in re.finditer(r"\\cite\w*\*?(?:\[[^]]*\]){0,2}\{([^}]+)\}", text):
            citations.extend({"key": key.strip(), "file": name,
                              "line": text[:match.start()].count("\n")+1}
                             for key in match.group(1).split(","))
        labels.extend(re.findall(r"\\label\{([^}]+)\}", text))
        for match in re.finditer(r"\\(?:[cC]|eq|page)?ref\*?\{([^}]+)\}", text):
            references.extend({"key": key.strip(), "file": name}
                              for key in match.group(1).split(","))
    absent_cites = [c for c in citations if c["key"] not in keys]
    absent_refs = [r for r in references if r["key"] not in labels]
    unused = sorted(set(keys)-{c["key"] for c in citations})
    duplicate_labels = {k: v for k, v in Counter(labels).items() if v > 1}
    old.require(report, not absent_cites, "all_citations_resolved", missing=absent_cites)
    old.require(report, not absent_refs, "all_cross_references_resolved", missing=absent_refs)
    old.require(report, not unused, "all_eight_bibliography_items_cited", unused=unused)
    old.require(report, not duplicate_labels, "no_duplicate_labels", duplicates=duplicate_labels)
    table_checks = []
    for name, text in current.items():
        if not name.startswith("contents/sections/"):
            continue
        baseline = normalized(git_read(LOCAL_BASELINE, PAPER / name))
        tables = lambda s: re.findall(r"\\begin\{table\}.*?\\end\{table\}", s, re.S)
        same = tables(text) == tables(baseline)
        table_checks.append({"file": name, "table_count": len(tables(text)), "identical": same})
        old.require(report, same, "numerical_table_source_preserved", file=name)
    report["remote_content_preservation"] = {
        "remote_commit": REMOTE, "active_body_tree": sorted(remote_body),
        "normalization": "Only UTF-8 BOM and CR/LF line-ending differences are ignored.",
        "files": checks, "reference_exception": "Local typography outside bibitem paragraphs only.",
        "bibliography": b, "bibliography_order_and_paragraphs_identical": a == b,
        "citations": citations, "undefined_citations": absent_cites,
        "undefined_cross_references": absent_refs, "unused_bibliography_keys": unused,
        "duplicate_labels": duplicate_labels, "tables_against_local_baseline": table_checks,
    }
    return b


def check_baseline_sources_and_data(manifest, report):
    records = subprocess.check_output(["git", "ls-tree", "-rz", LOCAL_BASELINE], cwd=WORKSPACE)
    prefix = PROJECT.relative_to(WORKSPACE).as_posix() + "/"
    source_names = {item["source"].replace("\\", "/") for item in manifest}
    checks = []
    for record in records.split(b"\0"):
        if not record:
            continue
        metadata, name_raw = record.split(b"\t", 1)
        name = name_raw.decode("utf-8")
        if not name.startswith(prefix):
            continue
        relative = name[len(prefix):]
        path = Path(relative)
        is_source = relative in source_names
        is_data = (path.parts[0] in {"results", "comsol_q1", "comsol_q4", "附件"}
                   and path.suffix.lower() in DATA_EXTENSIONS and "figures" not in path.parts)
        if not (is_source or is_data):
            continue
        current = (PROJECT / path).read_bytes()
        baseline_blob = metadata.split()[2].decode("ascii")
        raw_blob = hashlib.sha1(b"blob " + str(len(current)).encode("ascii") + b"\0" + current).hexdigest()
        exact = raw_blob == baseline_blob
        same = exact
        if (is_source or path.suffix.lower() in {".json", ".csv", ".txt"}) and not exact:
            same = normalized(current) == normalized(git_read(LOCAL_BASELINE, PROJECT / path))
        checks.append({"file": relative, "kind": "source" if is_source else "input_or_result",
                       "same_as_local_baseline": same, "raw_blob_identical": exact,
                       "baseline_git_blob": baseline_blob, "current_sha256": sha(current)})
        old.require(report, same, "local_model_source_or_result_preserved", file=relative)
    checked_source_names = {x["file"] for x in checks if x["kind"] == "source"}
    old.require(report, checked_source_names == source_names, "all_33_sources_match_local_baseline",
                missing=sorted(source_names-checked_source_names))
    report["model_data_preservation"] = {
        "baseline": LOCAL_BASELINE, "file_count": len(checks),
        "source_count": len(checked_source_names), "checks": checks,
        "text_comparison_policy": "Git checkout may convert LF/CRLF; source and text data content are compared with line endings normalized. Binary NPZ/XLSX bytes must match exactly.",
        "numerical_simulations_executed_in_this_audit": False,
    }


def check_prior_numerical_evidence(report):
    path = PREVIOUS / "model_freshness_checks.json"
    previous_bytes = path.read_bytes()
    previous = json.loads(previous_bytes)
    expected = {k.replace("\\", "/"): v for k, v in previous["protected_hashes_after"].items()}
    expected["code/solve_drying.py"] = previous["current_solver_sha256"]
    expected["code/write_results.py"] = previous["current_exporter_sha256"]
    expected.update({"results/" + k: v for k, v in previous["final_workbooks_sha256"].items()})
    checks = []
    for name, value in sorted(expected.items()):
        actual = sha((PROJECT / name).read_bytes())
        checks.append({"file": name, "previous_sha256": value,
                       "current_sha256": actual, "matches": actual == value})
        old.require(report, actual == value, "previous_numerical_audit_hash_still_current", file=name)
    old.require(report, previous["status"] == "PASS", "prior_numerical_report_passed")
    old.require(report, normalized(previous_bytes) == normalized(git_read(LOCAL_BASELINE, path)),
                "previous_numerical_report_preserved_from_local_baseline")
    report["prior_numerical_evidence"] = {
        "report": str(path.relative_to(PROJECT)), "sha256": sha(previous_bytes),
        "previous_status": previous["status"], "protected_files": checks,
        "still_applicable_by_hash": all(c["matches"] for c in checks),
        "previous_computation_not_repeated": True,
        "previous_verified_field_values": previous["field_value_count"],
        "previous_verified_workbook_result_cells": previous["workbook_total_result_cells_compared"],
        "previous_verified_paper_table_values": previous["paper_primary_values_compared"],
        "scope": previous["scope"],
    }


def check_final_pdf(doc, bibliography, args, report):
    a_page, b_page = old.appendix_page(doc, "A"), old.appendix_page(doc, "B")
    remote_pdf = git_read(REMOTE, PAPER / "main.pdf")
    with pymupdf.open(stream=remote_pdf, filetype="pdf") as before:
        remote_a = old.appendix_page(before, "A")
        remote_pages = len(before)
    reference_page = doc[30]
    text = old.compact(reference_page.get_text())
    evidence = []
    for i, item in enumerate(bibliography, 1):
        doi = re.search(r"DOI:\s*(\S+)", item["paragraph"]).group(1).rstrip(".")
        present = old.compact(doi) in text and f"[{i}]" in text
        evidence.append({"number": i, "key": item["key"], "doi": doi,
                         "complete_doi_and_reference_number_on_page_31": present})
        old.require(report, present, "bibliography_item_present_on_final_page_31", key=item["key"])
    old.require(report, a_page == 31, "final_body_within_30_pages",
                actual_body_pages=a_page-1, appendix_A_page=a_page+1)
    old.require(report, b_page == 35, "complete_appendix_B_starts_page_36",
                appendix_B_page=b_page+1)
    old.require(report, len(doc) == args.expected_pages, "expected_complete_pdf_pages",
                expected=args.expected_pages, actual=len(doc))
    old.require(report, remote_a-1 == 31, "remote_body_had_31_pages", actual=remote_a-1)
    report.update({"pdf_pages": len(doc), "appendix_A_page": a_page+1,
                   "appendix_B_page": b_page+1, "pdf_sha256": sha(args.pdf.read_bytes()),
                   "pdf_bytes": args.pdf.stat().st_size})
    report["body_page_count_evidence"] = {
        "abstract_pages": 1, "remote_pdf_pages": remote_pages,
        "remote_appendix_A_page": remote_a+1, "remote_body_pages": remote_a-1,
        "final_body_pages": a_page-1, "final_appendix_A_page": a_page+1,
        "final_reference_page": 31, "references": evidence,
        "policy": "Exclude the one-page abstract and appendices; include AI declaration and references.",
        "page_by_page_comparison_to_remote_deliberately_not_used": True,
    }
    return a_page, b_page


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=WORKSPACE / "tmp/merge-2f88633/main.pdf")
    parser.add_argument("--expected-pages", type=int, default=148)
    ns = parser.parse_args()
    args = SimpleNamespace(
        project=PROJECT, paper=PAPER, manifest=PREVIOUS / "source_manifest.json",
        pdf=ns.pdf.resolve(), log=ns.pdf.resolve().with_suffix(".log"),
        aux=ns.pdf.resolve().with_suffix(".aux"),
        compile_output=ns.pdf.resolve().parent / "compile-output.txt",
        render_previews=False, preview_dir=AUDIT / "unused-previews", page_tolerance=0.5,
        expected_pages=ns.expected_pages,
    )
    report = {"status": "FAIL", "audit": "2f88633 merge, references, page limit, full source appendix",
              "remote_commit": REMOTE, "local_preservation_commit": LOCAL_BASELINE,
              "pdf_path": str(args.pdf), "source_checks": [], "errors": [], "warnings": [],
              "numerical_source_execution": False, "old_compare_body_used": False}
    try:
        bibliography = check_remote_text(report)
        manifest = old.read_manifest(args.manifest)
        report["source_file_count"] = len(manifest)
        report["source_language_counts"] = dict(Counter(item["language"] for item in manifest))
        old.require(report, len(manifest) == 33, "exactly_33_complete_sources")
        old.check_sources(manifest, args, report)
        report["original_source_lines"] = sum(item["source_lines"] for item in manifest)
        old.check_latex_inputs(manifest, args, report)
        check_baseline_sources_and_data(manifest, report)
        check_prior_numerical_evidence(report)
        with pymupdf.open(args.pdf) as doc:
            a_page, b_page = check_final_pdf(doc, bibliography, args, report)
            old.check_pdf_sources(doc, manifest, a_page, b_page, args, report)
            old.check_log(doc, manifest, args, report)
            old.check_pdf_integrity(doc, a_page, args, report)
            report["visual_review"] = {
                "performed_by": "Root agent, confirmed in this merge task",
                "pages_reviewed": [1, 31, 32],
                "pdf_sha256": sha(args.pdf.read_bytes()),
                "findings": "All eight references are clear on page 31; reference font and line spacing are readable; AI declaration retains body line spacing; abstract and appendix opening visually checked.",
                "automated_script_does_not_claim_independent_visual_review": True,
            }
    except Exception as exc:
        report["errors"].append({"check": "verification_could_not_finish",
                                 "exception": type(exc).__name__, "message": str(exc)})
    report["status"] = "FAIL" if report["errors"] else ("PASS_WITH_NOTES" if report["warnings"] else "PASS")
    destination = AUDIT / "merge_checks.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "pdf_pages": report.get("pdf_pages"),
                      "appendix_A_page": report.get("appendix_A_page"),
                      "appendix_B_page": report.get("appendix_B_page"),
                      "source_file_count": report.get("source_file_count"),
                      "errors": report["errors"], "warnings": report["warnings"],
                      "report": str(destination)}, ensure_ascii=False, indent=2))
    return bool(report["errors"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
