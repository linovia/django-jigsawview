"""
Base classes for the jigsawview pieces
"""


class BasePiece(object):

    # Tracks each time a Field instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, *args, **kwargs):
        super(BasePiece, self).__init__()

        # Increase the creation counter, and save our local copy.
        self.creation_counter = BasePiece.creation_counter
        BasePiece.creation_counter += 1


class Piece(BasePiece):
    view_name = None
    template_name = None
    template_name_prefix = None
    mode = None
    base_mode = None
    default_mode = None

    def __init__(self, mode=None, default_mode=None, *args, **kwargs):
        self.base_mode = self.mode = mode
        self.default_mode = default_mode
        super(Piece, self).__init__(*args, **kwargs)

    def get_template_name(self, mode, *args, **kwargs):
        """
        Give the desired template name for this piece
        """
        if self.template_name:
            return u'%s' % self.template_name
        if self.template_name_prefix:
            return u'%s_%s' % (self.template_name_prefix, mode)
        return None

    def get_context_data(self, request, context, mode, *args, **kwargs):
        """
        Compute the view context for this piece.
        """
        return context

    def get_mode(self, mode, is_herited):
        """
        Return which mode this piece should be using
        """
        return self.mode or (is_herited and self.default_mode) or mode
