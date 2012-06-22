Design notes
~~~~~~~~~~~~

Template rendering
==================


The template to be used in a view will match the following rules:

- if the view has a template_name property, this will be used as the template name
- if the view has a template_name_prefix, it will append the view's mode and the template_name_suffix (defaults to „.html“)
- if none of the above can be done, then we'll ask the Piece objects in reverse order if they have an idea of the template_name or template_prefix/suffix
