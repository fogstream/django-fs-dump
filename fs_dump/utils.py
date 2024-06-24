import os
import pexpect
import shutil
import tarfile

from django.conf import settings
from django.db import connection

from . import settings as local_settings
from .models import Dump


def dump_database(dump):
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_name = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_pass = settings.DATABASES['default']['PASSWORD']

    command = f'pg_dump -f {dump.database_dump.path} -O -d {db_name} -h {db_host} -p {db_port} -U {db_user}'
    child = pexpect.run(command, events={'Password': f'{db_pass}\n'})
    dump.output = f'{command}\n' + str(child, 'utf-8')


def dump_media(dump):
    with tarfile.open(dump.media_dump.path, 'w:gz') as targz:
        for obj_name in os.listdir(settings.MEDIA_ROOT):
            if obj_name == local_settings.UPLOAD_DIR_NAME:
                continue
            obj_path = os.path.join(settings.MEDIA_ROOT, obj_name)
            targz.add(obj_path, arcname=obj_name)

def restore_database(dump):
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

    command = f'psql -d {db_name} -f {dump.database_dump.path} -h {db_host} -p {db_port} -U {db_user}'
    child = pexpect.run(command, events={'Password': f'{db_pass}\n'})


def delete_obj(obj_path):
    if os.path.isfile(obj_path) or os.path.islink(obj_path):
        os.remove(obj_path)
    elif os.path.isdir(obj_path):
        shutil.rmtree(obj_path)


def restore_media(dump):
    for obj_name in os.listdir(settings.MEDIA_ROOT):
        if obj_name == local_settings.UPLOAD_DIR_NAME:
            continue
        obj_path = os.path.join(settings.MEDIA_ROOT, obj_name)
        delete_obj(obj_path)

    with tarfile.open(dump.media_dump.path, 'r:gz') as targz:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(targz, settings.MEDIA_ROOT)

def clear_fs_dump():
    Dump.objects.all().delete()

    upload_dir_path = os.path.join(settings.MEDIA_ROOT, local_settings.UPLOAD_DIR_NAME)
    for obj_name in os.listdir(upload_dir_path):
        obj_path = os.path.join(upload_dir_path, obj_name)
        delete_obj(obj_path)
