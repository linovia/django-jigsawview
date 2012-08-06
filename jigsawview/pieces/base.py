"""
Base classes for the jigsawview pieces
"""

import copy


class UnboundPiece(object):
    cls = None
    cls_kwargs = {}

    def __init__(self, cls, **kwargs):
        self.cls = cls
        self.cls_kwargs = copy.copy(kwargs)

        # Increase the creation counter, and save our local copy.
        self.creation_counter = BasePiece.creation_counter
        BasePiece.creation_counter += 1

    def __call__(self, **instance_kwargs):
        kwargs = copy.copy(self.cls_kwargs)
        kwargs.update(instance_kwargs)
        kwargs['creation_counter'] = self.creation_counter
        return self.cls(bound=True, **kwargs)


class BasePiece(object):

    # Tracks each time a Field instance is created. Used to retain order.
    creation_counter = 0

    def __new__(cls, **kwargs):
        bound = kwargs.pop('bound', False)
        if not bound:
            return UnboundPiece(cls, **kwargs)
        return super(BasePiece, cls).__new__(cls, **kwargs)

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        super(BasePiece, self).__init__()

    def add_kwargs(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)


class Piece(BasePiece):
    view_name = None
    template_name = None
    template_name_prefix = None
    mode = None
    view_mode = None
    default_mode = None
    inherited_piece = False

    def __init__(self, *args, **kwargs):
        super(Piece, self).__init__(*args, **kwargs)
        self.mode = self.mode or \
            (self.inherited_piece and self.default_mode) or \
            self.view_mode

    def get_template_name(self, *args, **kwargs):
        """
        Give the desired template name for this piece
        """
        if self.template_name:
            return u'%s' % self.template_name
        if self.template_name_prefix:
            return u'%s_%s' % (self.template_name_prefix, self.mode)
        return None

    def get_context_data(self, context, *args, **kwargs):
        """
        Compute the view context for this piece.
        """
        return context

    def dispatch(self, context):
        return
