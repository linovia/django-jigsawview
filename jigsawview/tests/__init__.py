"""
Unit tests for the jigsawview application
"""
from __future__ import unicode_literals

import six

from mock import Mock

from django.test import TestCase
from django.test import RequestFactory

from django import forms


from jigsawview.pieces import Piece, FormPiece, ModelFormsetPiece
from jigsawview.views import JigsawView

from jigsawview.tests.models import MyObjectModel, MyOtherObjectModel
from jigsawview.tests.views import MyObjectPiece, MyRootPiece, FilterPiece
from jigsawview.tests.views import ObjectView

#
# Various test Pieces and View definitions
#


class MyPiece1(Piece):
    template_name_prefix = 'my_piece'

    def get_context_data(self, context, *args, **kwargs):
        context['my_piece_1'] = 'azerty'
        return context


class MyPiece2(Piece):
    pass


class DiscardContextPiece(Piece):
    def get_context_data(self, context, *args, **kwargs):
        return {}


class ContextDependsOnModePiece(Piece):
    def get_context_data(self, context, *args, **kwargs):
        context.update({
            self.mode: True,
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
        self.assertEqual(list(MyView1.base_pieces.keys()), ['piece1', 'piece2'])
        self.assertEqual(list(MyView2.base_pieces.keys()), ['piece2', 'piece1'])

    def test_base_pieces(self):
        self.assertEqual(list(MySubView.base_pieces.keys()), ['piece3'])
        self.assertEqual(list(MySubView2.base_pieces.keys()), ['piece3'])

    def test_view_keep_pieces_ordered_when_subclassed(self):
        self.assertEqual(
            list(MySubView.pieces.keys()),
            ['piece1', 'piece2', 'piece3']
        )
        self.assertEqual(
            list(MySubView2.pieces.keys()),
            ['piece2', 'piece1', 'piece3']
        )

    def test_changing_the_instance_pieces_does_not_affect_the_class(self):
        view = MyView1(mode='detail')
        self.assertEqual(list(view.pieces.keys()), ['piece1', 'piece2'])
        from django.utils.datastructures import SortedDict
        view.pieces = SortedDict()
        self.assertEqual(list(view.pieces.keys()), [])
        self.assertEqual(list(MyView1.base_pieces.keys()), ['piece1', 'piece2'])

    def test_use_view_mode_by_default(self):
        # When the piece is part of the class
        piece1 = MyPiece1(bound=True, view_mode='detail', inherited_piece=False)
        self.assertEqual(piece1.mode, 'detail')
        # When the piece in inherited
        piece1 = MyPiece1(bound=True, view_mode='detail', inherited_piece=True)
        self.assertEqual(piece1.mode, 'detail')

    def test_piece_mode_takes_over_view_mode(self):
        # When the piece is part of the class
        piece1 = MyPiece1(bound=True, mode='list', view_mode='detail', inherited_piece=False)
        self.assertEqual(piece1.mode, 'list')
        # When the piece in inherited
        piece1 = MyPiece1(bound=True, mode='list', view_mode='detail', inherited_piece=True)
        self.assertEqual(piece1.mode, 'list')

    def test_piece_default_mode_is_overriden_if_piece_is_not_inherited(self):
        piece1 = MyPiece1(bound=True, default_mode='list', view_mode='detail', inherited_piece=False)
        self.assertEqual(piece1.mode, 'detail')

    def test_piece_default_mode_is_overriden_by_view_mode_if_piece_is_not_inherited(self):
        piece1 = MyPiece1(bound=True, default_mode='list', view_mode='detail', inherited_piece=True)
        self.assertEqual(piece1.mode, 'list')


class TestJigsawTemplateRendering(TestCase):

    def setUp(self):
        self.template_strings = {
            'name': 'some_template_nam.html',
            'prefix': 'a_prefix_'
        }

    def test_template_name(self):
        template_name = self.template_strings['name']
        view = MyView1(mode='detail')
        view.template_name = template_name
        result = view.get_template_name()
        self.assertEqual(result, template_name)

    def test_template_name_preceed_template_prefix_or_pieces(self):
        template_name = self.template_strings['name']
        template_prefix = self.template_strings['prefix']
        view = MyView1(mode='list')
        view.template_name = template_name
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_name)

    def test_template_prefix(self):
        template_prefix = self.template_strings['prefix']

        view = MyView1(mode='list')
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'list.html')

        view = MyView1(mode='detail')
        view.template_name_prefix = template_prefix
        result = view.get_template_name()
        self.assertEqual(result, template_prefix + 'detail.html')

    def test_use_not_null_piece_template_name(self):
        view = MyView1(mode='list')
        self.assertEqual(
            view.get_template_name(),
            'my_piece_list.html')

        view = MyView1(mode='detail')
        self.assertEqual(
            view.get_template_name(),
            'my_piece_detail.html')

        view = MyView2(mode='list')
        self.assertEqual(
            view.get_template_name(),
            'my_piece_list.html')

    def test_basic_context(self):
        view = MyView1(mode='detail')
        self.assertEqual(
            view.get_context_data({}), {
                'my_piece_1': 'azerty',
        })
        view = MyView2(mode='detail')
        self.assertEqual(
            view.get_context_data({}), {
                'my_piece_1': 'azerty',
        })

    def test_get_context_data_can_discard_context_data(self):
        view = DiscardContextView(mode='detail')
        self.assertEqual(view.get_context_data({}), {})

    def test_get_context_data_can_depend_on_mode(self):
        view = ContextDependsOnModeView(mode='list')
        self.assertEqual(view.get_context_data({}), {
            'list': True,
            'my_piece_1': 'azerty',
        })
        view = ContextDependsOnModeView(mode='detail')
        self.assertEqual(view.get_context_data({}), {
            'detail': True,
            'my_piece_1': 'azerty',
        })


