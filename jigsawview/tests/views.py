"""
Models for the jigsawview tests.
"""

from jigsawview.pieces import ObjectPiece, InlineFormsetPiece
from jigsawview import JigsawView

from jigsawview.tests.models import (MyObjectModel, MyOtherObjectModel,
    MyInlineModel)


class MyObjectPiece(ObjectPiece):
    model = MyObjectModel


class MyOtherObjectPiece(ObjectPiece):
    model = MyOtherObjectModel


class MyInlinePiece(InlineFormsetPiece):
    model = MyInlineModel
    fk_field = 'root_obj'


class MyRootPiece(ObjectPiece):
    model = MyObjectModel
    inlines = {
        'data': MyInlinePiece(),
    }


class ObjectView(JigsawView):
    other = MyOtherObjectPiece(mode='list')
    obj = MyObjectPiece()


class SingleObjectView(JigsawView):
    obj = MyObjectPiece()


class InlineObjectView(JigsawView):
    obj = MyRootPiece()
