import os

import setuptools

module_path = os.path.join(os.path.dirname(__file__), 'flask_thumbnails_s3/__init__.py')
version_line = [line for line in open(module_path)
                if line.startswith('__version__')][0]

__version__ = version_line.split('__version__ = ')[-1][1:][:-2]

setuptools.setup(
    name='flask-thumbnails-s3',
    version=__version__,
    url='https://github.com/Jaza/flask-thumbnails-s3',

    license='MIT',
    author='Jeremy Epstein',
    author_email='jazepstein@gmail.com',

    description='An extension to create image thumbnails on Amazon S3 (or on local storage) with the Flask framework, based on flask-thumbnails.',
    long_description=open('README.rst').read(),

    packages=['flask_thumbnails_s3'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',

    install_requires=[
        'Flask',
        'Pillow',
    ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)

