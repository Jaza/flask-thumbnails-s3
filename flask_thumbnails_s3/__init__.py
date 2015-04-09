__version__ = '0.1.3'

import errno
import httplib2
from io import BytesIO
import os
import re
import urllib2 as urllib

try:
    from PIL import Image, ImageOps
except ImportError:
    raise RuntimeError('Image module of PIL needs to be installed')

from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
from boto.s3.key import Key

from flask import url_for
from url_for_s3 import url_for_s3


class Thumbnail(object):
    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        self.app = app

        if not self.app.config.get('MEDIA_FOLDER', None):
            raise RuntimeError('You\'re using the flask-thumbnail-s3 app '
                               'without having set the required MEDIA_FOLDER setting.')

        if self.app.config.get('MEDIA_THUMBNAIL_FOLDER', None) and not self.app.config.get('MEDIA_THUMBNAIL_URL', None):
            raise RuntimeError('You\'re set MEDIA_THUMBNAIL_FOLDER setting, need set and MEDIA_THUMBNAIL_URL setting.')

        app.config.setdefault('MEDIA_THUMBNAIL_FOLDER', os.path.join(self.app.config['MEDIA_FOLDER'], ''))
        app.config.setdefault('MEDIA_URL', '/')
        app.config.setdefault('MEDIA_THUMBNAIL_URL', os.path.join(self.app.config['MEDIA_URL'], ''))

        app.jinja_env.filters['thumbnail'] = self.thumbnail

    def _thumbnail_resize(self, image, thumb_size, crop=None, bg=None):
        """Performs the actual image cropping operation with PIL."""

        if crop == 'fit':
            img = ImageOps.fit(image, thumb_size, Image.ANTIALIAS)
        else:
            img = image.copy()
            img.thumbnail(thumb_size, Image.ANTIALIAS)

        if bg:
            img = self._bg_square(img, bg)

        return img

    def _thumbnail_local(self, original_filename, thumb_filename,
                         thumb_size, thumb_url, crop=None, bg=None,
                         quality=85):
        """Finds or creates a thumbnail for the specified image on the local filesystem."""

        # create folders
        self._get_path(thumb_filename)

        thumb_url_full = url_for('static', filename=thumb_url)

        # Return the thumbnail URL now if it already exists locally
        if os.path.exists(thumb_filename):
            return thumb_url_full

        try:
            image = Image.open(original_filename)
        except IOError:
            return ''

        img = self._thumbnail_resize(image, thumb_size, crop=crop, bg=bg)

        img.save(thumb_filename, image.format, quality=quality)

        return thumb_url_full

    def _thumbnail_s3(self, original_filename, thumb_filename,
                      thumb_size, thumb_url, bucket_name,
                      crop=None, bg=None, quality=85):
        """Finds or creates a thumbnail for the specified image on Amazon S3."""

        scheme = self.app.config.get('THUMBNAIL_S3_USE_HTTPS') and 'https' or 'http'

        thumb_url_full = url_for_s3(
            'static',
            bucket_name=bucket_name,
            filename=thumb_url,
            scheme=scheme)
        original_url_full = url_for_s3(
            'static',
            bucket_name=bucket_name,
            filename=self._get_s3_path(original_filename).replace('static/', ''),
            scheme=scheme)

        # Return the thumbnail URL now if it already exists on S3.
        # HTTP HEAD request saves us actually downloading the image
        # for this check.
        # Thanks to:
        # http://stackoverflow.com/a/16778749/2066849
        try:
            resp = httplib2.Http().request(thumb_url_full, 'HEAD')
            resp_status = int(resp[0]['status'])
            assert(resp_status < 400)
            return thumb_url_full
        except Exception:
            pass

        # Thanks to:
        # http://stackoverflow.com/a/12020860/2066849
        try:
            fd = urllib.urlopen(original_url_full)
            temp_file = BytesIO(fd.read())
            image = Image.open(temp_file)
        except Exception:
            return ''

        img = self._thumbnail_resize(image, thumb_size, crop=crop, bg=bg)

        temp_file = BytesIO()
        img.save(temp_file, image.format, quality=quality)

        conn = S3Connection(self.app.config.get('THUMBNAIL_S3_ACCESS_KEY_ID'), self.app.config.get('THUMBNAIL_S3_ACCESS_KEY_SECRET'))
        bucket = conn.get_bucket(bucket_name)

        path = self._get_s3_path(thumb_filename)
        k = bucket.new_key(path)

        try:
            k.set_contents_from_string(temp_file.getvalue())
            k.set_acl(self.app.config.get('THUMBNAIL_S3_ACL', 'public-read'))
        except S3ResponseError:
            return ''

        return thumb_url_full

    def thumbnail(self, img_url, size, crop=None, bg=None, quality=85,
                  storage_type=None, bucket_name=None):
        """
        :param img_url: url img - '/assets/media/summer.jpg'
        :param size: size return thumb - '100x100'
        :param crop: crop return thumb - 'fit' or None
        :param bg: tuple color or None - (255, 255, 255, 0)
        :param quality: JPEG quality 1-100
        :param storage_type: either 's3' or None
        :param bucket_name: s3 bucket name
        :return: :thumb_url:
        """

        width, height = [int(x) for x in size.split('x')]
        thumb_size = (width, height)
        url_path, img_name = os.path.split(img_url)
        name, fm = os.path.splitext(img_name)

        miniature = self._get_name(name, fm, size, crop, bg, quality)

        original_filename = os.path.join(self.app.config['MEDIA_FOLDER'], url_path, img_name)
        thumb_filename = os.path.join(self.app.config['MEDIA_THUMBNAIL_FOLDER'], url_path, miniature)

        thumb_url = os.path.join(self.app.config['MEDIA_THUMBNAIL_URL'], url_path, miniature)

        if not (storage_type and bucket_name):
            return self._thumbnail_local(original_filename,
                                         thumb_filename,
                                         thumb_size,
                                         thumb_url,
                                         crop=crop,
                                         bg=bg,
                                         quality=quality)
        else:
            if storage_type != 's3':
                raise ValueError('Storage type "%s" is invalid, the only supported storage type (apart from default local storage) is s3.' % storage_type)

            return self._thumbnail_s3(original_filename,
                                      thumb_filename,
                                      thumb_size,
                                      thumb_url,
                                      bucket_name,
                                      crop=crop,
                                      bg=bg,
                                      quality=quality)

    def _get_s3_path(self, filename):
        static_root_parent = self.app.config.get('THUMBNAIL_S3_STATIC_ROOT_PARENT', None)
        if not static_root_parent:
            raise ValueError('S3Save requires static_root_parent to be set.')

        return re.sub('^\/', '', filename.replace(static_root_parent, ''))

    @staticmethod
    def _bg_square(img, color=0xff):
        size = (max(img.size),) * 2
        layer = Image.new('L', size, color)
        layer.paste(img, tuple(map(lambda x: (x[0] - x[1]) / 2, zip(size, img.size))))
        return layer

    @staticmethod
    def _get_path(full_path):
        directory = os.path.dirname(full_path)

        try:
            if not os.path.exists(full_path):
                os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    @staticmethod
    def _get_name(name, fm, *args):
        for v in args:
            if v:
                name += '_%s' % v
        name += fm

        return name
