from django.conf import settings
from django.core.management.base import BaseCommand
from django_countries import countries
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from qdrant_client import QdrantClient

from assistant.langchain.qdrant_client import CustomQdrantClient
from document_manager.models import Document


class Command(BaseCommand):
    help = 'Upload documents to Qdrant vector DB'

    def add_arguments(self, parser):
        parser.add_argument('country', type=str, choices=[country[0] for country in countries], help='Country code')
        parser.add_argument('category', type=str, help='Document category', default=None, nargs='?')
        parser.add_argument('--recreate', action='store_true', help='Recreate the collection in Qdrant')

    def handle(self, *args, **options):
        country = options['country']
        category = options['category']
        recreate = options['recreate']

        # Fetch documents
        documents = Document.objects.filter(country=country)
        if category:
            documents = documents.filter(category=category)

        if not documents.exists():
            self.stdout.write(self.style.WARNING('No documents found for the specified country and category.'))
            return

        # Setup Qdrant client
        self.q_client = QdrantClient(url=settings.QDRANT_URL)
        embeddings = OpenAIEmbeddings(api_key=settings.OAI_KEY)
        self.qdrant_client = CustomQdrantClient(client=self.q_client, collection_name=country, embeddings=embeddings)

        # Process and upload each document
        for document in documents:
            file_hash = self.qdrant_client.generate_metadata_hash(country, category, document.document.path)
            
            
            if self.qdrant_client.is_file_uploaded(file_hash, country) and not recreate:
                self.stdout.write(self.style.ERROR('File already exists, moving on!'))
                continue

            elif self.qdrant_client.is_file_uploaded(file_hash, country) and recreate:
                self.qdrant_client.delete_prev_point(file_hash, country)

            self.stdout.write(self.style.SUCCESS('Uploading file!'))

            pdf_loader = PyPDFLoader(document.document.path)
            content = pdf_loader.load_and_split()
            payload = {
                "category": document.category,
                "file_name": document.document.name,
                "hash_id": file_hash
            }
            self.qdrant_client.from_documents(
                content, embeddings, collection_name=country, payload=payload, url=settings.QDRANT_URL
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully uploaded documents to Qdrant for country {country} and category {category}.'))
