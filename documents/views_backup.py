from django.shortcuts import render
from .models import Document
from .pdf_reader import extract_pdf_text, extract_pdf_pages
from .summarizer import generate_summary
from .qa import answer_question, get_relevant_text
from .ollama_client import generate_ai_answer, generate_ai_summary


def upload_document(request):
    extracted_text = ""
    extracted_pages = []
    summary = ""
    answer = ""
    selected_document_id = ""

    if request.method == 'POST':
        title = request.POST.get('title')
        uploaded_file = request.FILES.get('file')

        if title and uploaded_file:
            Document.objects.create(
                title=title,
                file=uploaded_file
            )

    documents = Document.objects.all()

    if request.GET.get('read'):
        document_id = request.GET.get('read')
        document = Document.objects.get(id=document_id)

        extracted_pages = extract_pdf_pages(document.file.path)
        extracted_text = extract_pdf_text(document.file.path)

    if request.GET.get('summary'):
        document_id = request.GET.get('summary')
        document = Document.objects.get(id=document_id)

        length = request.GET.get('length', 'medium')

        summary_lengths = {
            'short': 3,
            'medium': 5,
            'long': 8
        }

        sentences_count = summary_lengths.get(length, 5)

        text = extract_pdf_text(document.file.path)

        summary = generate_ai_summary(text, sentences_count)

        error_messages = [
            "Ollama server is not running.",
            "AI summarization timed out. Please try again.",
            "There was a problem connecting to the AI model.",
            "AI could not generate a summary.",
            "No readable text found in PDF."
        ]

        if summary in error_messages:
            summary = generate_summary(text, sentences_count)

    if request.method == 'POST' and request.POST.get('question'):
        document_id = request.POST.get('document_id')
        question = request.POST.get('question', '').strip()

        if document_id and question:
            try:
                document = Document.objects.get(id=document_id)
                selected_document_id = str(document.id)

                text = extract_pdf_text(document.file.path)

                relevant_text = get_relevant_text(text, question)

                if not relevant_text:
                    answer = "I could not find this information in the provided document."
                else:
                    answer = generate_ai_answer(relevant_text, question)

                if answer in (
                    "Ollama server is not running.",
                    "AI response timed out. Please try again.",
                    "There was a problem connecting to the AI model.",
                    "No answer was generated."
                ):
                    answer = answer_question(text, question)

            except Document.DoesNotExist:
                answer = "Selected document was not found."

        else:
            answer = "Please select a PDF and enter your question."

    return render(request, 'documents/upload.html', {
        'documents': documents,
        'extracted_text': extracted_text,
        'extracted_pages': extracted_pages,
        'summary': summary,
        'answer': answer,
        'selected_document_id': selected_document_id
    })
