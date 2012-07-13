"""
jigsawview
~~~~~~~~~~

:copyright: (c) 2012 by Linovia, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('jigsawview').version
except Exception, e:
    VERSION = 'unknown'


from jigsawview.views import JigsawView