#
# JIGSAW VIEW TESTS
#


class JigsawViewTest(TestCase):

    fixtures = ['object_piece.json']
    urls = 'jigsawview.tests.urls'

    def test_make_sure_set_mode_is_called_on_pieces(self):
        view = ObjectView(mode='new')
        self.assertEqual(view.obj.mode, 'new')
        self.assertEqual(view.other.mode, 'list')

    def test_detail_view_context(self):
        response = self.client.get('/object/1/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='tests/obj_detail.html')
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
            template_name='tests/obj_list.html')
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
            template_name='tests/obj_update.html')
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

    def test_failing_update_view_context(self):
        response = self.client.get('/object/1/update/')
        new_values = {
            'slug': 'new_slug_value',
        }
        response = self.client.post('/object/1/update/', new_values)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='tests/obj_update.html')
        self.assertFormError(response, 'obj_form', 'other_slug_field', 'This field is required.')

    def test_new_view(self):
        response = self.client.get('/object/new/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='tests/obj_new.html')
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

    def test_new_view_with_inline(self):
        response = self.client.get('/inlines/new/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='tests/obj_new.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted(['obj_form', 'obj_data_formset']))
        new_values = {
            'slug': 'new_slug_value',
            'other_slug_field': 'other_slug_value',
            'obj_data-TOTAL_FORMS': '1',
            'obj_data-INITIAL_FORMS': '0',
            'obj_data-MAX_NUM_FORMS': '',
            'obj_data-0-my_data': 'qwerty',
            'obj_data-0-id': '',
        }
        response = self.client.post('/inlines/new/', new_values)
        self.assertRedirects(response, '/object/3/',
            target_status_code=200)
        obj = MyObjectModel.objects.get(id=3)
        for key in ('slug', 'other_slug_field'):
            value = new_values[key]
            self.assertEqual(getattr(obj, key), value)
        self.assertEqual(obj.myinlinemodel_set.count(), 1)

    def test_update_view_with_inline(self):
        response = self.client.get('/inlines/1/update/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response=response,
            template_name='tests/obj_update.html')
        self.assertEqual(
            sorted(response.context_data.keys()),
            sorted(['obj', 'obj_form', 'obj_data_formset']))
        inline = response.context_data['obj_data_formset']
        self.assertEqual(len(inline), 2)
        self.assertEqual(inline[0]['my_data'].value(), 'azerty')

        new_values = {
            'slug': 'new_slug_value',
            'other_slug_field': 'other_slug_value',
            'obj_data-TOTAL_FORMS': '2',
            'obj_data-INITIAL_FORMS': '1',
            'obj_data-MAX_NUM_FORMS': '',
            'obj_data-0-my_data': 'qwerty',
            'obj_data-0-id': '1',
        }
        response = self.client.post('/inlines/1/update/', new_values)
        self.assertRedirects(response, '/object/1/',
            target_status_code=200)
        obj = MyObjectModel.objects.get(id=1)
        for key in ('slug', 'other_slug_field'):
            value = new_values[key]
            self.assertEqual(getattr(obj, key), value)
        self.assertEqual(obj.myinlinemodel_set.count(), 1)
        self.assertEqual(obj.myinlinemodel_set.all()[0].my_data, 'qwerty')

#
# OBJECT PIECE TESTS
#


class ObjectPieceTest(TestCase):

    fixtures = ['object_piece.json']

    def test_get_object_with_no_arguments_raises_an_exception(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        with self.assertRaises(AttributeError):
            object_view.get_object(request=Mock(), context={})

    def test_get_object_by_pk(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        obj = object_view.get_object(request=Mock(), context={}, pk='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_with_different_pk(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        object_view.pk_url_kwarg = 'obj_id'
        obj = object_view.get_object(request=Mock(), context={}, obj_id='1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_slug(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        obj = object_view.get_object(request=Mock(), context={}, slug='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_url_slug(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(request=Mock(), context={}, name='object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_object_by_custom_slug_field(self):
        object_view = MyObjectPiece(bound=True, mode='detail')
        object_view.slug_field = "other_slug_field"
        object_view.slug_url_kwarg = "name"
        obj = object_view.get_object(request=Mock(), context={}, name='other_object_1')
        self.assertTrue(isinstance(obj, MyObjectModel))
        self.assertEqual(obj.id, 1)

    def test_get_context_data_in_detail_mode(self):
        rf = RequestFactory()
        object_piece = MyObjectPiece(bound=True, mode='detail')
        object_piece.view_name = 'my_object'
        object_piece.add_kwargs(request=rf.get('object/1/'))
        context = {'demo': True}
        context = object_piece.get_context_data(context, pk=1)
        self.assertEqual(len(context), 2)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object' in context)
        self.assertEqual(context['my_object'].id, 1)

    def test_get_context_data_in_list_mode(self):
        rf = RequestFactory()
        object_piece = MyObjectPiece(bound=True, mode='list')
        object_piece.view_name = 'my_object'
        object_piece.add_kwargs(request=rf.get('objects'))
        context = {'demo': True}
        context = object_piece.get_context_data(context)
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
        object_piece = MyObjectPiece(bound=True, mode='update')
        object_piece.view_name = 'my_object'
        object_piece.add_kwargs(request=rf.get('object/1/update/'))
        context = {'demo': True}
        context = object_piece.get_context_data(context, pk=1)
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
        object_piece = MyObjectPiece(bound=True, mode='new')
        object_piece.view_name = 'my_object'
        object_piece.add_kwargs(request=rf.get('object/new/'))
        context = {'demo': True}
        context = object_piece.get_context_data(context)
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


class ObjectPieceWithInlinesTest(TestCase):

    fixtures = ['object_piece.json']

    def test_get_context_with_inlines_in_new_mode(self):
        rf = RequestFactory()
        object_piece = MyRootPiece(bound=True, mode='new')
        object_piece.view_name = 'root'
        object_piece.add_kwargs(request=rf.get('object/new/'))
        context = {'demo': True}
        context = object_piece.get_context_data(context)
        self.assertEqual(len(context), 3)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the root object form
        self.assertEqual(object_piece._inlines['data'].mode, 'new')
        self.assertTrue('root_form' in context)
        self.assertEqual(
            sorted(context['root_form'].fields.keys()),
            sorted(['slug', 'other_slug_field'])
        )
        # Test the inline form
        self.assertTrue('root_data_formset' in context)
        inline = context['root_data_formset']
        from django.forms.models import BaseModelFormSet
        self.assertTrue(isinstance(inline, BaseModelFormSet))
        # Make sure the FK isn't part of the formset
        self.assertFalse('root_obj' in inline[0].fields.keys())
        self.assertTrue('my_data' in inline[0].fields.keys())

    def test_get_context_with_inlines_in_update_mode(self):
        rf = RequestFactory()
        object_piece = MyRootPiece(bound=True, mode='update')
        object_piece.view_name = 'root'
        object_piece.add_kwargs(request=rf.get('object/1/update/'))
        context = {'demo': True}
        context = object_piece.get_context_data(context, pk=1)
        self.assertEqual(len(context), 4)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the root object form
        self.assertTrue('root_form' in context)
        self.assertEqual(
            sorted(context['root_form'].fields.keys()),
            sorted(['slug', 'other_slug_field'])
        )
        # Test the inline form
        self.assertEqual(object_piece._inlines['data'].mode, 'update')
        self.assertTrue(object_piece._inlines['data'].root_instance)
        self.assertTrue('root_data_formset' in context)
        inline = context['root_data_formset']
        from django.forms.models import BaseModelFormSet
        self.assertTrue(isinstance(inline, BaseModelFormSet))
        self.assertEqual(
            sorted(inline[0].fields.keys()),
            sorted(['my_data', 'id'])
        )
        self.assertEqual(len(inline), 2)
        self.assertEqual(
            inline[0]['id'].value(),
            1)
        self.assertEqual(
            inline[0]['my_data'].value(),
            'azerty')


#
# FORM PIECE TESTS
#

class TestForm(forms.Form):
    name = forms.CharField(max_length=32)
    description = forms.CharField(max_length=32)


class MyFormPiece(FormPiece):
    form_class = TestForm

    def __init__(self, *args, **kwargs):
        super(MyFormPiece, self).__init__(*args, **kwargs)
        self.form_is_valid = False
        self.form_is_invalid = False

    def form_valid(self, form):
        self.form_is_valid = True

    def form_invalid(self, form):
        self.form_is_invalid = True


class FormPieceTest(TestCase):

    def test_form_in_context(self):
        rf = RequestFactory()
        form_piece = MyFormPiece(bound=True, mode='detail')
        form_piece.view_name = 'login'
        form_piece.add_kwargs(request=rf.get('login/'))
        context = form_piece.get_context_data({'demo': True})
        self.assertEqual(len(context), 2)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the form is here
        self.assertTrue('login_form' in context)
        self.assertTrue(isinstance(context['login_form'], forms.Form))

    def test_valid_form(self):
        rf = RequestFactory()
        form_piece = MyFormPiece(bound=True, mode='detail')
        form_piece.view_name = 'login'
        form_piece.add_kwargs(request=rf.post('login/', {
            'name': 'Xavier Ordoquy',
            'description': 'Django and Python developer',
        }))
        context = form_piece.get_context_data({'demo': True})
        form_piece.dispatch(context)
        self.assertTrue(form_piece.form_is_valid)
        self.assertFalse(form_piece.form_is_invalid)

    def test_invalid_form(self):
        rf = RequestFactory()
        form_piece = MyFormPiece(bound=True, mode='detail')
        form_piece.view_name = 'login'
        form_piece.add_kwargs(request=rf.post('login/', {
            'name': 'Xavier Ordoquy',
        }))
        context = form_piece.get_context_data({'demo': True})
        form_piece.dispatch(context)
        self.assertFalse(form_piece.form_is_valid)
        self.assertTrue(form_piece.form_is_invalid)
        self.assertEqual(context['login_form'].errors, {
            'description': ['This field is required.'],
        })


#
# FORMSET TESTS
#


class MyFormsetPiece(ModelFormsetPiece):
    model = MyObjectModel

    def __init__(self, *args, **kwargs):
        super(MyFormsetPiece, self).__init__(*args, **kwargs)
        self.formset_is_valid = False
        self.formset_is_invalid = False

    def formset_valid(self, formset):
        self.formset_is_valid = True
        super(MyFormsetPiece, self).formset_valid(formset)

    def formset_invalid(self, formset):
        self.formset_is_invalid = True
        super(MyFormsetPiece, self).formset_invalid(formset)


class ModelFormsetPieceTest(TestCase):

    fixtures = ['object_piece.json']

    def test_formset_in_context(self):
        rf = RequestFactory()
        formset_piece = MyFormsetPiece(bound=True, mode='new')
        formset_piece.view_name = 'bugs'
        formset_piece.add_kwargs(request=rf.get('demo/'))
        context = formset_piece.get_context_data({'demo': True})
        self.assertEqual(len(context), 2)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the form is here
        self.assertTrue('bugs_formset' in context)
        formset = context['bugs_formset']
        from django.forms.models import BaseModelFormSet
        self.assertTrue(isinstance(formset, BaseModelFormSet))
        self.assertEqual(formset.total_form_count(), 3)  # 2 instances + 1 empty

    def test_valid_formset(self):
        rf = RequestFactory()
        self.assertEqual(len(MyObjectModel.objects.all()), 2)
        formset_piece = MyFormsetPiece(bound=True, mode='new')
        formset_piece.view_name = 'bugs'
        formset_piece.add_kwargs(request=rf.post('demo/', {
            'bugs-TOTAL_FORMS': '3',
            'bugs-INITIAL_FORMS': '2',
            'bugs-0-slug': 'object_1',
            'bugs-0-other_slug_field': 'other_object_1',
            'bugs-0-id': '1',
            'bugs-1-slug': 'modified_2',
            'bugs-1-other_slug_field': 'other_modified_2',
            'bugs-1-id': '2',
            'bugs-2-slug': 'object_3',
            'bugs-2-other_slug_field': 'other_object_3',
        }))
        context = formset_piece.get_context_data({'demo': True})
        formset_piece.dispatch(context)

        self.assertTrue(formset_piece.formset_is_valid)
        self.assertFalse(formset_piece.formset_is_invalid)

        self.assertEqual(len(MyObjectModel.objects.all()), 3)
        objs = MyObjectModel.objects.all().order_by('id')
        self.assertEqual(objs[0].slug, 'object_1')
        self.assertEqual(objs[0].other_slug_field, 'other_object_1')
        self.assertEqual(objs[1].slug, 'modified_2')
        self.assertEqual(objs[1].other_slug_field, 'other_modified_2')
        self.assertEqual(objs[2].slug, 'object_3')
        self.assertEqual(objs[2].other_slug_field, 'other_object_3')

    def test_invalid_formset(self):
        rf = RequestFactory()
        self.assertEqual(len(MyObjectModel.objects.all()), 2)
        formset_piece = MyFormsetPiece(bound=True, mode='new')
        formset_piece.view_name = 'bugs'
        formset_piece.add_kwargs(request=rf.post('demo/', {
            'bugs-TOTAL_FORMS': '3',
            'bugs-INITIAL_FORMS': '2',
            'bugs-0-slug': 'object_1',
            'bugs-0-other_slug_field': 'other_object_1',
            'bugs-0-id': '1',
            'bugs-1-slug': 'modified_2',
            'bugs-1-other_slug_field': '',
            'bugs-1-id': '2',
            'bugs-2-slug': '',
            'bugs-2-other_slug_field': 'other_object_3',
        }))
        context = formset_piece.get_context_data({'demo': True})
        formset_piece.dispatch(context)

        self.assertFalse(formset_piece.formset_is_valid)
        self.assertTrue(formset_piece.formset_is_invalid)

        self.assertEqual(len(MyObjectModel.objects.all()), 2)
        objs = MyObjectModel.objects.all().order_by('id')
        self.assertEqual(objs[0].slug, 'object_1')
        self.assertEqual(objs[0].other_slug_field, 'other_object_1')
        self.assertEqual(objs[1].slug, 'object_2')
        self.assertEqual(objs[1].other_slug_field, 'other_object_2')

        formset = context['bugs_formset']
        self.assertEqual(formset[0].errors, {})
        self.assertEqual(formset[1].errors, {
            'other_slug_field': ['This field is required.'],
        })
        self.assertEqual(formset[2].errors, {
            'slug': ['This field is required.'],
        })


class FiltersTest(TestCase):

    fixtures = ['object_piece.json']

    def test_filters_are_in_context(self):
        rf = RequestFactory()
        object_piece = FilterPiece(bound=True, mode='list')
        object_piece.view_name = 'my_object'
        object_piece.add_kwargs(request=rf.get('objects'))
        context = {'demo': True}
        context = object_piece.get_context_data(context)
        self.assertEqual(len(context), 6)
        # Test the previous context wasn't discarded
        self.assertTrue('demo' in context)
        self.assertEqual(context['demo'], True)
        # Test the context addition
        self.assertTrue('my_object_list' in context)
        self.assertEqual(len(context['my_object_list']), 2)
        self.assertTrue('my_object_is_paginated' in context)
        self.assertTrue('my_object_page_obj' in context)
        self.assertTrue('my_object_paginator' in context)
        self.assertTrue('my_object_filters' in context)
        self.assertTrue(context['my_object_filters'])
        # TODO: tester les valeurs du filtre
        self.assertTrue('slug' in context['my_object_filters'].filters)
        self.assertTrue(context['my_object_filters'].filters['slug'])
