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
    formset_factory = None
    formset = None
    initial = {}

    fields = None
    exclude = None
    extra = 1
    can_delete = False

    def __init__(self, *args, **kwargs):
        super(ModelFormsetPiece, self).__init__(*args, **kwargs)
        if not self.formset_factory:
            self.formset_factory = modelformset_factory(self.model,
                fields=self.fields, exclude=self.exclude,
                extra=self.extra, can_delete=self.can_delete)

    def get_context_name(self):
        """
        Returns the formset context name
        """
        return self.view_name + u'_formset'

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

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

    def get_formset(self, **kwargs):
        """
        Returns an instance of the formset to be used in this view.
        """
        if not self.formset:
            formset_factory = self.formset_factory
            self.formset = formset_factory(**self.get_form_kwargs(**kwargs))
        return self.formset

    def get_form_kwargs(self, **kwargs):
        """
        Returns the keyword arguments for instanciating the form.
        """
        args = {
            'initial': self.get_initial(),
            'queryset': self.get_queryset(),
            'prefix': self.view_name,
        }
        if self.request.method in ('POST', 'PUT'):
            args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return args

    def get_context_data(self, context, **kwargs):
        context[self.get_context_name()] = self.get_formset(**kwargs)
        return context

    def formset_valid(self, formset):
        formset.save()
        return

    def formset_invalid(self, formset):
        return

    def dispatch(self, context):
        formset = self.get_formset()
        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)

    #
    # Utility function
    #

    def is_valid(self):
        return self.get_formset().is_valid()


class InlineFormsetPiece(ModelFormsetPiece):

    root_instance = None
    fk_field = None

    def get_queryset(self):
        qs = self.model.objects.none()
        if self.root_instance:
            qs = self.model.objects.filter(**{
                self.fk_field: self.root_instance
            })
        return qs

    def formset_valid(self, formset):
        objs = formset.save(commit=False)
        for obj in objs:
            setattr(obj, self.fk_field, self.root_instance)
            obj.save()
        return
