import os
import re
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")


def _call_groq(prompt, max_tokens=250, temperature=0.1, timeout=60):
    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        return ""
    return (choices[0].get("message", {}).get("content") or "").strip()


def _call_ollama(prompt, num_predict=150, temperature=0.1, timeout=180):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "No answer was generated.").strip()


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
        if GROQ_API_KEY:
            answer = _call_groq(prompt, max_tokens=200, temperature=0.1, timeout=60)
            return answer or "No answer was generated."
        return _call_ollama(prompt, num_predict=150, temperature=0.1, timeout=180)

    except requests.exceptions.ConnectionError:
        if GROQ_API_KEY:
            return "There was a problem connecting to the Groq API."
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
        if GROQ_API_KEY:
            summary = _call_groq(
                prompt,
                max_tokens=sentences_count * 45,
                temperature=0.1,
                timeout=60,
            )
        else:
            summary = _call_ollama(
                prompt,
                num_predict=sentences_count * 30,
                temperature=0.1,
                timeout=120,
            )

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

        sentences[-1] = sentences[-1].rstrip()
        if sentences[-1][-1] not in ".!?":
            sentences[-1] += "."

        return " ".join(sentences)

    except requests.exceptions.ConnectionError:
        if GROQ_API_KEY:
            return "There was a problem connecting to the Groq API."
        return "Ollama server is not running."

    except requests.exceptions.Timeout:
        return "AI summarization timed out. Please try again."

    except requests.exceptions.RequestException:
        return "There was a problem connecting to the AI model."
