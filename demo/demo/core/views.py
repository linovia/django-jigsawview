"""
Bug tracker views.
"""

from jigsawview import JigsawView
from jigsawview.pieces import ObjectPiece
from demo.core.models import Project, Milestone, Bug
from django.core.urlresolvers import reverse


class ProjectMixin(ObjectPiece):
    model = Project
    pk_url_kwarg = 'project_id'

    def get_success_url(self, obj=None):
        return reverse('projects')

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user.id)


class MilestoneMixin(ObjectPiece):
    model = Milestone
    pk_url_kwarg = 'milestone_id'

    def get_success_url(self):
        return reverse('milestones')

    def get_queryset(self):
        return Milestone.objects.filter(project=self.view.context['project'])


class BugMixin(ObjectPiece):
    model = Bug
    pk_url_kwarg = 'bug_id'

    def get_success_url(self, obj=None):
        return reverse('bugs', kwargs={'project_id': obj.project.id})

    def get_queryset(self):
        # Limits the bugs to the current project's ones
        # and possibly the milestone if we have one
        qs = Bug.objects.filter(project=self.view.context['project'])
        if 'milestone' in self.view.context:
            qs = qs.filter(milestone=self.view.context['milestone'])
        return qs


class ProjectView(JigsawView):
    project = ProjectMixin(default_mode='detail')


class MilestoneView(ProjectView):
    milestone = MilestoneMixin(default_mode='detail')


class BugView(ProjectView):
    milestones = MilestoneMixin(mode='list')
    bug = BugMixin(default_mode='detail')


class BugMilestoneView(MilestoneView):
    bug = BugMixin(default_mode='detail')
