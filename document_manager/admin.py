from django.contrib import admin

from document_manager.models import Document


class DocumentAdmin(admin.ModelAdmin):
    search_fields = ['category']


admin.site.register(Document, DocumentAdmin)
