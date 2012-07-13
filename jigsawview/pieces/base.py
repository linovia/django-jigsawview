"""
Base classes for the jigsawview pieces
"""


class BasePiece(object):

    # Tracks each time a Field instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, *args, **kwargs):
        self.type = None
        super(BasePiece, self).__init__(*args, **kwargs)

        # Increase the creation counter, and save our local copy.
        self.creation_counter = BasePiece.creation_counter
        BasePiece.creation_counter += 1


class Piece(BasePiece):
    view_name = None
    template_name = None
    template_name_prefix = None
    mode = None
    base_mode = None

    def __init__(self, mode=None, *args, **kwargs):
        self.base_mode = self.mode = mode
        super(Piece, self).__init__(*args, **kwargs)

    def get_template_name(self, *args, **kwargs):
        if self.template_name:
            return u'%s' % self.template_name
        if self.template_name_prefix:
            return u'%s_%s' % (self.template_name_prefix, self.mode)
        return None

    def get_context_data(self, request, context, mode, *args, **kwargs):
        return context
