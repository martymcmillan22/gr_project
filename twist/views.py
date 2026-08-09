from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView
from .models import CreativeIdea
from .forms import CreativeIdeaForm
from .serializers import CreativeIdeaSerializer
from polish.reminders import get_daily_polish_reminder


def _resolve_visibility_scope(request):
    visibility_scope = (request.GET.get('visibility') or request.POST.get('visibility') or CreativeIdea.VISIBILITY_PUBLIC).strip().lower()
    if visibility_scope not in {CreativeIdea.VISIBILITY_PUBLIC, CreativeIdea.VISIBILITY_PERSONAL}:
        return CreativeIdea.VISIBILITY_PUBLIC
    return visibility_scope


def get_user_idea_or_404(user, pk, visibility_scope=None):
    try:
        lookup = {'pk': pk, 'user': user}
        if visibility_scope in {CreativeIdea.VISIBILITY_PUBLIC, CreativeIdea.VISIBILITY_PERSONAL}:
            lookup['visibility'] = visibility_scope
        return CreativeIdea.objects.get(**lookup)
    except CreativeIdea.DoesNotExist as exc:
        raise Http404() from exc

class CreativeIdeaViewSet(viewsets.ModelViewSet):
    serializer_class = CreativeIdeaSerializer

    # This ensures users only see and modify their own ideas
    def get_queryset(self):
        visibility_scope = _resolve_visibility_scope(self.request)
        return CreativeIdea.objects.filter(user=self.request.user, visibility=visibility_scope)

    # Automatically attaches the logged-in user to the new idea
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, visibility=_resolve_visibility_scope(self.request))


class TwistEntryView(TemplateView):
    template_name = 'twist/entry.html'
    page_size = 8

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            query = self.request.GET.get('q', '').strip()
            status_filter = self.request.GET.get('status', 'all').strip() or 'all'
            ideas = CreativeIdea.objects.filter(user=self.request.user)
            visibility_scope = _resolve_visibility_scope(self.request)
            ideas = ideas.filter(visibility=visibility_scope)
            allowed_statuses = {
                CreativeIdea.STATUS_RAW,
                CreativeIdea.STATUS_SEED,
                CreativeIdea.STATUS_PROJECT,
                CreativeIdea.STATUS_BUSINESS,
            }
            if status_filter in allowed_statuses:
                ideas = ideas.filter(status=status_filter)
            if query:
                ideas = ideas.filter(Q(content__icontains=query) | Q(tags__icontains=query))

            paginator = Paginator(ideas, self.page_size)
            page_obj = paginator.get_page(self.request.GET.get('page'))

            context['form'] = kwargs.get('form') or CreativeIdeaForm()
            context['ideas'] = page_obj.object_list
            context['page_obj'] = page_obj
            context['search_query'] = query
            context['status_filter'] = status_filter
            context['status_choices'] = [('all', 'All')] + list(CreativeIdea.STATUS_CHOICES)
            context['visibility_scope'] = visibility_scope
            reminder_payload = get_daily_polish_reminder(self.request.user, source_label='Twist')
            context['show_polish_reminder_popup'] = reminder_payload['show_popup']
            context['polish_reminder_message'] = reminder_payload['message']
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')

        form = CreativeIdeaForm(request.POST)
        if form.is_valid():
            CreativeIdea.objects.create(
                user=request.user,
                content=form.cleaned_data['content'],
                tags=form.cleaned_data['tags'],
                status=form.cleaned_data['status'],
                visibility=_resolve_visibility_scope(request),
            )
            messages.success(request, 'Idea saved to Twist.')
            return redirect('twist-entry')

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class TwistTokenView(LoginRequiredMixin, TemplateView):
    template_name = 'twist/token.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token, _ = Token.objects.get_or_create(user=self.request.user)
        context['api_token'] = token.key
        return context


class TwistIdeaEditView(LoginRequiredMixin, TemplateView):
    template_name = 'twist/edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        idea = get_user_idea_or_404(self.request.user, self.kwargs['pk'])
        context['idea'] = idea
        context['form'] = kwargs.get('form') or CreativeIdeaForm(
            initial={'content': idea.content, 'tags': idea.tags, 'status': idea.status}
        )
        context['visibility_scope'] = idea.visibility
        return context

    def post(self, request, *args, **kwargs):
        visibility_scope = _resolve_visibility_scope(request)
        idea = get_user_idea_or_404(request.user, self.kwargs['pk'], visibility_scope=visibility_scope)
        form = CreativeIdeaForm(request.POST)
        if form.is_valid():
            idea.content = form.cleaned_data['content']
            idea.tags = form.cleaned_data['tags']
            idea.status = form.cleaned_data['status']
            idea.visibility = visibility_scope
            idea.save(update_fields=['content', 'tags', 'status', 'visibility'])
            messages.success(request, 'Idea updated.')
            return redirect('twist-entry')

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class TwistIdeaDeleteView(LoginRequiredMixin, TemplateView):
    template_name = 'twist/delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['idea'] = get_user_idea_or_404(self.request.user, self.kwargs['pk'], visibility_scope=_resolve_visibility_scope(self.request))
        return context

    def post(self, request, *args, **kwargs):
        idea = get_user_idea_or_404(request.user, self.kwargs['pk'], visibility_scope=_resolve_visibility_scope(request))
        idea.delete()
        messages.success(request, 'Idea deleted.')
        return redirect('twist-entry')