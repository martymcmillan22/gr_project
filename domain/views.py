from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from center.models import CorporationItem
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
		context["matter_scope"] = "personal"
		context["profile"] = profile
		context["cells"] = [
			{
				"slug": definition["slug"],
				**DOMAIN_CELLS[definition["slug"]],
				"label": profile.get_compartment_label(definition["slug"]),
				"editable": definition["editable"],
				"display_limit": definition.get("display_limit"),
			}
			for definition in DOMAIN_COMPARTMENT_DEFINITIONS
		]
		board_cards = profile.board_records()
		context["board_cards"] = [
			{
				**board_cards[0],
				"href": f"{reverse('center:corporation_admin')}?visibility={CorporationItem.VISIBILITY_PERSONAL}",
			},
			{
				**board_cards[1],
				"href": f"{reverse('center:museum_social')}?visibility={CorporationItem.VISIBILITY_PERSONAL}",
			},
			{
				**board_cards[2],
				"href": f"{reverse('center:garden_board')}?visibility={CorporationItem.VISIBILITY_PERSONAL}",
			},
		]
		if self.request.user.subscription_tier == self.request.user.SUBSCRIPTION_PREMIUM_ENTERPRISE:
			context["board_cards"].append(
				{
					"label": "Personal Meta",
					"href": f"{reverse('center:meta_interface')}?visibility={CorporationItem.VISIBILITY_PERSONAL}",
				}
			)
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
		context["matter_scope"] = "personal"
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
				"display_limit": definition.get("display_limit"),
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
		context["matter_scope"] = "personal"
		context["namespace"] = "domain"
		context["cell"] = {
			**cell,
			"label": profile.get_compartment_label(slug),
			"slug": slug,
		}
		context["profile"] = profile
		return context
