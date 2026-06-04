import pathlib
import sys

SAMPLE = pathlib.Path(__file__).parent / "src" / "data_plane" / "sample_data"
OUTPUT = pathlib.Path(__file__).parent / "verification_results.txt"


class _Tee:
    """Writes to both stdout and a file simultaneously."""
    def __init__(self, file):
        self._file = file
        self._stdout = sys.stdout

    def write(self, data):
        self._stdout.write(data)
        self._file.write(data)

    def flush(self):
        self._stdout.flush()
        self._file.flush()


_out_file = open(OUTPUT, "w", encoding="utf-8")
_tee = _Tee(_out_file)
sys.stdout = _tee


#PyMuPDF 
print("=" * 60)
print("1. PyMuPDF — Bioinformatics PDF")
print("=" * 60)

#fitz is the main module of PyMuPDF, which provides the core functionality for working with PDF files. It allows you to open, read, and manipulate PDF documents, including extracting text, images, and metadata.
import fitz 

pdf_path = SAMPLE / "Bioinformatics analysis of the role of RNA modification regulators in polycystic ovary syndrome.pdf"

#Extract metadata and a preview of the first page to verify PyMuPDF is working correctly
with fitz.open(pdf_path) as doc:
    meta = doc.metadata
    print(f"  Title  : {meta.get('title') or '(not embedded)'}")
    print(f"  Author : {meta.get('author') or '(not embedded)'}")
    # Fallback: first ~500 chars of page 1 text to show extraction works
    first_page_text = doc[0].get_text()[:500].strip()
    print(f"  Page 1 preview:\n{first_page_text}\n")


#pandas
print("=" * 60)
print("2. pandas — iris_data.csv")
print("=" * 60)

import pandas as pd

df = pd.read_csv(SAMPLE / "iris_data.csv")
print(f"  Shape   : {df.shape[0]} rows × {df.shape[1]} columns")
print(f"  Columns : {list(df.columns)}")
print(f"  Head:\n{df.head(3).to_string(index=False)}\n")


#python-pptx 
print("=" * 60)
print("3. python-pptx — DS340 Discussion1.pptx")
print("=" * 60)

#python-pptx is a library for creating and manipulating PowerPoint (.pptx) files. It allows you to read existing presentations, modify slides, add new content, and save the changes. You can extract text, images, and other elements from slides, as well as create new slides with various layouts and designs.
from pptx import Presentation

#To verify python-pptx, we will open the presentation, count the number of slides, and extract text from the first few slides to confirm that we can read the content correctly.
pptx_path = SAMPLE / "DS340 – Discussion1.pptx"
prs = Presentation(pptx_path)
print(f"  Slides : {len(prs.slides)}")

#printing content from the first 3 slides 
for i, slide in enumerate(list(prs.slides)[:3], 1):
    texts = [
        shape.text.strip()
        for shape in slide.shapes
        if shape.has_text_frame and shape.text.strip()
    ]
    print(f"  Slide {i}: {' | '.join(texts[:3]) or '(no text)'}")
print()


#python-docx

print("=" * 60)
print("4. python-docx — Flaws_In_Clinical_Methodology_Kashish.docx")
print("=" * 60)

#python-docx is a library for creating and manipulating Microsoft Word (.docx) files. It allows you to read existing documents, modify text, add new paragraphs, and save the changes. You can extract text, tables, and other elements from Word documents, as well as create new documents with various formatting options.
from docx import Document

doc_path = SAMPLE / "Flaws_In_Clinical_Methodology_Kashish.docx"
doc = Document(doc_path)

#To verify python-docx, we will extract the document's core properties (like title and author) and count the number of non-empty paragraphs to confirm that we can read the content correctly.
core = doc.core_properties
print(f"  Title  : {core.title or '(not set)'}")
print(f"  Author : {core.author or '(not set)'}")

# Count non-empty paragraphs and show a preview of the first one to confirm text extraction works
non_empty = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
print(f"  Paragraphs (non-empty): {len(non_empty)}")
print(f"  First paragraph: {non_empty[0][:200] if non_empty else '(empty)'}\n")

#Summary
print("=" * 60)
print("All packages verified successfully.")
print("=" * 60)

# Restore original stdout and close the file
sys.stdout = _tee._stdout
_out_file.close()
print(f"\nResults saved to: {OUTPUT}")
