from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from .forms import ForumPostForm
from .models import ForumPost


def _resolve_visibility_scope(request):
    visibility_scope = (request.GET.get("visibility") or request.POST.get("visibility") or ForumPost.VISIBILITY_PUBLIC).strip().lower()
    if visibility_scope not in {ForumPost.VISIBILITY_PUBLIC, ForumPost.VISIBILITY_PERSONAL}:
        return ForumPost.VISIBILITY_PUBLIC
    return visibility_scope


FORUM_DETAILS = {
    "city": {
        "title": "City Forum",
        "subtitle": "Garden-level discussion space for city priorities, local operations, and neighborhood feedback.",
        "summary": "Use this forum to coordinate city initiatives tied to active Garden board work.",
        "forum_url_name": "forums:city",
        "back_url_name": "center:garden_board",
        "back_label": "Back to Garden",
        "is_public": False,
    },
    "state": {
        "title": "State Forum",
        "subtitle": "Museum-level forum for state-wide discussions, coordination, and communication plans.",
        "summary": "Use this forum to align state-level messaging and distribution from Museum workflows.",
        "forum_url_name": "forums:state",
        "back_url_name": "center:museum_social",
        "back_label": "Back to Museum",
        "is_public": False,
    },
    "national": {
        "title": "National Forum",
        "subtitle": "Corporation-level forum for national policy, infrastructure strategy, and protection planning.",
        "summary": "Use this forum to capture and review national priorities before downstream Museum and Garden execution.",
        "forum_url_name": "forums:national",
        "back_url_name": "center:corporation_admin",
        "back_label": "Back to Corporation",
        "is_public": False,
    },
    "global": {
        "title": "Global Forum",
        "subtitle": "Global discussion space for international collaboration across city, state, and national contexts.",
        "summary": "Use this forum to connect worldwide ideas, initiatives, and long-term coordination plans.",
        "forum_url_name": "forums:global",
        "back_url_name": "index",
        "back_label": "Back to Home",
        "is_public": True,
    },
}

SEVM_BRANCHES = [
    {"letter": "S", "subject": "Math", "format": "SACP"},
    {"letter": "E", "subject": "Language", "format": "EDNP"},
    {"letter": "V", "subject": "Arts", "format": "VLSM"},
    {"letter": "M", "subject": "Science", "format": "MBSP"},
]


class ForumContextMixin:
    forum_key = None

    def get_forum_detail(self):
        detail = FORUM_DETAILS.get(self.forum_key)
        if not detail:
            raise Http404("Forum not found")
        return detail

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum = self.get_forum_detail()
        visibility_scope = _resolve_visibility_scope(self.request)
        context["forum"] = forum
        context["forum_share_path"] = reverse("forums:access", kwargs={"forum_key": self.forum_key})
        context["sevm_branches"] = SEVM_BRANCHES
        context["posts"] = ForumPost.objects.filter(forum_type=self.forum_key, visibility=visibility_scope)
        context["visibility_scope"] = visibility_scope
        context["post_form"] = kwargs.get("post_form") or ForumPostForm()
        return context


class ForumBoardMixin(ForumContextMixin):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.forum_type = self.forum_key
            post.visibility = _resolve_visibility_scope(request)
            post.save()
            return redirect(request.path)

        context = self.get_context_data(post_form=form)
        return self.render_to_response(context)


class CityForumView(LoginRequiredMixin, ForumBoardMixin, TemplateView):
    template_name = "forums/city_forum.html"
    forum_key = "city"



class StateForumView(LoginRequiredMixin, ForumBoardMixin, TemplateView):
    template_name = "forums/state_forum.html"
    forum_key = "state"



class NationalForumView(LoginRequiredMixin, ForumBoardMixin, TemplateView):
    template_name = "forums/national_forum.html"
    forum_key = "national"



class InternationalForumView(ForumBoardMixin, TemplateView):
    template_name = "forums/global_forum.html"
    forum_key = "global"


class ForumAccessView(ForumContextMixin, TemplateView):
    template_name = "forums/access.html"

    def dispatch(self, request, *args, **kwargs):
        self.forum_key = kwargs.get("forum_key")
        self.get_forum_detail()
        return super().dispatch(request, *args, **kwargs)