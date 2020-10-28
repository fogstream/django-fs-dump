import os
import pexpect
import tarfile

from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html

from .models import Dump
from .models import UPLOAD_DIR_NAME


@admin.register(Dump)
class DumpAdmin(admin.ModelAdmin):
    """
    """

    list_display = ('id', 'created_at', '_download_database_dump', '_download_media_dump')
    readonly_fields = ('created_at',)

    def _download_database_dump(self, obj):
        file_name = os.path.basename(obj.database_dump.name)
        file_size = filesizeformat(obj.database_dump.size)
        link = format_html(f'<a href="{obj.database_dump.url}">{file_name}</a> ({file_size})')
        return link
    _download_database_dump.short_description = 'Database Dump'

    def _download_media_dump(self, obj):
        file_name = os.path.basename(obj.media_dump.name)
        file_size = filesizeformat(obj.media_dump.size)
        link = format_html(f'<a href="{obj.media_dump.url}">{file_name}</a> ({file_size})')
        return link
    _download_media_dump.short_description = 'Media Dump'

    def add_view(self, request, form_url='', extra_context=None):
        dump = Dump.objects.create()

        dump.database_dump.save(f'{dump.id}_database_dump.psql', ContentFile(''))
        dump.media_dump.save(f'{dump.id}_media_dump.tar.gz', ContentFile(''))

        self._dump_pg_db(dump)
        self._dump_media(dump)

        dump.save()

        change_list_view = f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
        return redirect(change_list_view)

    def _dump_pg_db(self, dump):
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_pass = settings.DATABASES['default']['PASSWORD']

        command = f'pg_dump -f {dump.database_dump.path} -O -d {db_name} -h {db_host} -p {db_port} -U {db_user}'
        child = pexpect.run(command, events={'Password: ': f'{db_pass}\n'})
        dump.output = f'{command}\n' + str(child, 'utf-8')

    def _dump_media(self, dump):
        with tarfile.open(dump.media_dump.path, 'w:gz') as targz:
            for obj_name in os.listdir(settings.MEDIA_ROOT):
                if obj_name == UPLOAD_DIR_NAME:
                    continue
                obj_path = os.path.join(settings.MEDIA_ROOT, obj_name)
                targz.add(obj_path, arcname=obj_name)
