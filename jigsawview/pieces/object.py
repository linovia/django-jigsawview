"""
Object related piece
"""

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext as _
from django.forms import models as model_forms
from django.http import HttpResponseRedirect


from jigsawview.pieces.base import Piece


class ObjectPiece(Piece):

    model = None
    queryset = None
    slug_field = 'slug'
    context_object_name = None
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    initial = {}
    form_class = None
    success_url = None

    #
    # Single object management
    #

    def get_object(self, queryset=None, **kwargs):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = kwargs.get(self.pk_url_kwarg, None)
        slug = kwargs.get(self.slug_url_kwarg, None)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        elif slug is not None:
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        # If none of those are defined, it's an error.
        else:
            raise AttributeError(u"Generic detail view %s must be called with "
                                 u"either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(_(u"No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_slug_field(self):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.slug_field

    def get_context_object_name(self, obj=None):
        """
        Get the name to use for the object.
        """
        return self.view_name

    #
    # Queryset
    #

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

    #
    # Form management
    #

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

    def get_form_class(self, **kwargs):
        """
        Returns the form class to use in this view
        """
        if self.form_class:
            return self.form_class
        else:
            if self.model is not None:
                # If a model has been explicitly provided, use it
                model = self.model
            elif 'object' in kwargs and kwargs['object'] is not None:
                # If this view is operating on a single object, use
                # the class of that object
                model = kwargs['object'].__class__
            else:
                # Try to get a queryset and extract the model class
                # from that
                model = self.get_queryset().model
            return model_forms.modelform_factory(model)

    def get_form(self, **kwargs):
        """
        Returns an instance of the form to be used in this view.
        """
        form_class = self.get_form_class(**kwargs)
        return form_class(**self.get_form_kwargs(**kwargs))

    def get_form_kwargs(self, **kwargs):
        """
        Returns the keyword arguments for instanciating the form.
        """
        args = {
            'initial': self.get_initial()
        }
        if self.request.method in ('POST', 'PUT'):
            args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        if 'instance' in kwargs:
            args['instance'] = kwargs['instance']
        return args

    def form_valid(self, form):
        obj = form.save()
        return HttpResponseRedirect(self.get_success_url(obj=obj))

    def form_invalid(self, form):
        return

    def get_success_url(self, obj=None):
        if self.success_url:
            url = self.success_url
            if obj:
                url = self.success_url % obj.__dict__
        else:
            try:
                url = obj.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the Model.")
        return url

    #
    # Generic members
    #

    def get_context_data(self, context, **kwargs):
        mode = self.mode
        if mode in ('detail', 'update', 'delete'):
            obj = self.get_object(**kwargs)
            context_object_name = self.get_context_object_name(obj)
            context[context_object_name] = obj
        elif mode == 'list':
            objs = self.get_queryset()
            context_object_name = self.get_context_object_name()
            context.update({
                context_object_name + '_list': objs,
                context_object_name + '_is_paginated': False,
                context_object_name + '_paginator': None,
                context_object_name + '_page_obj': None,
            })
        elif mode == 'new':
            context_object_name = self.get_context_object_name()

        if mode == 'update':
            form = self.get_form(instance=obj)
            context[context_object_name + '_form'] = form
        elif mode == 'new':
            form = self.get_form()
            context[context_object_name + '_form'] = form
        return context

    def dispatch(self, context):
        if self.mode in ('update', 'new'):
            form_name = self.get_context_object_name() + '_form'
            form = context[form_name]
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        return

    def get_template_name(self, *args, **kwargs):
        app_name = None
        if self.model:
            app_name = self.model._meta.app_label
        if hasattr(self, 'object') and self.object:
            app_name = type(self.object)._meta.app_label
        if app_name:
            return u'%s/%s_%s' % (app_name, self.view_name, self.mode)
        return u'%s_%s' % (self.view_name, self.mode)
