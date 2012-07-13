"""
Models for the jigsawview tests.
"""

from jigsawview.pieces import ObjectPiece
from jigsawview import JigsawView

from jigsawview.tests.models import MyObjectModel, MyOtherObjectModel


class MyObjectPiece(ObjectPiece):
    model = MyObjectModel


class MyOtherObjectPiece(ObjectPiece):
    model = MyOtherObjectModel


class ObjectView(JigsawView):
    other = MyOtherObjectPiece(mode='list')
    obj = MyObjectPiece()


class SingleObjectView(JigsawView):
    obj = MyObjectPiece()
