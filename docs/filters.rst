Using Filters
=============


Filters are using django-filter. You'll find more documentation on the filters
themselves at https://django-filter.readthedocs.org/en/latest/


Basic usage
-----------

ObjectPiece provides an easy way to configure filters. Let's see how this
works with the Bug model taken from the demo application::


    from django.db import models
    
    class Bug(models.Model):
        title = models.CharField(max_length=256)
        description = models.TextField(null=True, blank=True)
        project = models.ForeignKey(Project, related_name='bugs')
        milestone = models.ForeignKey(Milestone, related_name='bugs',
            blank=True, null=True)
        status = models.CharField(max_length=32, default='new')


We can now define our ObjectPiece and add filters based on price and
release_date::


    class BugPiece(ObjectPiece):
        model = Bug
        pk_url_kwarg = 'bug_id'
        filters = ['project', 'milestone']


We'll also need a template::


    <template>


You user will now see two dropboxes. One with the project list, the other with
milestones.


Advanced usage
--------------

Filters can be easily customized with a custom django-filter's FilterSet.
Imagine you defined a custom filter::


    import django_filters
    
    class BugFilter(django_filters.FilterSet):
        class Meta:
            model = Bug
            fields = ['project', 'milestone']


If you want to use that FilterSet on a BugPiece, you'll simply define the
filter_class::


    class BugPiece(ObjectPiece):
        model = Bug
        pk_url_kwarg = 'bug_id'
        filter_class = BugFilter


And you're done.

If you need an even more specific usage for filters, for example if you
want to adjust the proposed values for the filters according to the user,
then you should override the get_filter_class

For example, let's redefine our previous filter and restrict the project list
to the user's projects::


    import django_filters
    
    class BugFilter(django_filters.FilterSet):
        class Meta:
            model = Bug
            fields = ['project', 'milestone']

        def __init__(self, user, *args, **kwargs):
            self.user = user
            super(ProductFilterSet, self).__init__(*args, **kwargs)

            # Only keep projects the user has access to
            projects_qs = self.filters['project'].extra['queryset']
            projects_qs = projects_qs.filter(project_manager__user=self.user)
            self.filters['project'].extra['queryset'] = projects_qs


As you can see, we need the user to correctly filter the project list
accordingly. If we simply set the filter_class we won't get it. Therefore we
need to override the get_filter_class in our ObjectPiece::


    class BugPiece(ObjectPiece):
        model = Bug
        pk_url_kwarg = 'bug_id'

        def get_filter_class(self):
            from django.utils.functional import curry
            user = self.request.user
            return curry(ProductFilterSet, user=user)


We need to use the curry function to defer the class's instanciation. Whenever
the filter class will be instanciated, it'll use the request's user as argument
and the project list we'll get will be restricted to the user's ones.
