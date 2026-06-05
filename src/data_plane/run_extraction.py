"""
Extract text from all documents in src/data_plane/data/ and write to extracted_data.txt.

Each ExtractedBlock is written as a clearly-delimited section so future chunking
(e.g. with HuggingFace tokenizers) can split on the separators or treat each block
as a pre-segmented chunk.
"""

#things to consider - ways to reduce the text and noise in the extracted data 
#Right now, the pdfs are really long and while I removed the figures and footnotes, there is still a lot of text that may not be relevant for the knowledge graph. I could consider adding more rules to filter out sections that are likely to be less informative, such as sections with a lot of numbers (e.g. tables), or sections that are very short (e.g. headers). I could also consider using a more advanced NLP technique to identify and extract only the most relevant sentences or paragraphs from the documents, rather than extracting everything. This could help reduce the amount of noise and make the extracted data more focused and useful for building the knowledge graph.
#Another approach could be to use a pre-trained language model to summarize the extracted text, which could help condense the information and focus on the most important points. Additionally, I could consider using a more structured format for the extracted data, such as JSON or CSV, which would allow for easier parsing and analysis in later stages of the knowledge graph construction process. This structured format could include metadata about the source of each piece of information, such as the file name, section, and location within the document, which would help maintain context and improve the quality of the knowledge graph.
#The thing to worry about there is the accuracy and fine tuning of the model to ensure that it is summarizing the relevant information correctly, and not omitting important details or including irrelevant information. 

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from src.data_plane.data_processing import process_file

DATA_DIR = pathlib.Path("src/data_plane/data")
OUTPUT_FILE = pathlib.Path("src/data_plane/extracted_data.txt")

SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv"}

BLOCK_SEP = "=" * 80


def main():
    #Find all supported files in the data directory, sorted by name for consistent processing order. If no supported files are found, print a message and exit. Otherwise, iterate through each file, process it to extract text blocks, and accumulate the total number of blocks extracted. For each block, format it with clear separators and metadata about the source file, type, and location within the file. Finally, write all formatted blocks to the output file and print a summary of the extraction results.
    files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in SUPPORTED)

    if not files:
        print(f"No supported files found in {DATA_DIR}")
        return

    #initialize blocks and lines
    total_blocks = 0
    lines = []

    #Process each file and extract blocks, formatting them with separators and metadata for clarity. Each block is separated by a line of equal signs, followed by a header containing the file name, type, and location of the extracted text within the file. The extracted text is then added below the header, with an additional blank line for readability. After processing all files, a final summary line is added to indicate the total number of blocks extracted and the number of files processed.
    for path in files:
        print(f"Processing: {path.name}")
        blocks = process_file(path)
        total_blocks += len(blocks)

        #Format each block with clear separators and metadata about the source file, type, and location within the file. This structured formatting allows for easy parsing in future steps, such as chunking with tokenizers or further analysis. Each block is clearly delineated to maintain the context of where the extracted text came from, which can be crucial for downstream processing and understanding the content in relation to its source.
        for block in blocks:
            lines.append(BLOCK_SEP)
            lines.append(f"FILE: {block.source_file}  |  TYPE: {block.source_type}  |  LOCATION: {block.location}")
            lines.append(BLOCK_SEP)
            lines.append(block.text)
            lines.append("")  # blank line after each block for readability

    #After processing all files, a final summary line is added to indicate the total number of blocks extracted and the number of files processed. This provides a clear overview of the extraction results, allowing users to quickly understand the scope of the data that has been extracted and how many documents contributed to the final output. The summary is also separated by lines for emphasis and clarity in the output file.
    lines.append(BLOCK_SEP)
    lines.append(f"TOTAL: {total_blocks} blocks from {len(files)} files")
    lines.append(BLOCK_SEP)

    #Write all formatted blocks to the output file, ensuring that the text is encoded in UTF-8 to handle a wide range of characters. After writing the data, print a confirmation message indicating that the extraction process is complete and providing the location of the output file for easy access.
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nDone. {total_blocks} blocks from {len(files)} files -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
