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
