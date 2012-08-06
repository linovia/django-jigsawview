"""
Models for the jigsawview tests.
"""


from django.db import models


class MyObjectModel(models.Model):
    slug = models.CharField(max_length=16)
    other_slug_field = models.CharField(max_length=16)

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return u'%i' % (self.id,)

    @models.permalink
    def get_absolute_url(self):
        return ('object_detail', (), {'pk': self.id})


class MyOtherObjectModel(models.Model):
    class Meta:
        ordering = ['id']

    def __unicode__(self):
        return u'%i' % (self.id,)


class MyInlineModel(models.Model):

    root_obj = models.ForeignKey(MyObjectModel)
    data = models.CharField(max_length=32)
