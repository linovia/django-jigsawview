"""
Unit tests for the jigsawview application
"""

# from unittest2 import TestCase
from django.test import TestCase
from django.test import RequestFactory


from jigsawview.pieces import Piece
from jigsawview.views import JigsawView

from jigsawview.tests.models import MyObjectModel, MyOtherObjectModel
from jigsawview.tests.views import SingleObjectView, MyObjectPiece

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


class MyView3(JigsawView):
    piece1 = MyPiece1(mode='list')
    piece2 = MyPiece2()


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

    def test_view_keep_pieces_ordered_when_subclassed(self):
        self.assertEqual(
            MySubView.base_pieces.keys(),
            ['piece1', 'piece2', 'piece3']
        )
        self.assertEqual(
            MySubView2.base_pieces.keys(),
            ['piece2', 'piece1', 'piece3']
        )

    def test_changing_the_instance_pieces_does_not_affect_the_class(self):
        view = MyView1()
        self.assertEqual(view.pieces.keys(), ['piece1', 'piece2'])
        from django.utils.datastructures import SortedDict
        view.pieces = SortedDict()
        self.assertEqual(view.pieces.keys(), [])
        self.assertEqual(MyView1.base_pieces.keys(), ['piece1', 'piece2'])

    def test_view_contains_bound_pieces(self):
        view = MySubView()
        from jigsawview.views import BoundPiece
        self.assertTrue(isinstance(view['piece2'], BoundPiece))
        self.assertTrue(isinstance(view['piece3'], BoundPiece))

    def test_view_sets_piece_mode(self):
        view = MyView1()
        view.set_mode('detail')
        self.assertEqual(view.pieces['piece1'].mode, 'detail')
        view.set_mode('list')
        self.assertEqual(view.pieces['piece1'].mode, 'list')

    def test_view_sets_piece_mode_unless_piece_has_explicit_mode(self):
        view = MyView3()
        view.set_mode('detail')
        self.assertEqual(view.pieces['piece1'].mode, 'list')
        self.assertEqual(view.pieces['piece2'].mode, 'detail')
        view.set_mode('list')
        self.assertEqual(view.pieces['piece1'].mode, 'list')
        self.assertEqual(view.pieces['piece2'].mode, 'list')


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
        view.set_mode('list')
        view.template_name = template_name
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_name)

    def test_template_prefix(self):
        template_prefix = self.template_strings['prefix']

        view = MyView1()
        view.set_mode('list')
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'list.html')

        view = MyView1()
        view.set_mode('detail')
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'detail.html')

    def test_use_not_null_piece_template_name(self):
        view = MyView1()
        view.set_mode('list')
        self.assertEqual(
            view.get_template_name(),
            'my_piece_list.html')

        view = MyView1()
        view.set_mode('detail')
        self.assertEqual(
            view.get_template_name(),
            'my_piece_detail.html')

        view = MyView2()
        view.set_mode('list')
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
        view.set_mode('list')
        self.assertEqual(view.get_context_data(None), {
            'list': True,
            'my_piece_1': 'azerty',
        })
        view.set_mode('detail')
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

#
# OBJECT PIECE TESTS
#


class ObjectPieceTest(TestCase):

    fixtures = ['object_piece.json']

    def test_get_object_with_no_arguments_raises_an_exception(self):
        object_view = MyObjectPiece(mode='detail')
        with self.assertRaises(AttributeError):
            object_view.get_object()

    def test_get_object_by_pk(self):
        object_view = MyObjectPiece(mode='detail')
        obj = object_view.get_object(pk='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_with_different_pk(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.pk_url_kwarg = 'obj_id'
        obj = object_view.get_object(obj_id='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_slug(self):
        object_view = MyObjectPiece(mode='detail')
        obj = object_view.get_object(slug='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_url_slug(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(name='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_slug_field(self):
        object_view = MyObjectPiece(mode='detail')
        object_view.slug_field = "other_slug_field"
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(name='other_object_1')
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
