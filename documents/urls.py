
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.upload_document, name='upload_document'),

    # Chat History
    path('delete-chat/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('clear-history/', views.clear_history, name='clear_history'),
    path('export-chat-history/', views.export_chat_history, name='export_chat_history'),

    # Document Management
    path('rename-document/<int:document_id>/', views.rename_document, name='rename_document'),
    path('delete-document/<int:document_id>/', views.delete_document, name='delete_document'),
    path('download-document/<int:document_id>/', views.download_document, name='download_document'),
]
