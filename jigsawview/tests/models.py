"""
Models for the jigsawview tests.
"""

from __future__ import unicode_literals

from django.db import models
try:
    from django.utils.encoding import python_2_unicode_compatible
except:
    def python_2_unicode_compatible():
        return


@python_2_unicode_compatible
class MyObjectModel(models.Model):
    slug = models.CharField(max_length=16)
    other_slug_field = models.CharField(max_length=16)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return '%i' % (self.id,)

    @models.permalink
    def get_absolute_url(self):
        return ('object_detail', (), {'pk': self.id})


@python_2_unicode_compatible
class MyOtherObjectModel(models.Model):
    class Meta:
        ordering = ['id']

    def __str__(self):
        return '%i' % (self.id,)


class MyInlineModel(models.Model):

    root_obj = models.ForeignKey(MyObjectModel)
    my_data = models.CharField(max_length=32)
