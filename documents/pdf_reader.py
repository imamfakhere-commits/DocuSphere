import re
import unicodedata
from pypdf import PdfReader


def is_heading(line):
    words = line.split()

    if not words or len(words) > 10:
        return False

    if line.isupper():
        return True

    small_words = {"and", "or", "of", "the", "to", "in", "for"}

    return (
        not line.endswith((".", ",", "?", "!"))
        and all(
            word[0].isupper() or word.lower() in small_words
            for word in words
        )
        and any(word[0].isupper() for word in words)
    )


def clean_pdf_text(text):
    if not text:
        return ""

    text = text.replace("\xa0", " ")

    text = "".join(
        char for char in text
        if char in "\n\t" or not unicodedata.category(char).startswith("C")
    )

    paragraphs = []
    current_lines = []

    def save_paragraph():
        if current_lines:
            paragraphs.append(" ".join(current_lines))
            current_lines.clear()

    for line in text.splitlines():
        line = line.strip()

        if not line:
            save_paragraph()
            continue

        if re.search(
            r"DocuSphere.*Sample Learning Document",
            line,
            re.IGNORECASE
        ):
            continue

        if re.fullmatch(r"Page\s+\d+", line, re.IGNORECASE):
            continue

        if re.fullmatch(r"End of sample document", line, re.IGNORECASE):
            continue

        if re.fullmatch(r"SAMPLE DOCUMENT\s*[-–|]?\s*EDUCATIONAL CONTENT", line, re.IGNORECASE):
            continue

        if re.match(r"^\d+\.\s+", line) or is_heading(line):
            save_paragraph()
            paragraphs.append(line)
            continue

        current_lines.append(line)

    save_paragraph()

    return "\n\n".join(paragraphs)


def extract_pdf_pages(file_path):
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = clean_pdf_text(page_text)

        pages.append({
            "page_number": page_number,
            "text": page_text
        })

    return pages


def extract_pdf_text(file_path):
    pages = extract_pdf_pages(file_path)

    return "\n\n".join(
        page["text"]
        for page in pages
        if page["text"]
    )
