"""
Extract text from all documents in src/data_plane/data/ and write to extracted_data.txt.

Each ExtractedBlock is written as a clearly-delimited section so future chunking
(e.g. with HuggingFace tokenizers) can split on the separators or treat each block
as a pre-segmented chunk.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from src.data_plane.data_processing import process_file

DATA_DIR = pathlib.Path("src/data_plane/data")
OUTPUT_FILE = pathlib.Path("src/data_plane/extracted_data.txt")

SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv"}

BLOCK_SEP = "=" * 80


def main():
    files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in SUPPORTED)

    if not files:
        print(f"No supported files found in {DATA_DIR}")
        return

    total_blocks = 0
    lines = []

    for path in files:
        print(f"Processing: {path.name}")
        blocks = process_file(path)
        total_blocks += len(blocks)

        for block in blocks:
            lines.append(BLOCK_SEP)
            lines.append(f"FILE: {block.source_file}  |  TYPE: {block.source_type}  |  LOCATION: {block.location}")
            lines.append(BLOCK_SEP)
            lines.append(block.text)
            lines.append("")  # blank line after each block for readability

    lines.append(BLOCK_SEP)
    lines.append(f"TOTAL: {total_blocks} blocks from {len(files)} files")
    lines.append(BLOCK_SEP)

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDone. {total_blocks} blocks from {len(files)} files -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
