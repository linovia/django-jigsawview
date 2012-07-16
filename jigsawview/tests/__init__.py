"""
Unit tests for the jigsawview application
"""

from mock import Mock

# from unittest2 import TestCase
from django.test import TestCase
from django.test import RequestFactory


from jigsawview.pieces import Piece
from jigsawview.views import JigsawView

from jigsawview.tests.models import MyObjectModel, MyOtherObjectModel
from jigsawview.tests.views import MyObjectPiece

#
# Various test Pieces and View definitions
#


class MyPiece1(Piece):
    template_name_prefix = 'my_piece'

    def get_context_data(self, request, context, *args, **kwargs):
        context['my_piece_1'] = 'azerty'
        return context


class MyPiece2(Piece):
    pass


class DiscardContextPiece(Piece):
    def get_context_data(self, request, context, *args, **kwargs):
        return {}


class ContextDependsOnModePiece(Piece):
    def get_context_data(self, request, context, mode, *args, **kwargs):
        context.update({
            mode: True,
        })
        return context


class MyView1(JigsawView):
    piece1 = MyPiece1()
    piece2 = MyPiece2()


class MyView2(JigsawView):
    piece2 = MyPiece2()
    piece1 = MyPiece1()


class MySubView(MyView1):
    piece3 = MyPiece1()


class MySubView2(MyView2):
    piece3 = MyPiece1()


class MyView4(JigsawView):
    piece1 = MyPiece1(default_mode='list')


class DiscardContextView(MyView1):
    discard_context_piece = DiscardContextPiece()


class ContextDependsOnModeView(MyView1):
    mode_dependant_context = ContextDependsOnModePiece()


#
# TESTS FOR THE PIECE IN VIEWS - ORDERING, TYPES...
#


class TestJigsawViewPiece(TestCase):

    def test_two_Piece_instances_have_different_creation_counter(self):
        piece1 = MyPiece1()
        piece2 = MyPiece2()
        piece1b = MyPiece1()
        self.assertEqual(piece1.creation_counter + 1, piece2.creation_counter)
        self.assertEqual(piece2.creation_counter + 1, piece1b.creation_counter)

    def test_view_keep_pieces_ordered(self):
        self.assertEqual(MyView1.base_pieces.keys(), ['piece1', 'piece2'])
        self.assertEqual(MyView2.base_pieces.keys(), ['piece2', 'piece1'])

    def test_base_pieces(self):
        self.assertEqual(MySubView.base_pieces.keys(), ['piece3'])
        self.assertEqual(MySubView2.base_pieces.keys(), ['piece3'])

    def test_view_keep_pieces_ordered_when_subclassed(self):
        self.assertEqual(
            MySubView.pieces.keys(),
            ['piece1', 'piece2', 'piece3']
        )
        self.assertEqual(
            MySubView2.pieces.keys(),
            ['piece2', 'piece1', 'piece3']
        )

    def test_changing_the_instance_pieces_does_not_affect_the_class(self):
        view = MyView1()
        self.assertEqual(view.pieces.keys(), ['piece1', 'piece2'])
        from django.utils.datastructures import SortedDict
        view.pieces = SortedDict()
        self.assertEqual(view.pieces.keys(), [])
        self.assertEqual(MyView1.base_pieces.keys(), ['piece1', 'piece2'])

    def test_use_view_mode_by_default(self):
        piece1 = MyPiece1()
        # When the piece is part of the class
        self.assertEqual(piece1.get_mode('detail', False), 'detail')
        # When the piece in inherited
        self.assertEqual(piece1.get_mode('detail', True), 'detail')

    def test_piece_mode_takes_over_view_mode(self):
        piece1 = MyPiece1(mode='list')
        # When the piece is part of the class
        self.assertEqual(piece1.get_mode('detail', False), 'list')
        # When the piece in inherited
        self.assertEqual(piece1.get_mode('detail', True), 'list')

    def test_piece_default_mode_is_overriden_if_piece_is_not_inherited(self):
        piece1 = MyPiece1(default_mode='list')
        self.assertEqual(piece1.get_mode('detail', False), 'detail')

    def test_piece_default_mode_is_overriden_by_view_mode_if_piece_is_not_inherited(self):
        piece1 = MyPiece1(default_mode='list')
        self.assertEqual(piece1.get_mode('detail', True), 'list')


