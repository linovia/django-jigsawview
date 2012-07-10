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
    template_name = None

    def get_template_name(self):
        return self.template_name

    def get_context(self, context):
        return context
