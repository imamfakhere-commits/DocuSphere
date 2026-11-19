import re


SECTION_HEADINGS = [
    "What Is Artificial Intelligence?",
    "Understanding Machine Learning",
    "What Is a Digital Document?",
    "How PDF Text Extraction Works",
    "The Purpose of Automatic Summarization",
    "A Simple Document Assistant Workflow",
    "Privacy, Security, and Responsible Use",
    "Conclusion"
]


def clean_text(text):
    if not text:
        return ""

    text = text.replace("\x7f", " ")

    text = re.sub(
        r'DocuSphere[\s\-–—]*Sample Learning Document\s*Page\s*\d+',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'SAMPLE DOCUMENT|EDUCATIONAL CONTENT|END OF SAMPLE DOCUMENT',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    first_section = re.search(r'\b1\.\s+[A-Z]', text)

    if first_section:
        text = text[first_section.start():]

    for heading in SECTION_HEADINGS:
        pattern = r'\d+\.\s*' + re.escape(heading)
        text = re.sub(
            pattern,
            '\nSECTION_BREAK\n',
            text,
            flags=re.IGNORECASE
        )

    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)

    return text.strip()


def get_best_sentence(section):
    sentences = re.split(r'(?<=[.!?])\s+', section)

    scored = []

    for index, sentence in enumerate(sentences):
        sentence = sentence.strip()

        if len(sentence) < 50:
            continue

        if len(sentence) > 350:
            continue

        score = 0

        if 80 <= len(sentence) <= 250:
            score += 2

        if sentence.lower().startswith(
            ("for example", "first,", "next,", "however,")
        ):
            score -= 1

        scored.append((score, index, sentence))

    if not scored:
        return None

    scored.sort(key=lambda item: (-item[0], item[1]))

    return scored[0][2]


def generate_summary(text, sentences_count=5):
    if not text or not text.strip():
        return "No readable text found in PDF."

    cleaned_text = clean_text(text)

    sections = cleaned_text.split("SECTION_BREAK")

    representatives = []

    for section in sections:
        sentence = get_best_sentence(section)

        if sentence:
            representatives.append(sentence)

    if not representatives:
        return "Not enough meaningful text to generate a summary."

    count = min(sentences_count, len(representatives))

    if count == 1:
        selected = [representatives[0]]
    else:
        positions = [
            round(i * (len(representatives) - 1) / (count - 1))
            for i in range(count)
        ]

        selected = [representatives[i] for i in positions]

    return "\n\n".join(selected)
