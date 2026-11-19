import re


STOP_WORDS = {
    "what", "is", "are", "was", "were", "the", "a", "an",
    "in", "on", "of", "to", "for", "and", "or", "how",
    "why", "when", "where", "who", "which", "with", "do",
    "does", "did", "can", "could", "would", "should", "tell",
    "me", "about", "explain", "please"
}


def get_relevant_text(document_text, question, max_sentences=8):
    if not document_text or not question:
        return ""

    text = re.sub(
        r'A Practical Introduction to Artificial Intelligence',
        '',
        document_text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'DocuSphere|Sample Learning Document|Page\s+\d+',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r'\s+', ' ', text).strip()

    question_words = {
        word.lower()
        for word in re.findall(r'\b[a-zA-Z]{3,}\b', question)
        if word.lower() not in STOP_WORDS
    }

    if not question_words:
        return ""

    sentences = re.split(r'(?<=[.!?])\s+', text)
    scored_sentences = []

    for index, sentence in enumerate(sentences):
        sentence = sentence.strip()

        if len(sentence) < 25 or len(sentence) > 500:
            continue

        if sentence.endswith("?"):
            continue

        sentence_words = {
            word.lower()
            for word in re.findall(r'\b[a-zA-Z]{3,}\b', sentence)
        }

        matched_words = question_words.intersection(sentence_words)

        if matched_words:
            score = len(matched_words)
            scored_sentences.append((score, index, sentence))

    if not scored_sentences:
        return ""

    scored_sentences.sort(key=lambda item: (-item[0], item[1]))

    selected = scored_sentences[:max_sentences]
    selected.sort(key=lambda item: item[1])

    return " ".join(item[2] for item in selected)


def answer_question(document_text, question):
    if not document_text or not question:
        return "Please provide a question and a readable PDF."

    relevant_text = get_relevant_text(
        document_text,
        question,
        max_sentences=3
    )

    if not relevant_text:
        return "I could not find a relevant answer in this PDF."

    return relevant_text
