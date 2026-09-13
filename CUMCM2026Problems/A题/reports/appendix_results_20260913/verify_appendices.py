"""Verify the manifest-driven source appendix without running any submitted code.

Default body boundary: one abstract page plus thirty manuscript pages.  Appendix
titles and source labels determine the actual appendix ranges; an appendix list
may occupy any number of pages.  Pixel differences are reported separately from
text/layout changes because different TeX engines can rasterize identical text
differently.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

import pymupdf
from PIL import Image, ImageChops, ImageDraw, ImageStat

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
PAPER = PROJECT / "paper/cumcm-1.1.0"
WORKSPACE = PROJECT.parents[1]
BASELINE = WORKSPACE / "tmp/source-sync-5ae7984/main-before.pdf"
LANGUAGES = {".py": "Python", ".java": "Java", ".ps1": "PowerShell", ".sh": "Bash"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def compact(text: str) -> str:
    """Ignore extraction whitespace and typographic quote variants, not content."""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans({"−": "-", "‘": "'", "’": "'", "“": '"', "”": '"'}))
    return re.sub(r"\s+", "", text)


def strip_tex_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def within(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Manifest path escapes its root: {relative}")
    return path


def require(report: dict, condition: bool, code: str, **details) -> bool:
    if not condition:
        report["errors"].append({"check": code, **details})
    return condition


def warning(report: dict, code: str, **details) -> None:
    report["warnings"].append({"check": code, **details})


def read_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        data = data.get("sources", data.get("files"))
    if not isinstance(data, list) or not data:
        raise ValueError("The source manifest must contain a nonempty list of source files")
    return data


def check_sources(manifest: list[dict], args, report: dict) -> list[str]:
    normalized_sources = []
    seen_sources, seen_copies = set(), set()
    for number, item in enumerate(manifest, 1):
        source_name = Path(item["source"]).as_posix()
        copy_name = Path(item["appendix_copy"]).as_posix()
        check = {"index": number, "source": source_name, "appendix_copy": copy_name}
        report["source_checks"].append(check)
        require(report, source_name not in seen_sources, "duplicate_source", source=source_name)
        require(report, copy_name not in seen_copies, "duplicate_appendix_copy", copy=copy_name)
        seen_sources.add(source_name)
        seen_copies.add(copy_name)
        try:
            original_path = within(args.project, source_name)
            copy_path = within(args.paper, copy_name)
            raw, copied_raw = original_path.read_bytes(), copy_path.read_bytes()
            original = normalize_newlines(raw.decode("utf-8-sig"))
            copied = normalize_newlines(copied_raw.decode("utf-8-sig"))
            normalized_sources.append(original)
            expected_language = LANGUAGES.get(original_path.suffix.lower())
            language = item.get("language", expected_language)
            check["language"] = language
            require(report, expected_language is not None and language == expected_language,
                    "source_language_matches_extension", source=source_name,
                    declared=language, expected=expected_language)
            prefix = "//" if language == "Java" else "#"
            comment = f"{prefix} File: {source_name}"
            check.update({
                "source_sha256": digest(raw),
                "appendix_sha256": digest(copied_raw),
                "source_lines": len(original.splitlines()),
                "filename_comment": comment,
                "first_source_line": next((s for s in original.splitlines() if s.strip()), ""),
                "last_source_line": next((s for s in reversed(original.splitlines()) if s.strip()), ""),
            })
            require(report, item.get("first_line") == comment,
                    "manifest_filename_comment", source=source_name,
                    expected=comment, actual=item.get("first_line"))
            require(report, copied == comment + "\n" + original,
                    "full_source_identical_after_filename_comment", source=source_name)
            check["full_source_identical"] = copied == comment + "\n" + original
            require(report, digest(raw) == item.get("source_sha256"),
                    "source_manifest_hash", source=source_name)
            require(report, digest(copied_raw) == item.get("appendix_sha256"),
                    "appendix_manifest_hash", source=source_name)
            require(report, len(original.splitlines()) == item.get("source_lines"),
                    "source_manifest_line_count", source=source_name,
                    actual=len(original.splitlines()), declared=item.get("source_lines"))
            if language == "Python":
                # Parsing/compilation creates code objects only; no imports or numerical runs.
                parsed = ast.parse(copied, filename=source_name)
                compile(parsed, source_name, "exec")
                check["syntax_check"] = "Python AST parse and compile passed; not executed"
            else:
                check["syntax_check"] = "Not executed or compiled; exact source copy verified"
        except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
            if len(normalized_sources) < number:
                normalized_sources.append("")
            check["error"] = str(exc)
            require(report, False, "source_check_failed", source=source_name, error=str(exc))
    return normalized_sources


def source_listing_blocks(a2_text: str) -> list[dict]:
    text = strip_tex_comments(a2_text)
    listings = []
    pattern = re.compile(r"\\lstinputlisting\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}")
    for match in pattern.finditer(text):
        starts = list(re.finditer(r"\\label\{app:source(\d+)\}", text[:match.start()]))
        end = re.search(r"\\label\{app:source(\d+)end\}", text[match.end():])
        listings.append({
            "path": Path(match.group(2)).as_posix(),
            "options": match.group(1) or "",
            "start_label": int(starts[-1].group(1)) if starts else None,
            "end_label": int(end.group(1)) if end else None,
        })
    return listings


def check_latex_inputs(manifest: list[dict], args, report: dict) -> None:
    a1 = (args.paper / "contents/appendix/a1.tex").read_text(encoding="utf-8")
    a2 = (args.paper / "contents/appendix/a2.tex").read_text(encoding="utf-8")
    blocks = source_listing_blocks(a2)
    report["latex_listing_count"] = len(blocks)
    require(report, len(blocks) == len(manifest), "listing_count",
            expected=len(manifest), actual=len(blocks))
    text = strip_tex_comments(a2)
    for suffix in ("", "end"):
        labels = re.findall(r"\\label\{app:source(\d+)" + suffix + r"\}", text)
        require(report, Counter(map(int, labels)) == Counter(range(1, len(manifest) + 1)),
                "source_label_coverage", suffix=suffix, labels=labels)
    a1_compact = compact(strip_tex_comments(a1))
    for index, item in enumerate(manifest, 1):
        check = report["source_checks"][index - 1]
        require(report, compact(item["source"]) in a1_compact,
                "source_listed_in_appendix_A_tex", source=item["source"])
        if index > len(blocks):
            continue
        block = blocks[index - 1]
        check["latex_listing"] = block
        require(report, block["path"] == Path(item["appendix_copy"]).as_posix(),
                "listing_path_matches_manifest", source=item["source"], listing=block)
        require(report, block["start_label"] == index and block["end_label"] == index,
                "listing_labels_bracket_source", source=item["source"], listing=block)
        require(report, not re.search(r"\b(firstline|lastline|linerange)\s*=", block["options"]),
                "listing_has_no_source_truncation", source=item["source"], options=block["options"])


def appendix_page(doc, letter: str) -> int:
    """Find an actual appendix heading near the top, not a mention in prose."""
    for index, page in enumerate(doc):
        text = compact(page.get_text())
        if re.match(r"附录" + re.escape(letter) + r"(?=[^A-Za-z]|$)", text):
            return index
        # Some engines put a short running header before the chapter title.
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                if line["bbox"][1] < page.rect.height * 0.24:
                    lines.append("".join(span["text"] for span in line["spans"]))
        heading = compact("".join(lines))
        if re.search(r"附录" + re.escape(letter) + r"(?:支撑|源|核心|完整)", heading):
            return index
    raise ValueError(f"Cannot locate the actual appendix {letter} heading in the PDF")


def page_lines(page) -> list[tuple[str, tuple]]:
    result = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = compact("".join(span["text"] for span in line["spans"]))
            if text:
                result.append((text, tuple(line["bbox"])))
    return result


def compare_body(doc, baseline, a_page: int, args, report: dict) -> None:
    baseline_a = appendix_page(baseline, "A")
    expected = args.abstract_pages + args.body_pages
    report["body_layout_policy"] = {
        "allow_body_reflow": args.allow_body_reflow,
        "actual_pdf_producer": doc.metadata.get("producer"),
        "baseline_pdf_producer": baseline.metadata.get("producer"),
        "text_and_page_count_checks_remain_strict": True,
        "text_line_reflow_pages": [],
        "bbox_only_difference_pages": [],
    }
    report["body_boundary"] = {
        "abstract_pages_expected": args.abstract_pages,
        "manuscript_pages_expected": args.body_pages,
        "preserved_prefix_pages_expected": expected,
        "actual_preserved_prefix_pages": a_page,
        "baseline_preserved_prefix_pages": baseline_a,
    }
    require(report, a_page == expected, "abstract_plus_body_page_count",
            expected_appendix_A_page=expected + 1, actual_appendix_A_page=a_page + 1)
    require(report, baseline_a == expected, "baseline_body_page_count",
            expected=expected, actual=baseline_a)
    count = min(expected, a_page, baseline_a, len(doc), len(baseline))
    for index in range(count):
        actual, before = doc[index], baseline[index]
        actual_text, before_text = actual.get_text(), before.get_text()
        left, right = page_lines(actual), page_lines(before)
        same_lines = [line[0] for line in left] == [line[0] for line in right]
        displacement = (max((abs(x-y) for a, b in zip(left, right)
                             for x, y in zip(a[1], b[1])), default=0.0)
                        if same_lines else None)
        actual_pix = actual.get_pixmap(matrix=pymupdf.Matrix(1, 1),
                                       colorspace=pymupdf.csRGB, alpha=False)
        before_pix = before.get_pixmap(matrix=pymupdf.Matrix(1, 1),
                                       colorspace=pymupdf.csRGB, alpha=False)
        size_equal = (actual_pix.width, actual_pix.height) == (before_pix.width, before_pix.height)
        pixel_equal = size_equal and actual_pix.samples == before_pix.samples
        check = {
            "page": index + 1,
            "exact_text_equal": actual_text == before_text,
            "normalized_text_equal": compact(actual_text) == compact(before_text),
            "line_text_sequence_equal": same_lines,
            "max_line_bbox_displacement_pt": displacement,
            "line_layout_tolerance_pt": args.layout_tolerance,
            "page_size_equal": tuple(actual.rect) == tuple(before.rect),
            "pixels_identical": pixel_equal,
            "actual_render_sha256": digest(actual_pix.samples),
            "baseline_render_sha256": digest(before_pix.samples),
        }
        if size_equal and not pixel_equal:
            im_a = Image.frombytes("RGB", (actual_pix.width, actual_pix.height), actual_pix.samples)
            im_b = Image.frombytes("RGB", (before_pix.width, before_pix.height), before_pix.samples)
            difference = ImageChops.difference(im_a, im_b)
            channel_max = ImageChops.lighter(ImageChops.lighter(*difference.split()[:2]),
                                            difference.split()[2])
            histogram = channel_max.histogram()
            check["changed_pixel_fraction"] = 1 - histogram[0] / (actual_pix.width * actual_pix.height)
            check["mean_absolute_channel_difference_255"] = sum(ImageStat.Stat(difference).mean) / 3
        require(report, check["normalized_text_equal"], "body_text_changed", page=index+1)
        require(report, check["page_size_equal"], "body_page_size_changed", page=index+1)
        layout_ok = same_lines and displacement is not None and displacement <= args.layout_tolerance
        if not layout_ok:
            line_changes, bbox_changes = [], []
            matcher = difflib.SequenceMatcher(a=[line[0] for line in left],
                                             b=[line[0] for line in right], autojunk=False)
            for kind, i, j, k, l in matcher.get_opcodes():
                if kind != "equal":
                    line_changes.append({
                        "kind": kind,
                        "actual_line_numbers": [i+1, j],
                        "baseline_line_numbers": [k+1, l],
                        "actual_lines": [{"text": text, "bbox": list(box)} for text, box in left[i:j]],
                        "baseline_lines": [{"text": text, "bbox": list(box)} for text, box in right[k:l]],
                    })
                else:
                    for offset, (actual_line, baseline_line) in enumerate(zip(left[i:j], right[k:l])):
                        delta = max(abs(x-y) for x, y in zip(actual_line[1], baseline_line[1]))
                        if delta > args.layout_tolerance:
                            bbox_changes.append({
                                "actual_line": i+offset+1, "baseline_line": k+offset+1,
                                "text": actual_line[0], "max_displacement_pt": delta,
                                "actual_bbox": list(actual_line[1]), "baseline_bbox": list(baseline_line[1]),
                            })
            check["line_reflow_details"] = line_changes
            check["bbox_difference_details"] = bbox_changes
            category = "bbox_only_difference_pages" if same_lines else "text_line_reflow_pages"
            report["body_layout_policy"][category].append(index+1)
            if args.allow_body_reflow:
                warning(report, "body_line_layout_changed_explicitly_allowed", page=index+1,
                        line_sequence_equal=same_lines, max_displacement_pt=displacement,
                        page_text_equal=check["normalized_text_equal"],
                        note="Explicit --allow-body-reflow; detailed line and bbox changes retained. Text/page limits remain strict.")
            else:
                require(report, False, "body_line_layout_changed", page=index+1,
                        line_sequence_equal=same_lines, max_displacement_pt=displacement)
        if not pixel_equal:
            if args.strict_pixels:
                require(report, False, "body_pixels_changed", page=index+1)
            else:
                warning(report, "body_pixels_differ", page=index+1,
                        note="Reported separately; text and line layout are checked independently")
        report["body_page_checks"].append(check)


def aux_page(aux: str, label: str) -> int | None:
    match = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{.*?\}\{(\d+)\}", aux)
    return int(match.group(1)) if match else None


def check_pdf_sources(doc, manifest, a_page: int, b_page: int, args, report: dict) -> None:
    texts = [page.get_text() for page in doc]
    compact_pages = [compact(text) for text in texts]
    list_text = "".join(compact_pages[a_page:b_page])
    report["appendix_A_pages"] = list(range(a_page+1, b_page+1))
    for item in manifest:
        require(report, compact(item["source"]) in list_text,
                "source_listed_in_appendix_A_pdf", source=item["source"])
    required_support = [f"results/result{i}.xlsx" for i in range(1, 5)] + ["AI工具使用详情.pdf"]
    report["supporting_files_found"] = {name: compact(name) in list_text for name in required_support}
    for name, found in report["supporting_files_found"].items():
        require(report, found, "support_file_listed_in_appendix_A", source=name)
    report["appendix_A_continuation_headers"] = [
        {"page": i+1, "continuation_marker_present": "续" in compact_pages[i]}
        for i in range(a_page+1, b_page)
    ]
    aux = args.aux.read_text(encoding="utf-8", errors="replace")
    previous_end = b_page+1
    for index, item in enumerate(manifest, 1):
        check = report["source_checks"][index-1]
        start, end = aux_page(aux, f"app:source{index}"), aux_page(aux, f"app:source{index}end")
        check.update({"pdf_first_page": start, "pdf_last_page": end})
        if not require(report, start is not None and end is not None,
                       "source_page_labels_resolved", source=item["source"]):
            continue
        if not require(report, b_page+1 <= start <= end <= len(doc) and start >= previous_end,
                       "source_page_range_order", source=item["source"],
                       start=start, end=end, previous_end=previous_end):
            continue
        previous_end = end
        for field, target in (("filename_comment", item["first_line"]),
                              ("first_source_line", check.get("first_source_line", "")),
                              ("last_source_line", check.get("last_source_line", ""))):
            needle = compact(target)
            found = [page+1 for page in range(start-1, end) if needle and needle in compact_pages[page]]
            check[f"{field}_pdf_pages"] = found
            require(report, bool(found) or (not needle and item["source_lines"] == 0),
                    "source_boundary_line_visible", source=item["source"],
                    boundary=field, line=target, source_page_range=[start, end])
    require(report, len(doc) >= b_page+1, "appendix_B_has_content")


def check_log(doc, manifest, args, report: dict) -> None:
    log = args.log.read_text(encoding="utf-8", errors="replace")
    patterns = [
        r"^!", r"Missing character:", r"Overfull \\[hv]box",
        r"Undefined control sequence", r"There were undefined references",
        r"Reference .* undefined", r"Citation .* undefined",
        r"multiply defined", r"Label\(s\) may have changed",
    ]
    findings = []
    for pattern in patterns:
        for match in re.finditer(pattern, log, flags=re.M):
            line_start, line_end = log.rfind("\n", 0, match.start())+1, log.find("\n", match.end())
            findings.append({"pattern": pattern, "line": log[line_start:line_end if line_end >= 0 else None]})
    output = re.search(r"Output written on\s+(.+?\.(?:pdf|xdv))\s+\((\d+)\s+pages?", log, flags=re.S)
    inputs = [args.manifest, args.paper/"contents/appendix/a1.tex",
              args.paper/"contents/appendix/a2.tex"]
    inputs.extend(within(args.paper, item["appendix_copy"]) for item in manifest)
    newest_input = max(path.stat().st_mtime for path in inputs)
    fresh = args.log.stat().st_mtime + 2 >= newest_input
    aux_fresh = args.aux.stat().st_mtime + 2 >= newest_input
    conversion = None
    conversion_verified = bool(output) and output.group(1).strip().lower().endswith(".pdf")
    if output and output.group(1).strip().lower().endswith(".xdv"):
        console_path = args.compile_output
        if console_path.is_file():
            raw_console = console_path.read_bytes()
            encoding = "utf-16" if raw_console.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            console = raw_console.decode(encoding, errors="replace")
            written = list(re.finditer(
                r"Writing\s+[`\"']([^`\"']+\.pdf)[`\"']\s+\(([0-9.]+)\s+(B|KiB|MiB|GiB)\)",
                console))
            if written:
                last = written[-1]
                written_path = Path(last.group(1)).resolve()
                factors = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}
                recorded_bytes = float(last.group(2)) * factors[last.group(3)]
                same_output = written_path.is_file() and digest(written_path.read_bytes()) == digest(args.pdf.read_bytes())
                console_fresh = console_path.stat().st_mtime + 2 >= newest_input
                byte_count_matches = abs(recorded_bytes - args.pdf.stat().st_size) <= 1
                conversion_verified = same_output and console_fresh and byte_count_matches
                conversion = {
                    "path": str(console_path), "sha256": digest(raw_console),
                    "encoding": encoding, "written_pdf": str(written_path),
                    "recorded_bytes": recorded_bytes, "actual_bytes": args.pdf.stat().st_size,
                    "same_pdf_bytes": same_output, "byte_count_matches": byte_count_matches,
                    "not_older_than_appendix_inputs": console_fresh,
                    "verified": conversion_verified,
                }
            else:
                conversion = {"path": str(console_path), "verified": False,
                              "reason": "No successful Tectonic PDF Writing record"}
        else:
            conversion = {"path": str(console_path), "verified": False,
                          "reason": "Tectonic console output file is missing"}
    report["compile_log"] = {
        "path": str(args.log), "sha256": digest(args.log.read_bytes()),
        "aux_path": str(args.aux), "aux_sha256": digest(args.aux.read_bytes()),
        "not_older_than_manifest_and_appendix_inputs": fresh,
        "aux_not_older_than_manifest_and_appendix_inputs": aux_fresh,
        "reported_output": output.group(1).strip() if output else None,
        "tectonic_pdf_conversion": conversion,
        "reported_pages": int(output.group(2)) if output else None,
        "findings": findings,
    }
    require(report, fresh and aux_fresh, "current_build_log_and_aux_required")
    require(report, not findings, "latex_log_errors_or_unresolved_references", findings=findings)
    require(report, conversion_verified, "pdf_output_completion_verified", conversion=conversion)
    require(report, bool(output) and int(output.group(2)) == len(doc),
            "log_matches_current_pdf_page_count", actual_pages=len(doc))


def check_pdf_integrity(doc, a_page: int, args, report: dict) -> None:
    outside, missing, unresolved = [], [], []
    for index, page in enumerate(doc):
        text = page.get_text()
        if any(character in text for character in ("\ufffd", "\ufffe", "\uffff", "\x00")):
            missing.append(index+1)
        if index < a_page and "??" in text:
            unresolved.append(index+1)
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                x0, y0, x1, y1 = line["bbox"]
                if (x0 < -args.page_tolerance or y0 < -args.page_tolerance or
                        x1 > page.rect.width + args.page_tolerance or
                        y1 > page.rect.height + args.page_tolerance):
                    outside.append({"page": index+1, "bbox": list(line["bbox"]),
                                    "text": "".join(s["text"] for s in line["spans"])})
    report["pdf_integrity"] = {
        "replacement_or_missing_character_pages": missing,
        "body_unresolved_reference_marker_pages": unresolved,
        "text_outside_page": outside,
        "visual_review_claimed": False,
    }
    require(report, not missing, "pdf_missing_or_replacement_characters", pages=missing)
    require(report, not unresolved, "pdf_unresolved_reference_markers", pages=unresolved)
    require(report, not outside, "pdf_text_outside_physical_page", findings=outside[:20])
    report["rendered_appendix_pages"] = []
    if args.render_previews:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        for index in range(a_page, len(doc)):
            path = args.preview_dir / f"page_{index+1:03d}.png"
            doc[index].get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2), alpha=False).save(path)
            report["rendered_appendix_pages"].append(index+1)
        for start in range(a_page, len(doc), 12):
            sheet = Image.new("RGB", (1160, 1260), "#dddddd")
            draw = ImageDraw.Draw(sheet)
            for offset, index in enumerate(range(start, min(start+12, len(doc)))):
                with Image.open(args.preview_dir / f"page_{index+1:03d}.png") as page:
                    page.thumbnail((280, 396))
                    x, y = (offset % 4)*290+5, (offset//4)*420+20
                    sheet.paste(page, (x, y))
                    draw.text((x, y-16), f"Page {index+1}", fill="black")
            sheet.save(args.preview_dir / f"contact_{start+1:03d}.png")


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--paper", type=Path, default=PAPER)
    parser.add_argument("--manifest", type=Path, default=AUDIT/"source_manifest.json")
    parser.add_argument("--pdf", type=Path, default=PAPER/"main.pdf")
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--log", type=Path, help="Log of this build; defaults beside --pdf")
    parser.add_argument("--aux", type=Path, help="Aux file of this build; defaults beside --pdf")
    parser.add_argument("--compile-output", type=Path, help="Tectonic console output; defaults beside --log")
    parser.add_argument("--report", type=Path, default=AUDIT/"source_sync_checks.json")
    parser.add_argument("--abstract-pages", type=int, default=1)
    parser.add_argument("--body-pages", type=int, default=30)
    parser.add_argument("--layout-tolerance", type=float, default=2.0,
                        help="Allowed line-box displacement in points, independent of pixel differences")
    parser.add_argument("--page-tolerance", type=float, default=0.5)
    parser.add_argument("--allow-body-reflow", action="store_true",
                        help="Report line-wrap/font-metric changes as warnings, while keeping per-page text and page counts strict")
    parser.add_argument("--strict-pixels", action="store_true",
                        help="Also fail on any pixel difference; default only reports those differences")
    parser.add_argument("--render-previews", action="store_true")
    parser.add_argument("--preview-dir", type=Path,
                        default=WORKSPACE/"tmp/source-sync-5ae7984/appendix-preview")
    args = parser.parse_args()
    args.log = args.log or args.pdf.with_suffix(".log")
    args.aux = args.aux or args.pdf.with_suffix(".aux")
    args.compile_output = args.compile_output or args.log.parent / "compile-output.txt"
    if args.abstract_pages < 0 or args.body_pages < 0:
        parser.error("Page counts must be nonnegative")
    return args


def main() -> int:
    args = arguments()
    report = {
        "status": "FAIL", "audit": "manifest-driven complete-source appendix synchronization",
        "manifest_path": str(args.manifest), "pdf_path": str(args.pdf),
        "baseline_path": str(args.baseline), "source_checks": [],
        "body_page_checks": [], "errors": [], "warnings": [],
        "numerical_source_execution": False,
    }
    try:
        manifest = read_manifest(args.manifest)
        report["source_file_count"] = len(manifest)
        report["source_language_counts"] = dict(Counter(
            item.get("language", LANGUAGES.get(Path(item["source"]).suffix.lower())) for item in manifest))
        check_sources(manifest, args, report)
        report["original_source_lines"] = sum(item.get("source_lines", 0) for item in manifest)
        check_latex_inputs(manifest, args, report)
        with pymupdf.open(args.pdf) as doc, pymupdf.open(args.baseline) as baseline:
            a_page, b_page = appendix_page(doc, "A"), appendix_page(doc, "B")
            require(report, a_page < b_page, "appendix_title_order",
                    appendix_A_page=a_page+1, appendix_B_page=b_page+1)
            report.update({"pdf_pages": len(doc), "appendix_A_page": a_page+1,
                           "appendix_B_page": b_page+1,
                           "pdf_sha256": digest(args.pdf.read_bytes()),
                           "baseline_sha256": digest(args.baseline.read_bytes())})
            compare_body(doc, baseline, a_page, args, report)
            check_pdf_sources(doc, manifest, a_page, b_page, args, report)
            check_log(doc, manifest, args, report)
            check_pdf_integrity(doc, a_page, args, report)
    except Exception as exc:
        report["errors"].append({"check": "verification_could_not_finish",
                                 "exception": type(exc).__name__, "message": str(exc)})
    report["status"] = "FAIL" if report["errors"] else ("PASS_WITH_NOTES" if report["warnings"] else "PASS")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {key: report.get(key) for key in (
        "status", "pdf_pages", "appendix_A_page", "appendix_B_page",
        "source_file_count", "source_language_counts", "original_source_lines")}
    summary.update({"errors": report["errors"], "warning_count": len(report["warnings"]),
                    "report": str(args.report)})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