class TestJigsawTemplateRendering(TestCase):

    def setUp(self):
        self.template_strings = {
            'name': 'some_template_nam.html',
            'prefix': 'a_prefix_'
        }

    def test_template_name(self):
        template_name = self.template_strings['name']
        view = MyView1()
        view.template_name = template_name
        result = view.get_template_name()
        self.assertEqual(result, template_name)

    def test_template_name_preceed_template_prefix_or_pieces(self):
        template_name = self.template_strings['name']
        template_prefix = self.template_strings['prefix']
        view = MyView1()
        view.mode = 'list'
        view.template_name = template_name
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_name)

    def test_template_prefix(self):
        template_prefix = self.template_strings['prefix']

        view = MyView1()
        view.mode = 'list'
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'list.html')

        view = MyView1()
        view.mode = 'detail'
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'detail.html')

    def test_use_not_null_piece_template_name(self):
        view = MyView1()
        view.mode = 'list'
        self.assertEqual(
            view.get_template_name(),
            'my_piece_list.html')

        view = MyView1()
        view.mode = 'detail'
        self.assertEqual(
            view.get_template_name(),
            'my_piece_detail.html')

        view = MyView2()
        view.mode = 'list'
        self.assertEqual(
            view.get_template_name(),
            'my_piece_list.html')

    def test_basic_context(self):
        view = MyView1()
        self.assertEqual(
            view.get_context_data(None), {
                'my_piece_1': 'azerty',
        })
        view = MyView2()
        self.assertEqual(
            view.get_context_data(None), {
                'my_piece_1': 'azerty',
        })

    def test_get_context_data_can_discard_context_data(self):
        view = DiscardContextView()
        self.assertEqual(view.get_context_data(None), {})

    def test_get_context_data_can_depend_on_mode(self):
        view = ContextDependsOnModeView()
        view.mode = 'list'
        self.assertEqual(view.get_context_data(None), {
            'list': True,
            'my_piece_1': 'azerty',
        })
        view.mode = 'detail'
        self.assertEqual(view.get_context_data(None), {
            'detail': True,
            'my_piece_1': 'azerty',
        })


#
# JIGSAW VIEW TESTS
#


class JigsawViewTest(TestCase):

    fixtures = ['object_piece.json']
    urls = 'jigsawview.tests.urls'

    def test_detail_view_context(self):
        response = self.client.get('/object/1/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='obj_detail.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted(['obj', 'other_paginator', 'other_page_obj',
                'other_is_paginated', 'other_list'
            ]))
        self.assertEqual(
            response.context_data['obj'],
            MyObjectModel.objects.get(id=1)
        )
        self.assertEqual(
            [(o.id, type(o)) for o in response.context_data['other_list']],
            [(o.id, type(o)) for o in MyOtherObjectModel.objects.all()]
        )

    def test_list_view_context(self):
        response = self.client.get('/objects/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='obj_list.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted([
                'obj_paginator', 'obj_page_obj',
                'obj_is_paginated', 'obj_list',
                'other_paginator', 'other_page_obj',
                'other_is_paginated', 'other_list',
            ]))
        self.assertEqual(
            [(o.id, type(o)) for o in response.context_data['obj_list']],
            [(o.id, type(o)) for o in MyObjectModel.objects.all()]
        )
        self.assertEqual(
            [(o.id, type(o)) for o in response.context_data['other_list']],
            [(o.id, type(o)) for o in MyOtherObjectModel.objects.all()]
        )

    def test_update_view_context(self):
        response = self.client.get('/object/1/update/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='obj_update.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted([
                'obj_form', 'obj',
                'other_paginator', 'other_page_obj',
                'other_is_paginated', 'other_list',
            ]))
        self.assertEqual(
            [(o.id, type(o)) for o in response.context_data['other_list']],
            [(o.id, type(o)) for o in MyOtherObjectModel.objects.all()]
        )
        new_values = {
            'slug': 'new_slug_value',
            'other_slug_field': 'other_slug_value',
        }
        response = self.client.post('/object/1/update/', new_values)
        self.assertRedirects(response, '/object/1/',
            target_status_code=200)
        obj = MyObjectModel.objects.get(id=1)
        for k, v in new_values.items():
            self.assertEqual(getattr(obj, k), v)

    def test_new_view_context(self):
        response = self.client.get('/object/new/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='obj_new.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted([
                'obj_form',
                'other_paginator', 'other_page_obj',
                'other_is_paginated', 'other_list',
            ]))
        self.assertEqual(
            [(o.id, type(o)) for o in response.context_data['other_list']],
            [(o.id, type(o)) for o in MyOtherObjectModel.objects.all()]
        )
        new_values = {
            'slug': 'new_slug_value',
            'other_slug_field': 'other_slug_value',
        }
        response = self.client.post('/object/new/', new_values)
        self.assertRedirects(response, '/object/3/',
            target_status_code=200)
        obj = MyObjectModel.objects.get(id=3)
        for k, v in new_values.items():
            self.assertEqual(getattr(obj, k), v)

