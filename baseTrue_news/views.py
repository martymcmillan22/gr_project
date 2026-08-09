from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic

from .forms import NewsletterSignupForm
from .models import Issue, NewsletterSubscriber, Story


def _resolve_visibility_scope(request):
	visibility_scope = (request.GET.get("visibility") or Story.Visibility.PUBLIC).strip().lower()
	if visibility_scope not in {Story.Visibility.PUBLIC, Story.Visibility.PERSONAL}:
		return Story.Visibility.PUBLIC
	return visibility_scope


class NewsletterHomeView(generic.TemplateView):
	template_name = "baseTrue_news/index.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		visibility_scope = _resolve_visibility_scope(self.request)
		published_issues = (
			Issue.objects.filter(
				stories__status=Story.Status.PUBLISHED,
				stories__publish_at__lte=timezone.now(),
				stories__visibility=visibility_scope,
			)
			.distinct()
			.order_by("-year", "-month")
		)
		current_issue = published_issues.first()

		context["current_issue"] = current_issue
		context["recent_issues"] = published_issues[:12]
		context["pip_stories"] = Story.objects.none()
		context["base_true_stories"] = Story.objects.none()
		context["visibility_scope"] = visibility_scope

		if current_issue:
			live_stories = current_issue.stories.published().filter(visibility=visibility_scope)
			context["pip_stories"] = live_stories.filter(feature=Story.Feature.PIP)
			context["base_true_stories"] = live_stories.filter(feature=Story.Feature.BASE_TRUE)
			context["lead_story"] = live_stories.first()

		context["signup_form"] = NewsletterSignupForm()

		return context


class NewsletterSignupView(generic.View):
	success_url = reverse_lazy("baseTrue_news:index")

	def post(self, request, *args, **kwargs):
		form = NewsletterSignupForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data["email"]
			subscriber, created = form._meta.model.objects.get_or_create(
				email=email,
				defaults={"is_active": True},
			)
			if not created and not subscriber.is_active:
				subscriber.is_active = True
				subscriber.save(update_fields=["is_active"])
			messages.success(request, "You are subscribed to the monthly newsletter email list.")
		else:
			messages.error(request, "Please enter a valid email address.")

		return redirect(self.success_url)


class IssueArchiveView(generic.ListView):
	template_name = "baseTrue_news/archive.html"
	context_object_name = "issue_list"

	def get_queryset(self):
		return (
			Issue.objects.filter(
				stories__status=Story.Status.PUBLISHED,
				stories__publish_at__lte=timezone.now(),
				stories__visibility=Story.Visibility.PUBLIC,
			)
			.distinct()
			.order_by("-year", "-month")
		)


class IssueDetailView(generic.TemplateView):
	template_name = "baseTrue_news/issue_detail.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		visibility_scope = _resolve_visibility_scope(self.request)
		issue = get_object_or_404(Issue, year=self.kwargs["year"], month=self.kwargs["month"])
		live_stories = issue.stories.published().filter(visibility=visibility_scope)
		context["issue"] = issue
		context["lead_story"] = live_stories.first()
		context["pip_stories"] = live_stories.filter(feature=Story.Feature.PIP)
		context["base_true_stories"] = live_stories.filter(feature=Story.Feature.BASE_TRUE)
		context["visibility_scope"] = visibility_scope
		return context


class NewsletterUnsubscribeView(generic.TemplateView):
	template_name = "baseTrue_news/unsubscribe.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		subscriber = get_object_or_404(NewsletterSubscriber, unsubscribe_token=self.kwargs["token"])
		if subscriber.is_active:
			subscriber.is_active = False
			subscriber.save(update_fields=["is_active"])
			context["status_message"] = "You have been unsubscribed from BaseTrue Monthly emails."
		else:
			context["status_message"] = "This email is already unsubscribed."

		context["email"] = subscriber.email
		return context

# Create your views here.
