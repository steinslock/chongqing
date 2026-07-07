#!/usr/bin/env python3
"""Build read-only QA artifacts for the Chongqing multimodal diagnosis dataset.

The script never writes inside DATA_ROOT. All derived artifacts go to OUT_DIR.
It intentionally avoids pandas/openpyxl so it can run in the base environment.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


DATA_ROOT = Path("/home/qiangminc/codes/data4_qiangminc/datasets_qiangmin/chongqing")
OUT_DIR = Path("/home/qiangminc/codes/data4_qiangminc/outputs/chongqing_binary_diagnosis_report")
DATA_DIR = OUT_DIR / "data"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

EXCLUDE_LABELS = {"-", "无基线信息，排除", None, ""}
HEALTHY_LABEL = "健康"
HIGH_RISK_LABEL = "高危"
MDD_LABEL = "MDD"

CLEAR_DIAGNOSIS_LABELS = {
    "MDD",
    "焦虑症",
    "多动症",
    "精分",
    "强迫症",
    "双相",
    "对立违抗",
    "PTSD",
    "抽动障碍",
    "孤独症",
    "品行障碍",
}


def colnum(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n


def shared_strings(zf: ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall("main:si", NS):
        out.append("".join((t.text or "") for t in si.iter(f"{{{NS['main']}}}t")))
    return out


def cell_value(cell: ET.Element, shared: list[str]) -> str | None:
    cell_type = cell.attrib.get("t")
    value = cell.find("main:v", NS)
    if cell_type == "inlineStr":
        inline = cell.find("main:is", NS)
        if inline is None:
            return ""
        return "".join((t.text or "") for t in inline.iter(f"{{{NS['main']}}}t"))
    if value is None:
        return None
    raw = value.text
    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (TypeError, ValueError, IndexError):
            return raw
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw


def xlsx_rows(path: Path, sheet_idx: int = 0) -> tuple[str, list[list[str | None]]]:
    with ZipFile(path) as zf:
        shared = shared_strings(zf)
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet = workbook.find("main:sheets", NS)[sheet_idx]
        sheet_name = sheet.attrib["name"]
        target = rid_to_target[sheet.attrib[f"{{{NS['rel']}}}id"]]
        if not target.startswith("worksheets/"):
            target = "worksheets/" + target.split("/")[-1]
        worksheet = ET.fromstring(zf.read("xl/" + target))
        rows = []
        for row in worksheet.findall(".//main:sheetData/main:row", NS):
            vals = {}
            for cell in row.findall("main:c", NS):
                vals[colnum(cell.attrib["r"])] = cell_value(cell, shared)
            max_col = max(vals) if vals else 0
            rows.append([vals.get(i) for i in range(1, max_col + 1)])
        return sheet_name, rows


def value_at(row: list[str | None], idx: int) -> str | None:
    return row[idx] if idx < len(row) else None


def make_label(diag: str | None, policy: str) -> int | None:
    if diag in EXCLUDE_LABELS:
        return None
    if policy == "primary_nonhealthy":
        return 0 if diag == HEALTHY_LABEL else 1
    if policy == "sensitivity_clear_diagnosis":
        if diag == HEALTHY_LABEL:
            return 0
        return 1 if diag in CLEAR_DIAGNOSIS_LABELS else None
    if policy == "sensitivity_mdd_highrisk":
        if diag == HEALTHY_LABEL:
            return 0
        return 1 if diag in {HIGH_RISK_LABEL, MDD_LABEL} else None
    raise ValueError(policy)


def collect_path_ids(path: Path) -> set[str]:
    id_patterns = [
        re.compile(r"(?<![A-Z0-9])L\d{1,5}(?!\d)", re.I),
        re.compile(r"(?<![A-Z0-9])A\d{5}(?!\d)", re.I),
    ]
    ids = set()
    for item in path.rglob("*"):
        rel = str(item.relative_to(path))
        for pattern in id_patterns:
            for match in pattern.findall(rel):
                ids.add(match.upper())
    return ids


def top_level_file_summary(path: Path) -> dict[str, object]:
    ext_counts: Counter[str] = Counter()
    top_dirs: Counter[str] = Counter()
    total_files = 0
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        total_files += 1
        ext_counts[item.suffix.lower() or "<noext>"] += 1
        rel = item.relative_to(path)
        top_dirs[rel.parts[0] if rel.parts else "."] += 1
    return {
        "total_files": total_files,
        "top_extensions": ext_counts.most_common(30),
        "top_level_file_counts": top_dirs.most_common(),
    }


def collect_modality_tasks() -> dict[str, Counter[str]]:
    tasks = {"EEG": Counter(), "fNIRS": Counter(), "Eye": Counter(), "Face": Counter()}
    for child in (DATA_ROOT / "脑电").iterdir():
        if child.is_dir():
            tasks["EEG"][child.name] = len(collect_path_ids(child))
    for child in (DATA_ROOT / "近红外").iterdir():
        if child.is_dir():
            tasks["fNIRS"][child.name] = len(collect_path_ids(child))
    for child in (DATA_ROOT / "眼动").rglob("*"):
        if child.is_dir() and child.name in {"平滑追随", "扫视", "自由观看"}:
            tasks["Eye"][child.name] += len(
                [
                    p
                    for p in child.iterdir()
                    if p.is_dir()
                    and re.match(r"^[A-E]\d{5}[_-][^_-]+[_-]?\d{10,}$", p.name)
                ]
            )
    for child in (DATA_ROOT / "面部").iterdir():
        if child.is_dir():
            tasks["Face"][child.name] = len(collect_path_ids(child))
    return tasks


def build_web_name_map() -> tuple[dict[str, set[str]], dict[str, int]]:
    web_path = DATA_ROOT / "附件" / "网页数据.xlsx"
    _, rows = xlsx_rows(web_path, 0)
    header = rows[0]
    name_idx = header.index("姓名")
    aid_idx = header.index("编号")
    mapping: dict[str, set[str]] = defaultdict(set)
    for row in rows[1:]:
        name = value_at(row, name_idx)
        aid = value_at(row, aid_idx)
        if name and aid:
            mapping[name.strip()].add(aid.strip().upper())
    stats = {
        "web_rows_with_id": sum(len(v) for v in mapping.values()),
        "unique_names": len(mapping),
        "duplicate_name_keys": sum(1 for v in mapping.values() if len(v) > 1),
    }
    return mapping, stats


def eye_name_mapping_stats(name_to_a: dict[str, set[str]]) -> tuple[set[str], dict[str, object]]:
    code_pattern = re.compile(r"^([A-E]\d{5})[_-]([^_-]+)[_-]?\d{10,}$")
    reachable_a: set[str] = set()
    code_prefix_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    matched_dirs = 0
    pattern_dirs = 0
    ambiguous_dirs = 0
    for d in (DATA_ROOT / "眼动").rglob("*"):
        if not d.is_dir():
            continue
        match = code_pattern.match(d.name)
        if not match:
            continue
        pattern_dirs += 1
        code_prefix_counts[match.group(1)[0]] += 1
        task_counts[d.parent.name] += 1
        name = match.group(2).strip()
        if name in name_to_a:
            matched_dirs += 1
            if len(name_to_a[name]) > 1:
                ambiguous_dirs += 1
            reachable_a.update(name_to_a[name])
    stats = {
        "eye_subject_dirs_with_name_pattern": pattern_dirs,
        "eye_dirs_name_matched_to_webdata": matched_dirs,
        "ambiguous_name_match_dirs": ambiguous_dirs,
        "eye_unique_a_reachable_by_name": len(reachable_a),
        "eye_code_prefix_counts": code_prefix_counts.most_common(),
        "eye_task_parent_counts": task_counts.most_common(),
    }
    return reachable_a, stats


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    clinical_path = DATA_ROOT / "临床信息-重医6.3.xlsx"
    sheet_name, rows = xlsx_rows(clinical_path, 0)
    header = rows[0]
    index = {name: i for i, name in enumerate(header) if name}
    required_columns = [
        "编号",
        "脑电编号",
        "诊断3-他评量表CDRS≥40",
        "CDRS量表总分：[JH05_10_006179_6387_1]",
        "性别",
        "年龄",
        "年级：[JH05_10_007153_6356_1]",
    ]
    missing_required = [col for col in required_columns if col not in index]
    if missing_required:
        raise RuntimeError(f"Missing required clinical columns: {missing_required}")

    records = []
    for row in rows[1:]:
        aid = value_at(row, index["编号"])
        lid = value_at(row, index["脑电编号"])
        if not aid and not lid:
            continue
        diag3 = value_at(row, index["诊断3-他评量表CDRS≥40"])
        cdrs_raw = value_at(row, index["CDRS量表总分：[JH05_10_006179_6387_1]"])
        try:
            cdrs_score = int(float(cdrs_raw)) if cdrs_raw not in (None, "", "#N/A") else None
        except ValueError:
            cdrs_score = None
        records.append(
            {
                "A_id": aid.upper() if aid else "",
                "L_id": lid.upper() if lid else "",
                "diag3": diag3,
                "primary_label_nonhealthy": make_label(diag3, "primary_nonhealthy"),
                "sensitivity_label_clear_diagnosis": make_label(diag3, "sensitivity_clear_diagnosis"),
                "sensitivity_label_mdd_highrisk": make_label(diag3, "sensitivity_mdd_highrisk"),
                "CDRS_score": cdrs_score,
                "sex": value_at(row, index["性别"]),
                "age": value_at(row, index["年龄"]),
                "grade": value_at(row, index["年级：[JH05_10_007153_6356_1]"]),
            }
        )

    modality_ids = {
        "EEG": collect_path_ids(DATA_ROOT / "脑电"),
        "fNIRS": collect_path_ids(DATA_ROOT / "近红外"),
        "Eye_direct": collect_path_ids(DATA_ROOT / "眼动"),
        "Face": collect_path_ids(DATA_ROOT / "面部"),
    }
    name_to_a, web_stats = build_web_name_map()
    eye_name_a_ids, eye_name_stats = eye_name_mapping_stats(name_to_a)

    for rec in records:
        aid = rec["A_id"]
        lid = rec["L_id"]
        rec["has_EEG"] = int(lid in modality_ids["EEG"])
        rec["has_fNIRS"] = int(lid in modality_ids["fNIRS"])
        rec["has_face"] = int(lid in modality_ids["Face"])
        rec["has_eye_direct"] = int(aid in modality_ids["Eye_direct"] or lid in modality_ids["Eye_direct"])
        rec["has_eye_name_mapped"] = int(aid in eye_name_a_ids)
        rec["modality_count_direct"] = (
            rec["has_EEG"] + rec["has_fNIRS"] + rec["has_face"] + rec["has_eye_direct"]
        )
        rec["modality_count_with_eye_name_map"] = (
            rec["has_EEG"] + rec["has_fNIRS"] + rec["has_face"] + rec["has_eye_name_mapped"]
        )

    manifest_fields = [
        "A_id",
        "L_id",
        "diag3",
        "primary_label_nonhealthy",
        "sensitivity_label_clear_diagnosis",
        "sensitivity_label_mdd_highrisk",
        "CDRS_score",
        "sex",
        "age",
        "grade",
        "has_EEG",
        "has_fNIRS",
        "has_face",
        "has_eye_direct",
        "has_eye_name_mapped",
        "modality_count_direct",
        "modality_count_with_eye_name_map",
    ]
    with (DATA_DIR / "subject_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(records)

    label_counts = Counter(rec["diag3"] for rec in records)
    cdrs_consistency = Counter()
    for rec in records:
        diag = rec["diag3"]
        score = rec["CDRS_score"]
        if score is None:
            cdrs_consistency["missing_score"] += 1
            continue
        if diag == HEALTHY_LABEL and score >= 40:
            cdrs_consistency["healthy_with_cdrs_ge_40"] += 1
        elif diag == HIGH_RISK_LABEL and score < 40:
            cdrs_consistency["highrisk_with_cdrs_lt_40"] += 1
        elif diag not in EXCLUDE_LABELS:
            cdrs_consistency["consistent_or_non_threshold_diag"] += 1
        else:
            cdrs_consistency["excluded_with_score"] += 1

    clinical_l_ids = {rec["L_id"] for rec in records if rec["L_id"]}
    clinical_a_ids = {rec["A_id"] for rec in records if rec["A_id"]}

    coverage_rows = []
    for modality, ids in modality_ids.items():
        matched_l = len(ids & clinical_l_ids)
        matched_a = len(ids & clinical_a_ids)
        matched_records = [
            rec
            for rec in records
            if rec["L_id"] in ids or rec["A_id"] in ids
        ]
        coverage_rows.append(
            {
                "modality": modality,
                "ids_seen": len(ids),
                "matched_L": matched_l,
                "matched_A": matched_a,
                "matched_subject_rows": len(matched_records),
                "diag3_counts": dict(Counter(rec["diag3"] for rec in matched_records)),
            }
        )
    eye_name_matched_records = [rec for rec in records if rec["A_id"] in eye_name_a_ids]
    coverage_rows.append(
        {
            "modality": "Eye_name_mapped",
            "ids_seen": len(eye_name_a_ids),
            "matched_L": 0,
            "matched_A": len(eye_name_a_ids & clinical_a_ids),
            "matched_subject_rows": len(eye_name_matched_records),
            "diag3_counts": dict(Counter(rec["diag3"] for rec in eye_name_matched_records)),
        }
    )

    with (DATA_DIR / "modality_coverage.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["modality", "ids_seen", "matched_L", "matched_A", "matched_subject_rows", "diag3_counts"],
        )
        writer.writeheader()
        writer.writerows(coverage_rows)

    label_policy_summary = {}
    for label_col in [
        "primary_label_nonhealthy",
        "sensitivity_label_clear_diagnosis",
        "sensitivity_label_mdd_highrisk",
    ]:
        values = Counter(rec[label_col] for rec in records)
        label_policy_summary[label_col] = {
            "negative_0": values.get(0, 0),
            "positive_1": values.get(1, 0),
            "excluded_null": values.get(None, 0),
        }

    duplicate_a = sum(1 for _, cnt in Counter(rec["A_id"] for rec in records).items() if cnt > 1)
    duplicate_l = sum(1 for _, cnt in Counter(rec["L_id"] for rec in records).items() if cnt > 1)
    modality_tasks = collect_modality_tasks()

    qa = {
        "dataset_root": str(DATA_ROOT),
        "output_dir": str(OUT_DIR),
        "clinical_file": str(clinical_path),
        "clinical_sheet": sheet_name,
        "clinical_rows": len(records),
        "clinical_columns": len(header),
        "duplicate_A_id_keys": duplicate_a,
        "duplicate_L_id_keys": duplicate_l,
        "diag3_counts": dict(label_counts),
        "label_policy_summary": label_policy_summary,
        "cdrs_consistency": dict(cdrs_consistency),
        "sex_counts": dict(Counter(rec["sex"] for rec in records)),
        "age_counts_top": Counter(rec["age"] for rec in records).most_common(25),
        "grade_counts": dict(Counter(rec["grade"] for rec in records)),
        "modality_coverage": coverage_rows,
        "webdata_mapping_stats": web_stats,
        "eye_name_mapping_stats": eye_name_stats,
        "modality_tasks": {k: dict(v) for k, v in modality_tasks.items()},
        "file_summary": top_level_file_summary(DATA_ROOT),
        "privacy_note": "Names are used only transiently for eye-tracking alignment and are not written to subject_manifest.csv.",
        "raw_data_mutation_policy": "Read-only input; derived artifacts are written only outside DATA_ROOT.",
    }
    with (DATA_DIR / "qa_summary.json").open("w", encoding="utf-8") as f:
        json.dump(qa, f, ensure_ascii=False, indent=2)

    # A compact text summary is handy for report drafting and grep.
    with (DATA_DIR / "qa_summary.md").open("w", encoding="utf-8") as f:
        f.write("# Chongqing Dataset QA Summary\n\n")
        f.write(f"- Clinical rows: {len(records)}\n")
        f.write(f"- Clinical columns: {len(header)}\n")
        f.write(f"- Duplicate A ids: {duplicate_a}; duplicate L ids: {duplicate_l}\n")
        f.write(f"- diag3 counts: {dict(label_counts)}\n")
        f.write(f"- label policies: {label_policy_summary}\n")
        f.write(f"- CDRS consistency: {dict(cdrs_consistency)}\n")
        f.write("\n## Modality coverage\n\n")
        for row in coverage_rows:
            f.write(
                f"- {row['modality']}: ids={row['ids_seen']}, "
                f"matched_subjects={row['matched_subject_rows']}, diag3={row['diag3_counts']}\n"
            )

    print(json.dumps({k: qa[k] for k in ["clinical_rows", "diag3_counts", "label_policy_summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
