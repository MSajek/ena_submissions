import csv
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom

def prettify(elem):
    rough_string = tostring(elem, 'utf-8')
    return minidom.parseString(rough_string).toprettyxml(indent="  ")

def add_attribute(parent, tag, value):
    attr = SubElement(parent, "SAMPLE_ATTRIBUTE")
    SubElement(attr, "TAG").text = tag
    SubElement(attr, "VALUE").text = value

root = Element("SAMPLE_SET")

with open("samples.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        sample = SubElement(root, "SAMPLE", alias=row["alias"], center_name=row["center_name"])
        SubElement(sample, "TITLE").text = (
            f"Human cell line {row['cell_line']}, {row['stage']}, "
            f"{row['oe'] + ' overexpression, ' if row['oe'] else ''}"
            f"{row['genotype'] if row['genotype'] else ''}, "
            f"doxycycline {'treated' if row['dox'].lower() == 'yes' else 'untreated'}"
        )

        name = SubElement(sample, "SAMPLE_NAME")
        SubElement(name, "TAXON_ID").text = "9606"
        SubElement(name, "SCIENTIFIC_NAME").text = "Homo sapiens"

        attrs = SubElement(sample, "SAMPLE_ATTRIBUTES")
        add_attribute(attrs, "cell_line", row["cell_line"])
        add_attribute(attrs, "differentiation_stage", row["stage"])
        if row["oe"]:
            add_attribute(attrs, "overexpression", row["oe"])
        if row["genotype"]:
            add_attribute(attrs, "genotype", row["genotype"])
        add_attribute(attrs, "doxycycline_treatment", row["dox"])

with open("samples.xml", "w") as f:
    f.write(prettify(root))
