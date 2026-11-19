
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"


def generate_ai_answer(document_text, question):
    if not document_text or not question:
        return "Please provide document text and a question."

    prompt = f"""You are DocuSphere, an AI document assistant.

STRICT ANSWERING RULES:
1. Answer only using information explicitly supported by the provided document text.
2. Do not use outside knowledge or invent facts.
3. Do not guess or make unsupported assumptions.
4. If the document text does not contain the answer, reply:
   "I could not find this information in the provided document."
5. Keep the answer clear, accurate and concise.
6. Use simple language.

DOCUMENT TEXT:
{document_text}

USER QUESTION:
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
                "keep_alive": "10m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": 200
                }
            },
            timeout=180
        )

        response.raise_for_status()
        result = response.json()

        return result.get(
            "response",
            "No answer was generated."
        ).strip()

    except requests.exceptions.ConnectionError:
        return "Ollama server is not running."

    except requests.exceptions.Timeout:
        return "AI response timed out. Please try again."

    except requests.exceptions.RequestException:
        return "There was a problem connecting to the AI model."


def generate_ai_summary(document_text, sentences_count=5):
    if not document_text or not document_text.strip():
        return "No readable text found in PDF."

    sentences_count = max(1, min(sentences_count, 8))

    token_limits = {
        3: 120,
        5: 200,
        8: 300
    }

    num_predict = token_limits.get(sentences_count, 200)

    prompt = f"""You are DocuSphere, an AI document summarization assistant.

TASK:
Create a clear and accurate summary of the provided document.

STRICT RULES:
1. Use ONLY information from the document.
2. Do not add outside knowledge.
3. Do not invent facts or examples.
4. Preserve the main ideas and important information.
5. Use simple, understandable English.
6. Avoid unnecessary repetition.
7. Write approximately {sentences_count} sentences.
8. Do not include an introduction.
9. Return only the summary.

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
                "keep_alive": "10m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": num_predict
                }
            },
            timeout=180
        )

        response.raise_for_status()
        result = response.json()

        summary = result.get("response", "").strip()

        if not summary:
            return "AI could not generate a summary."

        return summary

    except requests.exceptions.ConnectionError:
        return "Ollama server is not running."

    except requests.exceptions.Timeout:
        return "AI summarization timed out. Please try again."

    except requests.exceptions.RequestException:
        return "There was a problem connecting to the AI model."
