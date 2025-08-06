#!/usr/bin/env python3
import csv
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

def pretty_xml(elem):
    from xml.dom import minidom
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8")

def main(mapping_csv, out_xml="run.xml"):
    mapping_path = Path(mapping_csv)
    assert mapping_path.exists(), f"Mapping file not found: {mapping_csv}"
    run_set = ET.Element("RUN_SET")
    with open(mapping_path, newline="") as fh:
        rdr = csv.DictReader(fh)
        required = ["experiment_alias", "fastq_1", "fastq_2", "md5_1", "md5_2"]
        for col in required:
            if col not in rdr.fieldnames:
                raise SystemExit(f"Missing required column in CSV: {col}")
        for row in rdr:
            exp_alias = row["experiment_alias"].strip()
            fq1 = row["fastq_1"].strip()
            fq2 = row["fastq_2"].strip()
            md51 = row["md5_1"].strip().lower()
            md52 = row["md5_2"].strip().lower()
            if not (exp_alias and fq1 and fq2 and md51 and md52):
                raise SystemExit(f"Incomplete row for experiment_alias={exp_alias}. Fill all fields.")
            run_alias = f"{exp_alias}__run"
            run = ET.SubElement(run_set, "RUN", {"alias": run_alias})
            exp_ref = ET.SubElement(run, "EXPERIMENT_REF", {"refname": exp_alias})
            data_block = ET.SubElement(run, "DATA_BLOCK")
            files = ET.SubElement(data_block, "FILES")
            ET.SubElement(files, "FILE", {
                "filename": fq1,
                "filetype": "fastq",
                "checksum_method": "MD5",
                "checksum": md51
            })
            ET.SubElement(files, "FILE", {
                "filename": fq2,
                "filetype": "fastq",
                "checksum_method": "MD5",
                "checksum": md52
            })
    xml_bytes = pretty_xml(run_set)
    with open(out_xml, "wb") as f:
        f.write(xml_bytes)
    print(f"Wrote {out_xml}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: make_run_xml_from_mapping.py run_mapping.csv [out.xml]")
        sys.exit(1)
    mapping_csv = sys.argv[1]
    out_xml = sys.argv[2] if len(sys.argv) > 2 else "run.xml"
    main(mapping_csv, out_xml)
