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
    initial = {}

    fields = None
    exclude = None

    def __init__(self, *args, **kwargs):
        super(ModelFormsetPiece, self).__init__(*args, **kwargs)
        if not self.formset:
            self.formset = modelformset_factory(self.model,
                fields=self.fields, exclude=self.exclude)

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
        formset_class = self.formset
        return formset_class(**self.get_form_kwargs(**kwargs))

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
        if 'instance' in kwargs:
            args['instance'] = kwargs['instance']
        return args

    def get_context_data(self, context, **kwargs):
        context[self.get_context_name()] = self.get_formset()
        return context

    def formset_valid(self, formset):
        formset.save()
        return

    def formset_invalid(self, formset):
        return

    def dispatch(self, context):
        form_name = self.get_context_name()
        formset = context[form_name]
        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)


class InlineFormsetPiece(ModelFormsetPiece):

    root_instance = None
    fk_field = None

    def get_queryset(self):
        qs = self.model.objects.none()
        if self.root_instance in self.view.context:
            qs = self.model.objects.filter(**{
                self.fk_field: self.view.context[self.root_instance]
            })
        return qs

    def formset_valid(self, formset):
        instance = self.view.context[self.root_instance]
        objs = formset.save(commit=False)
        for obj in objs:
            setattr(obj, self.fk_field, instance)
            obj.save()
        return
