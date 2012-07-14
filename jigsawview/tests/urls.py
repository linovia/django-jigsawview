"""
Urls for the tests
"""

from __future__ import absolute_import

from django.conf.urls import patterns, url

from jigsawview.tests.views import ObjectView


urlpatterns = patterns('',
    url(r'^objects/$',
        ObjectView.as_view(mode='list'),
        name='object_list'),

    url(r'^object/new/$',
        ObjectView.as_view(mode='new'),
        name='object_new'),

    url(r'^object/(?P<pk>\d+)/$',
        ObjectView.as_view(mode='detail'),
        name='object_detail'),

    url(r'^object/(?P<pk>\d+)/update/$',
        ObjectView.as_view(mode='update'),
        name='object_update'),

    url(r'^object/(?P<pk>\d+)/delete/$',
        ObjectView.as_view(mode='delete'),
        name='object_delete'),
)
