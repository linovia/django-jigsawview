Tutorial
~~~~~~~~

The basic use case will look pretty similar to the Django generic
class based views. Let's start with a basic models::


    class Project(models.Model):
        name = models.CharField(max_length=64)
        slug = models.SlugField(max_length=64)
        members = models.ManyToManyField('auth.User', related_name='projects')


Next step, we are going to tie this models to an ObjectPiece::


    from jigsawview.pieces import ObjectPiece

    class ProjectMixin(ObjectPiece):
        model = Project
        pk_url_kwarg = 'project_id'


In order to use this piece we will create a view that use it. JigsawViews
are very similar to Models or Forms except that they'll use Pieces instead of
Fields::


    from jigsawview import JigsawView

    class ProjectView(JigsawView):
        project = ProjectMixin()


Last, we need to configure our urls::


    url(r'^projects/$',
        ProjectView.as_view(mode='list'),
        name='projects'),
    url(r'^projects/new/$',
        ProjectView.as_view(mode='new'),
        name='new-project'),
    url(r'^projects/(?P<project_id>\d+)/$',
        ProjectView.as_view(mode='detail'),
        name='project'),
    url(r'^projects/(?P<project_id>\d+)/update/$',
        ProjectView.as_view(mode='update'),
        name='update-project'),
    url(r'^projects/(?P<project_id>\d+)/delete/$',
        ProjectView.as_view(mode='delete'),
        name='delete-project'),


And now, you have all the basic views to list your projects, view, edit, create
or delete them.

There are a couple of extras that comes with JigsawViews:

- inlines formsets
- automatic filters
- chainable ObjectPieces
