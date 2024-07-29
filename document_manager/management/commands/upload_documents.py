import glob
import os
import tempfile
import zipfile

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django_countries import countries

from document_manager.models import Document


def get_filename(filename):
    return filename.split('/')[-1].split('.')[0]


class Command(BaseCommand):
    help = 'Upload documents to document model'

    def add_arguments(self, parser):
        parser.add_argument(
            'path', type=str, help='Path to a zip file or folder')
        parser.add_argument('country', type=str, help='Country code', choices=[
                            country[0] for country in countries])

    def handle(self, *args, **options):
        path = options['path']
        country = options['country']

        with tempfile.TemporaryDirectory() as temp_folder:
            if os.path.isfile(path) and zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)
                    folder_path = os.path.join(temp_folder, get_filename(path))
            elif os.path.isdir(path):
                folder_path = path
            else:
                self.stdout.write(self.style.ERROR('Invalid path'))
                return

            pdf_files = glob.glob(os.path.join(
                folder_path, '**', '*.pdf'), recursive=True)

            for pdf_file_path in pdf_files:
                category = os.path.basename(os.path.dirname(pdf_file_path))
                pdf_file = os.path.basename(pdf_file_path)

                try:
                    document = Document(country=country, category=category)
                    document.document.save(pdf_file, open(pdf_file_path, 'rb'))
                    self.stdout.write(self.style.SUCCESS(
                        f'Sucessfully saved document: {pdf_file}'))
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(
                        f'Error saving document: {pdf_file} - Error: {e}'))
