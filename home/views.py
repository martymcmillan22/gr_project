from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from datetime import datetime

class HomeView(TemplateView):
    template_name = 'index.html'
    extra_context = {'today':datetime.today()}


class ArchitectureSlidesView(TemplateView):
    template_name = "presentation/architecture_slides.html"


class ExecutiveSlidesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "presentation/executive_slides.html"
    raise_exception = True
    required_group = "executive_slides_access"

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name=self.required_group).exists()


class SlidesHubView(TemplateView):
    template_name = "presentation/slides_hub.html"


class BTSRLView(TemplateView):
    template_name = "presentation/btsrl.html"
