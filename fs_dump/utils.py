import os
import pexpect
import shutil
import tarfile

from django.conf import settings
from django.db import connection

from . import settings as local_settings
from .models import Dump


def dump_database(dump_path):
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_name = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_pass = settings.DATABASES['default']['PASSWORD']

    command = f'pg_dump -f {dump_path} -O -d {db_name} -h {db_host} -p {db_port} -U {db_user}'
    pexpect.run(command, events={'Password': f'{db_pass}\n'})


def dump_media(dump_path):
    with tarfile.open(dump_path, 'w:gz') as targz:
        for obj_name in os.listdir(settings.MEDIA_ROOT):
            if obj_name == local_settings.UPLOAD_DIR_NAME:
                continue
            obj_path = os.path.join(settings.MEDIA_ROOT, obj_name)
            targz.add(obj_path, arcname=obj_name)

def restore_database(dump_path):
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_name = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_pass = settings.DATABASES['default']['PASSWORD']

    drop_all_sql = '''
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    '''
    with connection.cursor() as cursor:
        cursor.execute(drop_all_sql)

    command = f'psql -d {db_name} -f {dump_path} -h {db_host} -p {db_port} -U {db_user}'
    pexpect.run(command, events={'Password': f'{db_pass}\n'})


def _delete_obj(obj_path):
    if os.path.isfile(obj_path) or os.path.islink(obj_path):
        os.remove(obj_path)
    elif os.path.isdir(obj_path):
        shutil.rmtree(obj_path)


def restore_media(dump_path):
    for obj_name in os.listdir(settings.MEDIA_ROOT):
        if obj_name == local_settings.UPLOAD_DIR_NAME:
            continue
        obj_path = os.path.join(settings.MEDIA_ROOT, obj_name)
        _delete_obj(obj_path)

    with tarfile.open(dump_path, 'r:gz') as targz:
        targz.extractall(settings.MEDIA_ROOT)


def clear_fs_dump():
    Dump.objects.all().delete()

    upload_dir_path = os.path.join(settings.MEDIA_ROOT, local_settings.UPLOAD_DIR_NAME)
    for obj_name in os.listdir(upload_dir_path):
        obj_path = os.path.join(upload_dir_path, obj_name)
        _delete_obj(obj_path)
