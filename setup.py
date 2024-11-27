import setuptools


setuptools.setup(
    name='django-fs-dump',
    version='1.0.0',
    packages=['fs_dump'],
    include_package_data=True,
    install_requires=['pexpect==4.9.0'],
    author='Yuri Lya',
    author_email='yuri.lya@fogstream.ru',
    url='https://github.com/fogstream/django-fs-dump',
    license='The MIT License (MIT)',
    description='The Django-related reusable app provides the ability to dump database and media files via an admin interface.',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    python_requires='>=3.6'
)
