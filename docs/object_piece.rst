Object Piece
~~~~~~~~~~~~

This piece will expose a Django Model. That piece will morph according to the view's request.

Options :

- model : Model to use for this Piece.
- fields : Limit the modle's form fields to that list.
- exclude : List of fields to exclude from the model's form field.
- instance_name : How should our object/list be called in the template's context.

