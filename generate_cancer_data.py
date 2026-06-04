"""Run this script once to generate cancer_genes.xlsx used by the Shiny dashboard."""
import pandas as pd
from pathlib import Path

data = {
    "Gene": [
        "EGFR", "KRAS G12C", "BRCA1", "BRCA2", "TP53",
        "ALK", "BRAF V600E", "PIK3CA", "PTEN", "MYC",
        "HER2", "CDK4/6", "RET", "MET", "FGFR1-3",
        "IDH1", "IDH2", "JAK2", "BCR-ABL1", "NRAS",
        "CDKN2A", "VHL", "VEGFR", "AR", "ESR1",
    ],
    "Cancer Type": [
        "Lung", "Lung/Colorectal", "Breast/Ovarian", "Breast/Ovarian/Pancreatic", "Pan-Cancer",
        "Lung", "Melanoma/Colorectal", "Breast", "Prostate/Endometrial", "Lymphoma/Breast",
        "Breast/Gastric", "Breast/Melanoma", "Thyroid/Lung", "Lung/Gastric", "Bladder/Lung",
        "AML/Glioma", "AML", "MPN/AML", "CML/ALL", "Melanoma/AML",
        "Melanoma/Pancreatic", "Renal Cell Carcinoma", "Renal/Colorectal", "Prostate", "Breast",
    ],
    "Treatment": [
        "Osimertinib", "Sotorasib", "Olaparib", "Olaparib", "No targeted therapy",
        "Alectinib", "Vemurafenib", "Alpelisib", "Everolimus", "No targeted therapy",
        "Trastuzumab", "Palbociclib", "Selpercatinib", "Capmatinib", "Erdafitinib",
        "Ivosidenib", "Enasidenib", "Ruxolitinib", "Imatinib", "Trametinib",
        "Palbociclib", "Belzutifan", "Sunitinib", "Enzalutamide", "Fulvestrant",
    ],
    "Pathway": [
        "MAPK/ERK", "MAPK/ERK", "DNA Damage Repair", "DNA Damage Repair", "Cell Cycle/Apoptosis",
        "MAPK/ERK", "MAPK/ERK", "PI3K/AKT/mTOR", "PI3K/AKT/mTOR", "Cell Cycle/Apoptosis",
        "PI3K/AKT/mTOR", "Cell Cycle/Apoptosis", "MAPK/ERK", "MAPK/ERK", "PI3K/AKT/mTOR",
        "Metabolism", "Metabolism", "JAK/STAT", "JAK/STAT", "MAPK/ERK",
        "Cell Cycle/Apoptosis", "Angiogenesis/HIF", "Angiogenesis/HIF", "Hormone Signaling", "Hormone Signaling",
    ],
    "Expression Level (log2FC)": [
        4.2, 3.1, 2.8, 2.5, 5.7,
        6.1, 4.8, 3.5, -1.2, 7.3,
        5.9, 3.2, 4.5, 3.8, 2.9,
        4.1, 3.7, 4.4, 8.2, 3.3,
        -2.1, 2.2, 3.6, 5.1, 4.7,
    ],
    "Patient Count": [
        8500, 12000, 6200, 5800, 25000,
        3200, 7100, 9800, 4500, 11200,
        8900, 2800, 1900, 2100, 3400,
        1600, 1200, 2700, 3100, 2400,
        4100, 2300, 5500, 7800, 6400,
    ],
    "Mutation Frequency (%)": [
        15, 13, 5, 4, 42,
        5, 8, 12, 6, 18,
        14, 7, 3, 4, 6,
        3, 2, 5, 2, 8,
        11, 7, 9, 15, 12,
    ],
    "Drug Status": [
        "Approved", "Approved", "Approved", "Approved", "None",
        "Approved", "Approved", "Approved", "Approved", "None",
        "Approved", "Approved", "Approved", "Approved", "Approved",
        "Approved", "Approved", "Approved", "Approved", "Investigational",
        "Investigational", "Approved", "Approved", "Approved", "Approved",
    ],
}

df = pd.DataFrame(data)
output_path = Path(__file__).parent / "cancer_genes.xlsx"
df.to_excel(output_path, index=False)
print(f"Created {output_path} with {len(df)} genes.")