#
# OBJECT PIECE TESTS
#


class ObjectPieceTest(TestCase):

    fixtures = ['object_piece.json']

    def test_get_object_with_no_arguments_raises_an_exception(self):
        object_view = MyObjectPiece(mode='detail')
        with self.assertRaises(AttributeError):
            object_view.get_object(request=Mock(), context={})

    def test_get_object_by_pk(self):
        object_view = MyObjectPiece(mode='detail')
        obj = object_view.get_object(request=Mock(), context={}, pk='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_with_different_pk(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.pk_url_kwarg = 'obj_id'
        obj = object_view.get_object(request=Mock(), context={}, obj_id='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_slug(self):
        object_view = MyObjectPiece(mode='detail')
        obj = object_view.get_object(request=Mock(), context={}, slug='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_url_slug(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(request=Mock(), context={}, name='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_slug_field(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.slug_field = "other_slug_field"
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(request=Mock(), context={}, name='other_object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_context_data_in_detail_mode(self):
        rf = RequestFactory()
        object_view = MyObjectPiece()
        object_view.view_name = 'my_object'
        request = rf.get('object/1/')
        context = {'demo': True}
        context = object_view.get_context_data(
            request, context, 'detail', pk=1)
        self.assertEqual(len(context), 2)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object' in context)
        self.assertEqual(context['my_object'].id, 1)

    def test_get_context_data_in_list_mode(self):
        rf = RequestFactory()
        object_view = MyObjectPiece()
        object_view.view_name = 'my_object'
        request = rf.get('objects')
        context = {'demo': True}
        context = object_view.get_context_data(
            request, context, 'list')
        self.assertEqual(len(context), 5)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object_list' in context)
        self.assertEqual(len(context['my_object_list']), 2)
        self.assertTrue('my_object_is_paginated' in context)
        self.assertTrue('my_object_page_obj' in context)
        self.assertTrue('my_object_paginator' in context)

    def test_get_context_data_in_update_mode(self):
        rf = RequestFactory()
        object_view = MyObjectPiece()
        object_view.view_name = 'my_object'
        request = rf.get('object/1/update/')
        context = {'demo': True}
        context = object_view.get_context_data(
            request, context, 'update', pk=1)
        self.assertEqual(len(context), 3)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object' in context)
        self.assertEqual(context['my_object'].id, 1)
        self.assertTrue('my_object_form' in context)
        self.assertEqual(
            sorted(context['my_object_form'].fields.keys()),
            sorted(['slug', 'other_slug_field'])
        )
        self.assertEqual(
            context['my_object_form']['slug'].value(),
            'object_1')
        self.assertEqual(
            context['my_object_form']['other_slug_field'].value(),
            'other_object_1')

    def test_get_context_data_in_new_mode(self):
        rf = RequestFactory()
        object_view = MyObjectPiece()
        object_view.view_name = 'my_object'
        request = rf.get('object/new/')
        context = {'demo': True}
        context = object_view.get_context_data(
            request, context, 'new')
        self.assertEqual(len(context), 2)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object_form' in context)
        self.assertEqual(
            sorted(context['my_object_form'].fields.keys()),
            sorted(['slug', 'other_slug_field'])
        )
        self.assertEqual(
            context['my_object_form']['slug'].value(),
            None)
        self.assertEqual(
            context['my_object_form']['other_slug_field'].value(),
            None)
