Prerequisites
=============

The package postgresql-client should be installed on the host.


Introduction
============

django-fs-dump is the Django-related reusable app provides the ability to dump database and media files via an admin interface.


Installation
============

Install ``django-fs-dump`` using ``pip``::

    $ pip install django-fs-dump

Add the ``'fs_dump'`` application to the ``INSTALLED_APPS`` setting of your Django project ``settings.py`` file::

    INSTALLED_APPS = (
        ...
        'fs_dump',
        ...
    )

Run ``migrate``::

    $ ./manage.py migrate


Credits
=======

`Fogstream <https://fogstream.ru>`_
