"""
Object related piece
"""

from __future__ import unicode_literals

import copy

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext as _
from django.forms import models as model_forms
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, InvalidPage

import django_filters

from jigsawview.pieces.base import Piece


class BaseObjectPiece(Piece):

    model = None
    queryset = None
    slug_field = 'slug'
    context_object_name = None
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

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
    # Filter hook
    #

    def get_filtered_queryset(self):
        return self.get_queryset()

    #
    # Pagination hook
    #

    def paginate_queryset(self, objs):
        return None, None, objs, False

    #
    # Generic functions
    #

    def get_context_data(self, context, **kwargs):
        mode = self.mode
        obj = None
        if mode in ('detail', 'update', 'delete'):
            obj = self.get_object(**kwargs)
            context_object_name = self.get_context_object_name(obj)
            context[context_object_name] = obj
        elif mode == 'list':
            context_object_name = self.get_context_object_name()

            # Get the filtered object list
            objs = self.get_filtered_queryset()

            # Pagination
            paginator, page, objs, is_paginated = self.paginate_queryset(objs)

            context.update({
                context_object_name + '_list': objs,
                context_object_name + '_is_paginated': is_paginated,
                context_object_name + '_paginator': paginator,
                context_object_name + '_page_obj': page,
            })

        elif mode == 'new':
            context_object_name = self.get_context_object_name()

        if mode == 'update':
            form = self.get_form(instance=obj)
            context[context_object_name + '_form'] = form
            self._form = form
            self._create_inlines(instance=obj)
        elif mode == 'new':
            form = self.get_form()
            context[context_object_name + '_form'] = form
            self._form = form
            self._create_inlines()

        for name, instance in self._inlines.items():
            context = instance.get_context_data(context, **kwargs)
        return context

    def dispatch(self, context):
        if self.mode in ('update', 'new'):
            form_name = self.get_context_object_name() + '_form'
            form = context[form_name]
            if self.is_form_valid():
                result = self.form_valid(form)
                for inline in self._inlines.values():
                    inline.dispatch(context)
                return result
            return self.form_invalid(form)
        return


class ObjectFormMixin(object):

    initial = {}
    form_class = None
    success_url = None


class FilterMixin(object):

    filters = None
    filter_class = None

    def __init__(self, *args, **kwargs):
        self._filters = None
        super(FilterMixin, self).__init__(*args, **kwargs)
        if self.filters and not self.filter_class:
            meta = type(str('Meta'), (object,), {
                    'model': self.model,
                    'fields': self.filters,
                }
            )
            self.filter_class = type(
                str('%sFilter' % self.__class__.__name__),
                (django_filters.FilterSet,), {
                'Meta': meta,
            })

    def get_filtered_queryset(self):
        if self._filters:
            return self._filters.qs
        return super(FilterMixin, self).get_filtered_queryset()

    def get_context_data(self, context, **kwargs):
        if self.filter_class:
            ctx_name = self.get_context_object_name()
            qs = self.get_queryset()
            self._filters = self.filter_class(self.request.GET, qs)
            context['%s_filters' % ctx_name] = self._filters

        return super(FilterMixin, self).get_context_data(context, **kwargs)


class PaginationMixin(object):

    allow_empty = True
    paginator_class = Paginator
    page_kwarg = 'page'
    page_all_name = 'all'
    paginate_by = None
    paginate_orphans = 0

    def paginate_queryset(self, queryset):
        """
        Paginate the queryset, if needed.
        """
        page_size = self.get_paginate_by(queryset)

        if page_size is None:
            return super(PaginationMixin, self).paginate_queryset(queryset)

        page_kwarg = self.page_kwarg
        page = self.request.GET.get(page_kwarg) or 1
        if page == self.page_all_name:
            return (None, None, queryset, False)
        paginator = self.get_paginator(
            queryset, page_size, orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty())
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise Http404(_("Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
            return (paginator, page, page.object_list, page.has_other_pages())
        except InvalidPage as e:
            raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {
                                'page_number': page_number,
                                'message': str(e)
            })

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.
        """
        return self.paginate_by

    def get_paginator(self, queryset, per_page, orphans=0,
                      allow_empty_first_page=True, **kwargs):
        """
        Return an instance of the paginator for this view.
        """
        return self.paginator_class(
            queryset, per_page, orphans=orphans,
            allow_empty_first_page=allow_empty_first_page, **kwargs)

    def get_paginate_orphans(self):
        """
        Returns the maximum number of orphans extend the last page by when
        paginating.
        """
        return self.paginate_orphans

    def get_allow_empty(self):
        """
        Returns ``True`` if the view should display empty lists, and ``False``
        if a 404 should be raised instead.
        """
        return self.allow_empty


class ObjectPiece(ObjectFormMixin, FilterMixin, PaginationMixin,
    BaseObjectPiece):

    fields = None
    exclude = None

    model_form_class = model_forms.ModelForm
    formfield_callback = None

    inlines = {}

    def __init__(self, *args, **kwargs):
        super(ObjectPiece, self).__init__(*args, **kwargs)
        self._inlines = {}
        self._kwargs = {}

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
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

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
                    "%(cls)s is missing a queryset. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_object()." % {
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
            return model_forms.modelform_factory(model,
                fields=self.fields, exclude=self.exclude,
                formfield_callback=self.formfield_callback,
                form=self.model_form_class)

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
        """
        Called when the object form is valid.
        Saves the object and set that object in the inlines.
        """
        obj = form.save()
        self.object = obj
        for inline in self._inlines.values():
            inline.root_instance = obj
        return HttpResponseRedirect(self.get_success_url(obj=obj))

    def form_invalid(self, form):
        """
        Called when the form is invalid.
        """
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
    # Inlines management
    #

    def add_kwargs(self, **kwargs):
        super(ObjectPiece, self).add_kwargs(**kwargs)
        self._kwargs = copy.copy(kwargs)

    def _create_inlines(self, instance=None):
        """
        Instanciate the inlines associated with the object.
        """
        self._inlines = {}
        for name, cls in self.inlines.items():
            self._inlines[name] = cls(
                mode=self.mode,
                view_name='%s_%s' % (self.view_name, name),
                root_instance=instance,
                **self._kwargs
            )

    def are_formsets_valid(self):
        """
        Return True if all the formsets are valid
        """
        return all([formset.is_valid() for formset in self._inlines.values()])

    #
    # Generic members
    #

    def is_form_valid(self):
        return self._form.is_valid() and self.are_formsets_valid()

    def get_template_name(self, *args, **kwargs):
        app_name = None
        if self.model:
            app_name = self.model._meta.app_label
        if hasattr(self, 'object') and self.object:
            app_name = type(self.object)._meta.app_label
        if app_name:
            return '%s/%s_%s' % (app_name, self.view_name, self.mode)
        return '%s_%s' % (self.view_name, self.mode)
