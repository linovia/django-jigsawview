"""
Formset Piece
"""

from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelformset_factory


from jigsawview.pieces.base import Piece


class FormsetPiece(Piece):

    pass


class ModelFormsetPiece(Piece):

    model = None
    queryset = None
    formset = None

    def __init__(self, *args, **kwargs):
        super(ModelFormsetPiece, self).__init__(*args, **kwargs)
        if not self.formset:
            self.formset = modelformset_factory(self.model)

    def get_queryset(self):
        """
        Get the queryset to look an object up against. May not be called if
        `get_object` is overridden.
        """
        if self.queryset is None:
            if self.model:
                return self.model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    u"%(cls)s is missing a queryset. Define "
                    u"%(cls)s.model, %(cls)s.queryset, or override "
                    u"%(cls)s.get_object()." % {
                        'cls': self.__class__.__name__
                    })
        return self.queryset._clone()

    def get_context_data(self, context, **kwargs):
        formset = self.formset(queryset=self.get_queryset())
        context[self.view_name + '_formset'] = formset
        return context

    def form_valid(self, form):
        return

    def form_invalid(self, form):
        return

    def dispatch(self, context):
        form_name = self.get_context_object_name() + '_form'
        form = context[form_name]
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
