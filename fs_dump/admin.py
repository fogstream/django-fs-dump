import os
from functools import update_wrapper

from django.contrib import admin
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat
from django.utils.html import format_html

from . import utils
from .models import Dump


@admin.register(Dump)
class DumpAdmin(admin.ModelAdmin):
    """
    """

    list_display = ('id', 'created_at', '_download_database_dump', '_download_media_dump')
    readonly_fields = ('created_at',)

    def _download_database_dump(self, obj):
        file_name = os.path.basename(obj.database_dump.name)
        try:
            file_size = filesizeformat(obj.database_dump.size)
        except FileNotFoundError:
            file_size = 0
        link = format_html(f'<a href="{obj.database_dump.url}">{file_name}</a> ({file_size})')
        return link
    _download_database_dump.short_description = 'Database Dump'

    def _download_media_dump(self, obj):
        file_name = os.path.basename(obj.media_dump.name)
        try:
            file_size = filesizeformat(obj.media_dump.size)
        except FileNotFoundError:
            file_size = 0
        link = format_html(f'<a href="{obj.media_dump.url}">{file_name}</a> ({file_size})')
        return link
    _download_media_dump.short_description = 'Media Dump'

    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urls = [
            path('create/', wrap(self.create_view), name='%s_%s_create' % info),
            path('upload/', wrap(self.upload_view), name='%s_%s_upload' % info),
        ] + super().get_urls()

        return urls

    def create_view(self, request, form_url='', extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied

        dump = Dump.objects.create()

        dump.database_dump.save(f'{dump.id}_database_dump.psql', ContentFile(''))
        dump.media_dump.save(f'{dump.id}_media_dump.tar.gz', ContentFile(''))

        utils.dump_database(dump.database_dump.path)
        utils.dump_media(dump.media_dump.path)

        dump.save()

        change_list_view = f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
        return redirect(change_list_view)

    def upload_view(self, request, form_url='', extra_context=None):
        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        form = ModelForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            dump = self.save_form(request, form, change=False)
            self.save_model(request, dump, form, False)

            if dump.database_dump:
                utils.restore_database(dump.database_dump.path)
            if dump.media_dump:
                utils.restore_media(dump.media_dump.path)
            if dump.database_dump or dump.media_dump:
                utils.clear_fs_dump()

            return redirect('admin:index')

        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request)),
            {},
            self.get_readonly_fields(request),
            model_admin=self
        )
        media = self.media + adminForm.media

        title = 'Upload & Restore'

        context = {
            **self.admin_site.each_context(request),
            'title': title,
            'adminform': adminForm,
            'object_id': None,
            'original': None,
            'is_popup': False,
            'to_field': None,
            'media': media,
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'preserved_filters': '',
            'show_save_and_add_another': False,
            'show_save_and_continue': False,
        }

        context.update(extra_context or {})

        return self.render_change_form(request, context, add=True, change=False, form_url=form_url)
