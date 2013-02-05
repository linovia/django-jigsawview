
Inlines
=======

ObjectPieces eases use of objects that have a link with its model.
It is similar to the Django admin's inlines.

Example
-------

You need to start by defining the inline models::


    class EmailFormset(InlineFormsetPiece):
        model = Email
        fk_field = 'contact'
        fields = ('email', 'type')


A few notable things. You'll need to define how the inlines relates to the
parent object. This is done with the fk_field that usually will be a
ForeignKey.

Also note that you can define the fields you want to see in your inline.

Once you have those inlines defined, you'll need to include them in the
top Model and you're done::


    class PeoplePiece(ObjectPiece):
        model = People
        pk_url_kwarg = 'people_id'
        inlines = {
            'websites': WebsiteFormset(),
        }


You can then use PeoplePiece as a regular piece, it'll come with an extra
formset.

ObjectPiece.inlines is a dictionnary 