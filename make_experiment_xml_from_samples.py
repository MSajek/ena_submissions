#!/usr/bin/env python3
"""
make_experiment_xml_from_samples.py
-----------------------------------
Create ENA experiment.xml from a samples.xml and a small CSV of global parameters.

Usage:
  python make_experiment_xml_from_samples.py \
      --samples samples.xml \
      --params experiment_params.csv \
      --out experiment.xml \
      [--exp-suffix "__RNAseq_PE"] \
      [--lib-name-suffix "_lib"]

The params CSV must contain a single row with headers:
  study_accession, instrument_model, library_strategy, library_source, library_selection, layout, nominal_length

Notes:
- layout must be SINGLE or PAIRED (case-insensitive). If PAIRED, NOMINAL_LENGTH is included.
- sample aliases are taken from <SAMPLE alias="..."> in samples.xml and referenced by refname.
"""
import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

def pretty_xml(elem):
    rough = ET.tostring(elem, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="utf-8")

def read_params_csv(path):
    with open(path, newline="") as fh:
        rdr = csv.DictReader(fh)
        rows = list(rdr)
        if len(rows) != 1:
            raise SystemExit(f"Expected exactly one row in params CSV, found {len(rows)}")
        row = rows[0]
        required = ["study_accession","instrument_model","library_strategy",
                    "library_source","library_selection","layout","nominal_length"]
        for r in required:
            if r not in row or not row[r].strip():
                raise SystemExit(f"Missing required parameter: {r}")
        return {k: v.strip() for k, v in row.items()}

def main(samples_xml, params_csv, out_xml, exp_suffix, lib_name_suffix):
    samples_path = Path(samples_xml)
    assert samples_path.exists(), f"samples.xml not found: {samples_xml}"
    params = read_params_csv(params_csv)

    study_accession   = params["study_accession"]
    instrument_model  = params["instrument_model"]
    library_strategy  = params["library_strategy"]
    library_source    = params["library_source"]
    library_selection = params["library_selection"]
    layout            = params["layout"].upper()
    nominal_length    = params["nominal_length"]

    tree = ET.parse(samples_path)
    root = tree.getroot()

    exp_set = ET.Element("EXPERIMENT_SET")

    for s in root.findall("SAMPLE"):
        alias = s.attrib.get("alias")
        if not alias:
            raise SystemExit("A SAMPLE element is missing an 'alias' attribute.")
        exp_alias = f"{alias}{exp_suffix}"
        exp = ET.SubElement(exp_set, "EXPERIMENT", {"alias": exp_alias})

        title = ET.SubElement(exp, "TITLE")
        title.text = f"{alias} RNA-seq ({'paired-end' if layout=='PAIRED' else 'single-end'})"

        ET.SubElement(exp, "STUDY_REF", {"accession": study_accession})

        design = ET.SubElement(exp, "DESIGN")
        desc = ET.SubElement(design, "DESIGN_DESCRIPTION")
        desc.text = f"{library_selection}-selected transcriptome sequencing ({'paired-end' if layout=='PAIRED' else 'single-end'})."

        ET.SubElement(design, "SAMPLE_DESCRIPTOR", {"refname": alias})

        lib_desc = ET.SubElement(design, "LIBRARY_DESCRIPTOR")
        lib_name = ET.SubElement(lib_desc, "LIBRARY_NAME")
        lib_name.text = f"{alias}{lib_name_suffix}"
        ET.SubElement(lib_desc, "LIBRARY_STRATEGY").text = library_strategy
        ET.SubElement(lib_desc, "LIBRARY_SOURCE").text   = library_source
        ET.SubElement(lib_desc, "LIBRARY_SELECTION").text= library_selection

        lib_layout = ET.SubElement(lib_desc, "LIBRARY_LAYOUT")
        if layout == "PAIRED":
            ET.SubElement(lib_layout, "PAIRED", {"NOMINAL_LENGTH": str(nominal_length)})
        elif layout == "SINGLE":
            ET.SubElement(lib_layout, "SINGLE")
        else:
            raise SystemExit("layout must be SINGLE or PAIRED")

        platform = ET.SubElement(exp, "PLATFORM")
        illumina = ET.SubElement(platform, "ILLUMINA")
        ET.SubElement(illumina, "INSTRUMENT_MODEL").text = instrument_model

    xml_bytes = pretty_xml(exp_set)
    with open(out_xml, "wb") as f:
        f.write(xml_bytes)
    print(f"Wrote {out_xml}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True, help="Path to samples.xml")
    ap.add_argument("--params", required=True, help="CSV with one row of global experiment params")
    ap.add_argument("--out", required=True, help="Output experiment.xml path")
    ap.add_argument("--exp-suffix", default="__RNAseq_PE", help="Suffix appended to experiment aliases")
    ap.add_argument("--lib-name-suffix", default="_lib", help="Suffix appended to LIBRARY_NAME")
    args = ap.parse_args()
    main(args.samples, args.params, args.out, args.exp_suffix, args.lib_name_suffix)
