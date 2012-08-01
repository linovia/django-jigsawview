"""
Form piece.
"""


from jigsawview.pieces.base import Piece


class FormPiece(Piece):

    form_class = None
    initial = {}

    def get_context_name(self):
        """
        Returns the form context name
        """
        return self.view_name + u'_form'

    def get_initial(self):
        """
        Returns the initial data to use for forms on this view.
        """
        return self.initial.copy()

    def get_form_class(self, **kwargs):
        """
        Returns the form class to use in this view
        """
        return self.form_class

    def get_form(self, **kwargs):
        """
        Returns an instance of the form to be used in this view.
        """
        form_class = self.get_form_class(**kwargs)
        return form_class(**self.get_form_kwargs(**kwargs))

    def get_form_kwargs(self, **kwargs):
        """
        Returns the keyword arguments for instanciating the form.
        """
        args = {
            'initial': self.get_initial()
        }
        if self.request.method in ('POST', 'PUT'):
            args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        if 'instance' in kwargs:
            args['instance'] = kwargs['instance']
        return args

    def form_valid(self, form):
        return

    def form_invalid(self, form):
        return

    def get_context_data(self, context, **kwargs):
        form = self.get_form()
        context[self.get_context_name()] = form
        return context

    def dispatch(self, context):
        form_name = self.get_context_name()
        form = context[form_name]
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
