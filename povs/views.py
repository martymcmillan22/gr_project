from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, TemplateView, View

from .forms import ExpoFactForm, FirstPersonForm, NarrativeForm, PredictionForm, ProbableOutcomeForm
from .models import ExpoFact, POVResponse


class PovsHomeView(LoginRequiredMixin, ListView):
    model = ExpoFact
    template_name = 'povs/index.html'
    context_object_name = 'expo_facts'

    def get_queryset(self):
        return ExpoFact.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expo_facts = context['expo_facts']
        user_responses = {
            r.expo_fact_id: r
            for r in POVResponse.objects.filter(
                user=self.request.user,
                expo_fact__in=expo_facts,
            )
        }
        my_facts = [f for f in expo_facts if f.created_by_id == self.request.user.pk]
        community_facts = [f for f in expo_facts if f.created_by_id != self.request.user.pk]
        context['my_fact_rows'] = [(f, user_responses.get(f.pk)) for f in my_facts]
        context['community_fact_rows'] = [(f, user_responses.get(f.pk)) for f in community_facts]
        return context


class ExpoFactDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'povs/detail.html'

    def _get_expo_and_pov(self):
        expo_fact = get_object_or_404(ExpoFact, pk=self.kwargs['pk'], is_active=True)
        pov, _ = POVResponse.objects.get_or_create(
            user=self.request.user, expo_fact=expo_fact
        )
        return expo_fact, pov

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expo_fact, pov = self._get_expo_and_pov()
        context['expo_fact'] = expo_fact
        context['pov'] = pov

        if 'first_person_form' not in context:
            context['first_person_form'] = FirstPersonForm(
                initial={'first_person': pov.first_person}
            )
        if pov.can_predict and 'prediction_form' not in context:
            context['prediction_form'] = PredictionForm(
                initial={'prediction': pov.prediction}
            )
        if pov.can_narrate and 'narrative_form' not in context:
            context['narrative_form'] = NarrativeForm(
                initial={'narrative': pov.narrative}
            )
        if pov.can_add_outcome and 'probable_outcome_form' not in context:
            context['probable_outcome_form'] = ProbableOutcomeForm(
                initial={'probable_outcome': pov.probable_outcome}
            )
        return context

    def post(self, request, *args, **kwargs):
        expo_fact, pov = self._get_expo_and_pov()
        stage = request.POST.get('stage', '')

        if stage == 'first_person':
            form = FirstPersonForm(request.POST)
            if form.is_valid():
                pov.first_person = form.cleaned_data['first_person']
                if not pov.first_person_at:
                    pov.first_person_at = timezone.now()
                pov.save()
                messages.success(request, 'First person description saved.')
                return redirect('povs-detail', pk=expo_fact.pk)
            return self.render_to_response(self.get_context_data(first_person_form=form))

        elif stage == 'prediction':
            if not pov.can_predict:
                messages.error(request, 'Complete your first person description first.')
                return redirect('povs-detail', pk=expo_fact.pk)
            form = PredictionForm(request.POST)
            if form.is_valid():
                pov.prediction = form.cleaned_data['prediction']
                if not pov.prediction_at:
                    pov.prediction_at = timezone.now()
                pov.save()
                messages.success(request, 'Prediction saved.')
                return redirect('povs-detail', pk=expo_fact.pk)
            return self.render_to_response(self.get_context_data(prediction_form=form))

        elif stage == 'narrative':
            if not pov.can_narrate:
                messages.error(request, 'Complete your prediction first.')
                return redirect('povs-detail', pk=expo_fact.pk)
            form = NarrativeForm(request.POST)
            if form.is_valid():
                pov.narrative = form.cleaned_data['narrative']
                if not pov.narrative_at:
                    pov.narrative_at = timezone.now()
                pov.save()
                messages.success(request, 'Narrative saved.')
                return redirect('povs-detail', pk=expo_fact.pk)
            return self.render_to_response(self.get_context_data(narrative_form=form))

        elif stage == 'probable_outcome':
            if not pov.can_add_outcome:
                messages.error(request, 'Create your publicist narrative first.')
                return redirect('povs-detail', pk=expo_fact.pk)
            form = ProbableOutcomeForm(request.POST)
            if form.is_valid():
                pov.probable_outcome = form.cleaned_data['probable_outcome']
                if not pov.probable_outcome_at:
                    pov.probable_outcome_at = timezone.now()
                pov.save()
                messages.success(request, 'Probable outcome saved.')
                return redirect('povs-detail', pk=expo_fact.pk)
            return self.render_to_response(self.get_context_data(probable_outcome_form=form))

        return redirect('povs-detail', pk=expo_fact.pk)


class CreateExpoFactView(LoginRequiredMixin, View):
    def get(self, request):
        from django.shortcuts import render
        return render(request, 'povs/create.html', {'form': ExpoFactForm()})

    def post(self, request):
        from django.shortcuts import render
        form = ExpoFactForm(request.POST)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.created_by = request.user
            fact.is_active = True
            fact.save()
            messages.success(request, 'Your POV set was created. Start your response below.')
            return redirect('povs-detail', pk=fact.pk)
        return render(request, 'povs/create.html', {'form': form})


class EditExpoFactView(LoginRequiredMixin, View):
    def _get_own_fact(self, request, pk):
        try:
            return ExpoFact.objects.get(pk=pk, created_by=request.user)
        except ExpoFact.DoesNotExist:
            raise Http404()

    def get(self, request, pk):
        from django.shortcuts import render
        fact = self._get_own_fact(request, pk)
        return render(request, 'povs/create.html', {'form': ExpoFactForm(instance=fact), 'fact': fact, 'editing': True})

    def post(self, request, pk):
        from django.shortcuts import render
        fact = self._get_own_fact(request, pk)
        form = ExpoFactForm(request.POST, instance=fact)
        if form.is_valid():
            form.save()
            messages.success(request, 'POV set updated.')
            return redirect('povs-detail', pk=fact.pk)
        return render(request, 'povs/create.html', {'form': form, 'fact': fact, 'editing': True})
