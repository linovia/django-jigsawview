"""
Object related piece
"""

from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_str


from jigsawview.pieces.base import Piece


class ObjectPiece(Piece):

    model = None
    queryset = None
    slug_field = 'slug'
    context_object_name = None
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
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
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
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

    def get_slug_field(self):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.slug_field

    def get_context_object_name(self, obj):
        """
        Get the name to use for the object.
        """
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(obj, '_meta'):
            return smart_str(obj._meta.object_name.lower())
        else:
            return None

    def get_context_data(self, context, mode, **kwargs):
        context_object_name = self.get_context_object_name(self.object)
        if mode in ('detail', 'update', 'delete'):
            context[context_object_name] = self.object
        return context

    def get_template_name(self, *args, **kwargs):
        # The least-specific option is the default <app>/<model>_detail.html;
        # only use this if the object in question is a model.
        if hasattr(self.object, '_meta'):
            return "%s/%s_" % (
                self.object._meta.app_label,
                self.object._meta.object_name.lower()
            )
        elif hasattr(self, 'model') and hasattr(self.model, '_meta'):
            return "%s/%s_" % (
                self.model._meta.app_label,
                self.model._meta.object_name.lower()
            )
        return self.template_name