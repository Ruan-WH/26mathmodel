"""Archive all appendix-B Python directly under 代码/.

This is a source submission archive, not a standalone simulation environment.
Runtime inputs and existing COMSOL data remain requirements of the original
project; the archive contains only the authorized code, results and AI PDF.
No source code is executed, adapted or rewritten by this builder.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import shutil
import xml.etree.ElementTree as ET
import zipfile

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parent.parent
PAPER = PROJECT / "paper/cumcm-1.1.0"
SOURCE_MANIFEST = PROJECT / "reports/appendix_results_20260913/source_manifest.json"
ZIP_PATH = PROJECT / "support_materials_final_20260913.zip"
PREFIX = "代码/"
EXPECTED_SOURCE_COUNT = 22
EXPECTED_FILE_COUNT = 27
MAX_BYTES = 20_000_000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Source path escapes project: {relative}")
    return path


def normalized_text(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def workbook_metadata(data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as book:
        properties = ET.fromstring(book.read("docProps/core.xml"))
    creator = properties.find("{http://purl.org/dc/elements/1.1/}creator")
    editor = properties.find(
        "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}lastModifiedBy")
    metadata = dict(creator=creator.text if creator is not None else None,
                    lastModifiedBy=editor.text if editor is not None else None)
    if metadata["creator"] or metadata["lastModifiedBy"]:
        raise ValueError(f"Submitted workbook has nonempty author metadata: {metadata}")
    return metadata


def build() -> dict:
    catalog = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8-sig"))
    if len(catalog) != EXPECTED_SOURCE_COUNT:
        raise ValueError(
            f"Wait for the final appendix source manifest: expected 22 Python files, got {len(catalog)}")
    discovered = {p.relative_to(PROJECT).as_posix()
                  for directory in ("code", "comsol_q1", "comsol_q4")
                  for p in (PROJECT / directory).rglob("*.py")}
    discovered.add("inspect_inputs.py")
    selected = {item["source"] for item in catalog}
    if selected != discovered or len(selected) != EXPECTED_SOURCE_COUNT:
        raise ValueError(dict(missing_from_appendix=sorted(discovered-selected),
                              unexpected_sources=sorted(selected-discovered)))

    payloads = {}
    entries = []
    snapshots = {}
    source_checks = []
    for item in catalog:
        relative = item["source"]
        if Path(relative).suffix.lower() != ".py":
            raise ValueError(f"Non-Python source in final appendix: {relative}")
        path = safe_path(PROJECT, relative)
        data = path.read_bytes()
        copy_path = safe_path(PAPER, item["appendix_copy"])
        copied = copy_path.read_bytes()
        if sha256(data) != item["source_sha256"]:
            raise ValueError(f"Source manifest is stale; synchronize appendix first: {relative}")
        if sha256(copied) != item["appendix_sha256"]:
            raise ValueError(f"Appendix-copy manifest is stale: {relative}")
        if normalized_text(copied) != item["first_line"] + "\n" + normalized_text(data):
            raise ValueError(f"Appendix source is not complete or differs from canonical: {relative}")
        # AST compilation checks syntax only. It does not import or execute the program.
        compile(ast.parse(normalized_text(data), filename=relative), relative, "exec")
        archive_path = PREFIX + Path(relative).name
        if archive_path in payloads:
            raise ValueError(f"Duplicate flat filename: {archive_path}")
        payloads[archive_path] = path
        snapshots[relative] = sha256(data)
        entries.append(dict(archive_path=archive_path, source=relative,
                            description=item["description"], kind="Python",
                            size_bytes=len(data), sha256=sha256(data)))
        source_checks.append(dict(source=relative, archive_path=archive_path,
                                  canonical_byte_identical=True,
                                  appendix_identical_after_filename_comment=True,
                                  syntax_checked_not_executed=True, sha256=sha256(data)))

    workbook_checks = []
    for number in range(1, 5):
        filename = f"result{number}.xlsx"
        relative = "results/" + filename
        data = (PROJECT / relative).read_bytes()
        metadata = workbook_metadata(data)
        payloads[filename] = PROJECT / relative
        snapshots[relative] = sha256(data)
        entries.append(dict(archive_path=filename, source=relative,
                            description=f"问题{number}正式结果工作簿（原样保留）",
                            kind="result_workbook", size_bytes=len(data), sha256=sha256(data)))
        workbook_checks.append(dict(file=filename, byte_identical=True,
                                    sha256=sha256(data), **metadata))
    ai_relative = "paper/AI_usage/AI工具使用详情.pdf"
    ai_data = (PROJECT / ai_relative).read_bytes()
    ai_name = "AI工具使用详情.pdf"
    payloads[ai_name] = PROJECT / ai_relative
    snapshots[ai_relative] = sha256(ai_data)
    entries.append(dict(archive_path=ai_name, source=ai_relative,
                        description="AI工具使用情况说明（原样保留）",
                        kind="AI_usage_pdf", size_bytes=len(ai_data), sha256=sha256(ai_data)))

    assert len(payloads) == EXPECTED_FILE_COUNT
    assert sum(name.endswith(".py") for name in payloads) == EXPECTED_SOURCE_COUNT
    assert all(name.count("/") == (1 if name.startswith(PREFIX) else 0) for name in payloads)
    temporary = ZIP_PATH.with_suffix(".zip.building")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(payloads.items()):
            archive.write(path, arcname=name)
    with zipfile.ZipFile(temporary) as archive:
        assert len(archive.namelist()) == EXPECTED_FILE_COUNT
        assert not any(info.is_dir() for info in archive.infolist())
        for item in entries:
            with archive.open(item["archive_path"]) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            assert digest == item["sha256"], item["archive_path"]
    after = {}
    for relative in snapshots:
        with (PROJECT / relative).open("rb") as stream:
            after[relative] = hashlib.file_digest(stream, "sha256").hexdigest()
    assert snapshots == after, "Source files changed during packaging"
    zip_bytes = temporary.stat().st_size
    with temporary.open("rb") as stream:
        zip_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    shutil.copyfile(temporary, ZIP_PATH)
    temporary.unlink()

    manifest = dict(schema_version=1, layout="root results and AI PDF; all appendix-B Python flat under 代码/",
                    file_count=EXPECTED_FILE_COUNT, python_source_count=EXPECTED_SOURCE_COUNT, mph_file_count=0,
                    files=sorted(entries, key=lambda item: item["archive_path"]),
                    runtime_scope="Flat source/model archive; restore original source paths shown in appendix B before running, with original problem inputs and applicable COMSOL data",
                    source_execution=False, internal_readme_or_manifest=False,
                    explicit_directory_entries=False)
    checks = dict(status="PASS_WITH_NOTES" if zip_bytes > MAX_BYTES else "PASS", zip_bytes=zip_bytes, zip_sha256=zip_digest,
                  mph_file_count=0, code_subdirectories=0,
                  exceeds_previous_20MB_limit=zip_bytes > MAX_BYTES,
                  size_policy="User explicitly requested all 2 selected MPH files; retained all without truncation",
                  archive_file_count=EXPECTED_FILE_COUNT, python_source_count=EXPECTED_SOURCE_COUNT,
                  archive_names=sorted(payloads), explicit_directory_entries=0,
                  root_file_names=sorted(name for name in payloads if not name.startswith(PREFIX)),
                  only_authorized_file_types=True, crc_check="PASS",
                  complete_appendix_B_source_set=True, source_checks=source_checks,
                  result_workbook_checks=workbook_checks, ai_pdf_byte_identical=True,
                  canonical_sources_and_documents_unchanged=True, protected_sha256=snapshots,
                  numerical_source_execution=False, runtime_smoke_performed=False,
                  verification_scope="Current source/appendix hash, exact contents, Python syntax, ZIP integrity and result metadata; no numerical rerun")
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT/"support_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (AUDIT/"checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: checks[key] for key in
                      ("status", "zip_bytes", "zip_sha256", "archive_file_count",
                       "python_source_count", "archive_names")}, ensure_ascii=False, indent=2))
    return checks


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build()
