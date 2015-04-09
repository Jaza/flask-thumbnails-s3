flask-thumbnails-s3
===================

An extension to create image thumbnails on Amazon S3 (or on local storage) with the Flask framework, based on flask-thumbnails.


Installation
------------

Install with ``pip``:

Run ``pip install flask-thumbnails-s3``

Add ``Thumbnail`` to your extension file:

.. code:: python

    from flask_thumbnails_s3 import Thumbnail

    app = Flask(__name__)

    thumb = Thumbnail(app)

Add ``MEDIA_FOLDER`` and ``MEDIA_URL`` in your settings, as well as various S3-related values:

.. code:: python

    app.config['MEDIA_FOLDER'] = '/home/www/media'
    app.config['MEDIA_URL'] = '/media/'
    app.config['THUMBNAIL_S3_STORAGE_TYPE'] = 's3'
    app.config['THUMBNAIL_S3_BUCKET_NAME'] = 'bucket-foo'
    app.config['THUMBNAIL_S3_ACCESS_KEY_ID'] = 'key-here'
    app.config['THUMBNAIL_S3_ACCESS_KEY_SECRET'] = 'secret-here'
    app.config['THUMBNAIL_S3_USE_HTTPS'] = True
    app.config['THUMBNAIL_S3_STATIC_ROOT_PARENT'] = '/path/to/project/root/'


Example usage
-------------

Use in Jinja2 template:

::

    <img src="{{ 'image.jpg'|thumbnail('200x200', storage_type='s3', bucket_name='bucket-foo') }}" alt="" />
    <img src="{{ 'image.jpg'|thumbnail('200x200', crop='fit', quality=100) }}" alt="" />


Options
~~~~~~~

``crop='fit'`` returns a sized and cropped version of the image, cropped to the requested aspect ratio and size, `read more <http://pillow.readthedocs.org/en/latest/reference/ImageOps.html#PIL.ImageOps.fit>`_.

``quality=XX`` changes the quality of the output JPEG thumbnail, default ``85``.


Develop and Production
----------------------

Production
~~~~~~~~~~

In production, you need to add media directory in you web server.


Develop
~~~~~~~

To service the uploaded files need a helper function, where ``/media/`` your settings ``app.config['MEDIA_URL']``:

.. code:: python

    from flask import send_from_directory

    @app.route('/media/<regex("([\w\d_/-]+)?.(?:jpe?g|gif|png)"):filename>')
    def media_file(filename):
        return send_from_directory(app.config['MEDIA_THUMBNAIL_FOLDER'], filename)


Option settings
---------------

If you want to store the thumbnail in a folder other than the ``MEDIA_FOLDER``, you need to set it manually:

.. code:: python

    app.config['MEDIA_THUMBNAIL_FOLDER'] = '/home/www/media/cache'
    app.config['MEDIA_THUMBNAIL_URL'] = '/media/cache/'


Acknowledgements
----------------

Much of the code here is based on flask-thumbnails by Dmitriy Sokolov:

https://github.com/silentsokolov/flask-thumbnails

Many thanks to the author and contributors of flask-thumbnails, for the foundation of this codebase, and for the generous license terms that allow forks like this.
