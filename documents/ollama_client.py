import re
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"


def generate_ai_answer(document_text, question):
    if not document_text or not question:
        return "Please provide document text and a question."

    prompt = f"""You are DocuSphere, an AI document assistant.
Answer the question using ONLY the document.
Do not invent facts or use outside knowledge.
If the answer is missing, say:
"I could not find this information in the provided document."
Keep the answer clear and concise.

DOCUMENT:
{document_text}

QUESTION:
{question}

ANSWER:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 150
                }
            },
            timeout=180
        )

        response.raise_for_status()
        return response.json().get(
            "response", "No answer was generated."
        ).strip()

    except requests.exceptions.ConnectionError:
        return "Ollama server is not running."

    except requests.exceptions.Timeout:
        return "AI response timed out. Please try again."

    except requests.exceptions.RequestException:
        return "There was a problem connecting to the AI model."


def split_sentences(text):
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def generate_ai_summary(document_text, sentences_count=5):
    if not document_text or not document_text.strip():
        return "No readable text found in PDF."

    sentences_count = max(1, min(sentences_count, 8))

    prompt = f"""You are DocuSphere.
Summarize this document in EXACTLY {sentences_count} sentences.
Use simple English and short, meaningful sentences.
Include the most important information only.
Use ONLY facts from the document.
Do not add a heading, introduction, numbering or extra text.
Put each sentence on a separate line.

DOCUMENT:
{document_text}

SUMMARY:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": sentences_count * 30
                }
            },
            timeout=120
        )

        response.raise_for_status()
        summary = response.json().get("response", "").strip()

        if not summary:
            return "AI could not generate a summary."

        summary = re.sub(
            r'(?m)^\s*(?:\d+[.)]|[-*])\s*',
            '',
            summary
        )

        sentences = split_sentences(summary)

        if len(sentences) < sentences_count:
            return "AI generated fewer sentences than requested. Please try again."

        sentences = sentences[:sentences_count]

        # Ensure the final sentence has punctuation.
        sentences[-1] = sentences[-1].rstrip()
        if sentences[-1][-1] not in ".!?":
            sentences[-1] += "."

        return " ".join(sentences)

    except requests.exceptions.ConnectionError:
        return "Ollama server is not running."

    except requests.exceptions.Timeout:
        return "AI summarization timed out. Please try again."

    except requests.exceptions.RequestException:
        return "There was a problem connecting to the AI model."
