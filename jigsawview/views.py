"""
Base Jigsaw view.
"""

import copy
from django.utils.datastructures import SortedDict

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


class JigsawView():

    __metaclass__ = ViewMetaclass

    def __getitem__(self, name):
        "Returns a BoundPiece with the given name."
        try:
            field = self.pieces[name]
        except KeyError:
            raise KeyError('Key %r not found in JigsawView' % name)
        return BoundPiece(self, field, name)
