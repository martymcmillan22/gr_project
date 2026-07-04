from django.contrib import admin
from django.db.models import Case, Exists, IntegerField, OuterRef, Value, When
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.html import strip_tags

from .models import Issue, NewsletterSubscriber, Story


def with_issue_readiness_flags(queryset):
	now = timezone.now()
	live_stories = Story.objects.filter(
		issue=OuterRef("pk"),
		status=Story.Status.PUBLISHED,
		publish_at__lte=now,
	)
	pip_live = live_stories.filter(feature=Story.Feature.PIP)
	base_true_live = live_stories.filter(feature=Story.Feature.BASE_TRUE)
	queryset = queryset.annotate(
		has_pip_live=Exists(pip_live),
		has_base_true_live=Exists(base_true_live),
	)
	return queryset.annotate(
		is_ready=Case(
			When(has_pip_live=True, has_base_true_live=True, then=Value(1)),
			default=Value(0),
			output_field=IntegerField(),
		),
	)


class IssueReadinessFilter(admin.SimpleListFilter):
	title = "readiness"
	parameter_name = "readiness"

	def lookups(self, request, model_admin):
		return [
			("ready", "Ready"),
			("not_ready", "Not Ready"),
		]

	def queryset(self, request, queryset):
		value = self.value()
		if value not in {"ready", "not_ready"}:
			return queryset

		flagged = with_issue_readiness_flags(queryset)
		if value == "ready":
			return flagged.filter(has_pip_live=True, has_base_true_live=True)

		return flagged.exclude(has_pip_live=True, has_base_true_live=True)


@admin.action(description="Email selected issues to active subscribers")
def send_issue_to_subscribers(modeladmin, request, queryset):
	active_subscribers = list(NewsletterSubscriber.objects.filter(is_active=True))
	if not active_subscribers:
		modeladmin.message_user(request, "No active subscribers to send email to.")
		return

	for issue in queryset:
		stories = issue.stories.published()

		for subscriber in active_subscribers:
			lines = [
				f"{issue.publication_name} - {issue.month_name} {issue.year}",
				issue.masthead_title,
				"",
				"Perpetual Infrastructure Program (PIP)",
			]

			pip_stories = stories.filter(feature=Story.Feature.PIP)
			for story in pip_stories:
				lines.append(f"- {story.headline} | By {story.byline}")
				lines.append(strip_tags(story.body)[:420])
				lines.append("")

			lines.append("Base True Information Format")
			base_true_stories = stories.filter(feature=Story.Feature.BASE_TRUE)
			for story in base_true_stories:
				lines.append(f"- {story.headline} | By {story.byline}")
				lines.append(strip_tags(story.body)[:420])
				lines.append("")

			unsubscribe_url = request.build_absolute_uri(
				reverse("baseTrue_news:unsubscribe", kwargs={"token": subscriber.unsubscribe_token})
			)
			lines.extend([
				"",
				f"Unsubscribe: {unsubscribe_url}",
			])

			send_mail(
				subject=f"{issue.publication_name}: {issue.month_name} {issue.year}",
				message="\n".join(lines),
				from_email=None,
				recipient_list=[subscriber.email],
				fail_silently=False,
			)

	modeladmin.message_user(
		request,
		f"Sent {queryset.count()} issue(s) to {len(active_subscribers)} subscribers.",
	)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
	list_display = [
		"masthead_title",
		"month",
		"year",
		"publication_name",
		"live_story_count",
		"issue_status_badge",
	]
	list_filter = ["year", "month", IssueReadinessFilter]
	search_fields = ["masthead_title", "publication_name", "tagline"]
	actions = [send_issue_to_subscribers]

	def get_queryset(self, request):
		queryset = super().get_queryset(request)
		queryset = with_issue_readiness_flags(queryset)
		if "o" not in request.GET:
			return queryset.order_by("is_ready", "-year", "-month")
		return queryset

	@admin.display(description="Live stories")
	def live_story_count(self, obj):
		return obj.stories.published().count()

	@admin.display(description="Issue status")
	def issue_status_badge(self, obj):
		now = timezone.now()
		live_stories = obj.stories.filter(status=Story.Status.PUBLISHED, publish_at__lte=now)
		has_pip = live_stories.filter(feature=Story.Feature.PIP).exists()
		has_base_true = live_stories.filter(feature=Story.Feature.BASE_TRUE).exists()

		if has_pip and has_base_true:
			return format_html(
				'<span style="background:#2d6a4f;color:#fff;padding:0.2rem 0.45rem;border-radius:0.3rem;font-weight:600;">Ready</span>'
			)

		return format_html(
			'<span style="background:#9b2226;color:#fff;padding:0.2rem 0.45rem;border-radius:0.3rem;font-weight:600;">Not Ready</span>'
		)


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
	list_display = ["headline", "feature", "status", "publish_at", "issue", "is_live"]
	list_filter = ["feature", "status", "issue__year", "issue__month"]
	search_fields = ["headline", "byline", "dek", "body"]
	list_select_related = ["issue"]
	date_hierarchy = "publish_at"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
	list_display = ["email", "is_active", "joined_at"]
	list_filter = ["is_active", "joined_at"]
	search_fields = ["email"]

# Register your models here.
