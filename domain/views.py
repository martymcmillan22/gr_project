from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .constants import DOMAIN_CELL_FIELD_BY_SLUG, DOMAIN_CELLS, DOMAIN_COMPARTMENT_DEFINITIONS, DOMAIN_EDITABLE_BOARD_FIELDS, DOMAIN_EDITABLE_COMPARTMENT_FIELDS, DOMAIN_BOARD_DEFINITIONS
from .forms import DomainProfileForm
from .models import DomainProfile


def get_or_create_domain_profile(user):
	profile, _ = DomainProfile.objects.get_or_create(user=user)
	return profile


class IndexView(LoginRequiredMixin, TemplateView):
	template_name = "domain/index.html"

	def get_profile(self):
		if not hasattr(self, "_domain_profile"):
			self._domain_profile = get_or_create_domain_profile(self.request.user)
		return self._domain_profile

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		profile = self.get_profile()
		context["profile_name"] = "Personal Domain"
		context["profile"] = profile
		context["cells"] = [
			{
				"slug": definition["slug"],
				**DOMAIN_CELLS[definition["slug"]],
				"label": profile.get_compartment_label(definition["slug"]),
				"editable": definition["editable"],
			}
			for definition in DOMAIN_COMPARTMENT_DEFINITIONS
		]
		context["board_cards"] = profile.board_records()
		context["locked_compartments"] = [definition for definition in DOMAIN_COMPARTMENT_DEFINITIONS if not definition["editable"]]
		return context


class EditView(LoginRequiredMixin, TemplateView):
	template_name = "domain/edit.html"
	form_class = DomainProfileForm

	def get_profile(self):
		if not hasattr(self, "_domain_profile"):
			self._domain_profile = get_or_create_domain_profile(self.request.user)
		return self._domain_profile

	def get_form(self, data=None):
		return self.form_class(data=data, instance=self.get_profile())

	def post(self, request, *args, **kwargs):
		form = self.get_form(data=request.POST)
		if form.is_valid():
			form.save()
			return redirect("domain:edit")
		return self.render_to_response(self.get_context_data(form=form))

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		profile = self.get_profile()
		form = kwargs.get("form") or self.get_form()
		context["profile_name"] = "Personal Domain"
		context["profile"] = profile
		context["form"] = form
		context["editable_compartment_fields"] = [form[field_name] for field_name in DOMAIN_EDITABLE_COMPARTMENT_FIELDS]
		context["board_fields"] = [form[field_name] for field_name in DOMAIN_EDITABLE_BOARD_FIELDS]
		context["locked_compartments"] = [definition for definition in DOMAIN_COMPARTMENT_DEFINITIONS if not definition["editable"]]
		context["cells"] = [
			{
				"slug": definition["slug"],
				**DOMAIN_CELLS[definition["slug"]],
				"label": profile.get_compartment_label(definition["slug"]),
				"editable": definition["editable"],
			}
			for definition in DOMAIN_COMPARTMENT_DEFINITIONS
		]
		context["board_cards"] = profile.board_records()
		return context


class CellDetailView(LoginRequiredMixin, TemplateView):
	template_name = "domain/cell_detail.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		profile = get_or_create_domain_profile(self.request.user)
		slug = self.kwargs.get("slug", "").lower()
		cell = DOMAIN_CELLS.get(slug)
		if not cell:
			raise Http404("Domain cell not found")
		context["profile_name"] = "Personal Domain"
		context["namespace"] = "domain"
		context["cell"] = {
			**cell,
			"label": profile.get_compartment_label(slug),
			"slug": slug,
		}
		context["profile"] = profile
		return context
