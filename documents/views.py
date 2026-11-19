
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable
)

from .models import Document, ChatHistory
from .pdf_reader import extract_pdf_text, extract_pdf_pages
from .summarizer import generate_summary
from .qa import answer_question, get_relevant_text
from .ollama_client import generate_ai_answer, generate_ai_summary


# ==============================
# AUTHENTICATION VIEWS
# ==============================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('upload_document')

    form = AuthenticationForm(
        request,
        data=request.POST or None
    )

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('upload_document')

    return render(
        request,
        'registration/login.html',
        {'form': form}
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('upload_document')

    form = UserCreationForm(
        request.POST or None
    )

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('upload_document')

    return render(
        request,
        'registration/register.html',
        {'form': form}
    )


@login_required(login_url='login')
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


# ==============================
# DOCUMENT DASHBOARD
# ==============================

@login_required(login_url='login')
def upload_document(request):
    extracted_text = ""
    extracted_pages = []
    summary = ""
    answer = ""
    selected_document_id = ""
    upload_error = ""

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        uploaded_file = request.FILES.get('file')
        category = request.POST.get('category', 'Other')

        if title and uploaded_file:
            file_name = uploaded_file.name.lower()
            file_header = uploaded_file.read(5)
            uploaded_file.seek(0)

            if not file_name.endswith('.pdf'):
                upload_error = "Invalid file type. Please upload a PDF file."

            elif file_header != b'%PDF-':
                upload_error = "Invalid PDF file. Please upload a valid PDF."

            else:
                Document.objects.create(
                    user=request.user,
                    title=title[:200],
                    file=uploaded_file,
                    category=category
                )

    documents = Document.objects.filter(
        user=request.user
    ).order_by('-uploaded_at')

    if request.GET.get('read'):
        document = get_object_or_404(
            Document,
            id=request.GET.get('read'),
            user=request.user
        )

        extracted_pages = extract_pdf_pages(document.file.path)
        extracted_text = extract_pdf_text(document.file.path)

    if request.GET.get('summary'):
        document = get_object_or_404(
            Document,
            id=request.GET.get('summary'),
            user=request.user
        )

        length = request.GET.get('length', 'medium')

        summary_lengths = {
            'short': 3,
            'medium': 5,
            'long': 8
        }

        sentences_count = summary_lengths.get(length, 5)

        cache_key = (
            f"docusphere_summary_{request.user.id}_"
            f"{document.id}_{length}"
        )

        summary = cache.get(cache_key)

        if summary is None:
            text = extract_pdf_text(document.file.path)

            summary = generate_ai_summary(
                text,
                sentences_count
            )

            error_messages = [
                "Ollama server is not running.",
                "AI summarization timed out. Please try again.",
                "There was a problem connecting to the AI model.",
                "AI could not generate a summary.",
                "No readable text found in PDF.",
                "AI generated fewer sentences than requested. Please try again."
            ]

            if summary in error_messages:
                summary = generate_summary(
                    text,
                    sentences_count
                )
            else:
                cache.set(cache_key, summary, 86400)

    if request.method == 'POST' and request.POST.get('question'):
        document_id = request.POST.get('document_id')
        question = request.POST.get('question', '').strip()

        if document_id and question:
            document = get_object_or_404(
                Document,
                id=document_id,
                user=request.user
            )

            selected_document_id = str(document.id)

            text = extract_pdf_text(document.file.path)
            relevant_text = get_relevant_text(text, question)

            if not relevant_text:
                answer = (
                    "I could not find this information "
                    "in the provided document."
                )
            else:
                answer = generate_ai_answer(
                    relevant_text,
                    question
                )

            if answer in (
                "Ollama server is not running.",
                "AI response timed out. Please try again.",
                "There was a problem connecting to the AI model.",
                "No answer was generated."
            ):
                answer = answer_question(text, question)

            ChatHistory.objects.create(
                document=document,
                question=question,
                answer=answer
            )

        else:
            answer = "Please select a PDF and enter your question."

    chat_history = ChatHistory.objects.filter(
        document__user=request.user
    ).select_related(
        'document'
    ).order_by('-created_at')[:50]

    return render(request, 'documents/upload.html', {
        'documents': documents,
        'extracted_text': extracted_text,
        'extracted_pages': extracted_pages,
        'summary': summary,
        'answer': answer,
        'selected_document_id': selected_document_id,
        'upload_error': upload_error,
        'chat_history': chat_history
    })


# ==============================
# CHAT HISTORY
# ==============================

@login_required(login_url='login')
@require_POST
def delete_chat(request, chat_id):
    chat = get_object_or_404(
        ChatHistory,
        id=chat_id,
        document__user=request.user
    )

    chat.delete()

    return redirect('/#history')


@login_required(login_url='login')
@require_POST
def clear_history(request):
    ChatHistory.objects.filter(
        document__user=request.user
    ).delete()

    return redirect('/#history')


@login_required(login_url='login')
@require_GET
def export_chat_history(request):
    document_id = request.GET.get('document_id')

    chats = ChatHistory.objects.filter(
        document__user=request.user
    ).select_related(
        'document'
    ).order_by('-created_at')

    selected_document = None

    if document_id:
        selected_document = get_object_or_404(
            Document,
            id=document_id,
            user=request.user
        )

        chats = chats.filter(document=selected_document)

    filename = "DocuSphere_Chat_History.pdf"

    if selected_document:
        filename = (
            f"DocuSphere_Document_{selected_document.id}_"
            "Chat_History.pdf"
        )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{filename}"'
    )

    pdf = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocuSphereTitle',
        parent=styles['Title'],
        textColor=colors.HexColor('#263b80'),
        fontSize=22,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        'ChatHeading',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#263b80'),
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'ChatBody',
        parent=styles['BodyText'],
        fontSize=9,
        leading=14,
        spaceAfter=7,
        wordWrap='CJK'
    )

    story = []

    story.append(
        Paragraph('DocuSphere', title_style)
    )

    if selected_document:
        subtitle = (
            f"Chat History: {escape(selected_document.title)}"
        )
    else:
        subtitle = "All Chat History"

    story.append(
        Paragraph(
            f'{subtitle} | Powered by Nexora AI',
            styles['Normal']
        )
    )

    story.append(Spacer(1, 18))

    if not chats.exists():
        story.append(
            Paragraph(
                'No chat history is available.',
                body_style
            )
        )

    else:
        story.append(
            Paragraph(
                f'Total Conversations: {chats.count()}',
                styles['Heading3']
            )
        )

        story.append(Spacer(1, 10))

        for number, chat in enumerate(chats, start=1):

            story.append(
                Paragraph(
                    f'{number}. {escape(chat.document.title)}',
                    heading_style
                )
            )

            story.append(
                Paragraph('<b>Question:</b>', body_style)
            )

            question = escape(chat.question).replace(
                '\n', '<br/>'
            )

            story.append(
                Paragraph(question, body_style)
            )

            story.append(
                Paragraph('<b>AI Answer:</b>', body_style)
            )

            answer = escape(chat.answer).replace(
                '\n', '<br/>'
            )

            story.append(
                Paragraph(answer, body_style)
            )

            date_text = chat.created_at.strftime(
                '%d %b %Y, %I:%M %p'
            )

            story.append(
                Paragraph(
                    f'<font color="#777777">Date: {date_text}</font>',
                    body_style
                )
            )

            story.append(
                HRFlowable(
                    width='100%',
                    thickness=0.5,
                    color=colors.lightgrey,
                    spaceBefore=5,
                    spaceAfter=8
                )
            )

    pdf.build(story)

    return response


# ==============================
# DOCUMENT MANAGEMENT
# ==============================

@login_required(login_url='login')
@require_POST
def rename_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        user=request.user
    )

    new_title = request.POST.get('title', '').strip()

    if new_title:
        document.title = new_title[:200]

        document.save(
            update_fields=['title']
        )

    return redirect('/#documents')


@login_required(login_url='login')
@require_POST
def delete_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        user=request.user
    )

    file_name = (
        document.file.name if document.file else None
    )

    storage = (
        document.file.storage if document.file else None
    )

    document.delete()

    if file_name and not Document.objects.filter(
        file=file_name
    ).exists():
        storage.delete(file_name)

    return redirect('/#documents')


@login_required(login_url='login')
@require_GET
def download_document(request, document_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        user=request.user
    )

    response = HttpResponse(
        document.file.open('rb'),
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="{document.file.name.split("/")[-1]}"'
    )

    return response
