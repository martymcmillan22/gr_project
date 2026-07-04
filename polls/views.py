from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.generic.dates import MonthArchiveView, WeekArchiveView, YearArchiveView


from .models import Choice, Question, Article


def year_archive(request, year):
    a_list = Article.objects.filter(pub_date__year=year).order_by("pub_date", "id")
    context = {"year": year, "article_list": a_list}
    return render(request, "polls/archive_year.html", context)

class ArticleMonthArchiveView(MonthArchiveView):
    queryset = Article.objects.all()
    date_field = "pub_date"
    month_format = '%m'  # Uses numeric months (e.g., /05/) instead of names (/may/)
    template_name = "polls/archive_month.html"


class Year_archive_detailView(YearArchiveView):
    queryset = Article.objects.all().order_by("pub_date", "id")
    date_field = "pub_date"
    make_object_list = True
    template_name = "polls/year_archive_detailView.html"


class ArticleDetailView(generic.DetailView):
    model = Article
    template_name = "polls/article_detail.html"


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
            :5
        ]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    # same as above, no changes needed.
    ...


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))