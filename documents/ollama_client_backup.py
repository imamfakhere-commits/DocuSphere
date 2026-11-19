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
5. Keep the answer clear, accurate, and concise.
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
