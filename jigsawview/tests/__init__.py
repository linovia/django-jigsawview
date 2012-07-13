"""
Unit tests for the jigsawview application
"""

# from unittest2 import TestCase
from django.test import TestCase


from jigsawview.pieces import Piece
from jigsawview.views import JigsawView

from jigsawview.tests.models import MyObjectModel, MyOtherObjectModel

#
# Various test Pieces and View definitions
#


class MyPiece1(Piece):
    template_name = 'my_piece_'

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
            template_name='local_tests/obj_detail.html')
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


#
# OBJECT PIECE TESTS
#


class ObjectPieceTest(TestCase):
    pass
