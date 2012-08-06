"""
Urls for the tests
"""

from __future__ import absolute_import

from django.conf.urls import patterns, url

from jigsawview.tests.views import ObjectView, InlineObjectView


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

    url(r'^inlines/$',
        InlineObjectView.as_view(mode='list'),
        name='inline_list'),

    url(r'^inlines/new/$',
        InlineObjectView.as_view(mode='new'),
        name='inline_new'),

    url(r'^inlines/(?P<pk>\d+)/$',
        InlineObjectView.as_view(mode='detail'),
        name='inline_detail'),

    url(r'^inlines/(?P<pk>\d+)/update/$',
        InlineObjectView.as_view(mode='update'),
        name='inline_update'),

    url(r'^inlines/(?P<pk>\d+)/delete/$',
        InlineObjectView.as_view(mode='delete'),
        name='inline_delete'),
)
