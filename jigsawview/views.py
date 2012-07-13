"""
Base Jigsaw view.
"""

import copy

from functools import update_wrapper

from django.utils.datastructures import SortedDict
from django.utils.decorators import classonlymethod
from django.template.response import TemplateResponse

from jigsawview.pieces import Piece

# Monkey patch SortedDict to work with copy
if not hasattr(SortedDict, '__copy__'):
    SortedDict.__copy__ = SortedDict.copy


def get_declared_pieces(bases, attrs):
    """
    Create a list of pieces instance from the passed in 'attrs', plus any
    similar piece in the base classes (in 'bases').
    """
    pieces = [(piece_name, attrs.pop(piece_name))
        for piece_name, obj in attrs.items() if isinstance(obj, Piece)]
    pieces.sort(key=lambda x: x[1].creation_counter)

    # If this class is subclassing another View, add that View's pieces.
    # Note that we loop over the bases in *reverse*. This is necessary in
    # order to preserve the correct order of fields.
    for base in bases[::-1]:
        if hasattr(base, 'base_pieces'):
            pieces = base.base_pieces.items() + pieces

    return SortedDict(pieces)


class ViewMetaclass(type):
    """
    A meta class the will gather the view's pieces
    """

    def __new__(cls, name, bases, attrs):
        attrs['base_pieces'] = get_declared_pieces(bases, attrs)
        attrs['pieces'] = copy.copy(attrs['base_pieces'])
        new_class = super(ViewMetaclass, cls).__new__(cls, name, bases, attrs)
        return new_class


class BoundPiece(object):

    def __init__(self, view, piece, name):
        self.name = name,
        self.piece = piece
        self.view = view


class JigsawView(object):

    mode = None
    http_method_names = [
        'get', 'post', 'put', 'delete', 'head', 'options', 'trace'
    ]

    template_name = None
    template_name_prefix = None

    __metaclass__ = ViewMetaclass

    def __init__(self, mode=None):
        self.set_mode(mode)
        for name, piece in self.pieces.iteritems():
            piece.view_name = name

    def set_mode(self, mode):
        self.mode = mode
        for name, piece in self.pieces.iteritems():
            piece.mode = mode

    def __getitem__(self, name):
        "Returns a BoundPiece with the given name."
        try:
            field = self.pieces[name]
        except KeyError:
            raise KeyError('Key %r not found in JigsawView' % name)
        return BoundPiece(self, field, name)

    def get_template_name(self):
        """
        Returns the best matching template name.
        """
        if self.template_name:
            return u'%s' % self.template_name

        if self.template_name_prefix:
            return u'%s%s.html' % (self.template_name_prefix, self.mode)

        for piece_name, piece in reversed(self.pieces.items()):
            result = piece.get_template_name()
            if result:
                return u'%s.html' % result

        return None

    def get_context_data(self, request, **kwargs):
        """
        Returns all the aggregated contexes from the pieces.
        """
        context = {}
        for piece_name, piece in self.pieces.items():
            context = piece.get_context_data(request, context, self.mode, **kwargs)
        return context

    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(u"You tried to pass in the %s method name as a "
                                u"keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError(u"%s() received an invalid keyword %r" % (
                    cls.__name__, key))

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            return self.dispatch(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def render_to_response(self, request, context, **response_kwargs):
        """
        Returns a response with a template rendered with the given context.
        """
        return TemplateResponse(
            request=request,
            template=self.get_template_name(),
            context=context,
            **response_kwargs
        )

    def dispatch(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(request, context)
