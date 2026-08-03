from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import os
from pathlib import Path
from django.views.generic import TemplateView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from platform_core.backend import BaseView

from .models import HomepageAction, HomepageBackendItem, HomepageFlow, HomepagePreference, HomepageTask
from .permissions import HomepageBackendItemPermissions
from .serializers import (
    HomepageActionSerializer,
    HomepageBackendItemSerializer,
    HomepageFlowSerializer,
    HomepagePreferenceSerializer,
    HomepageTaskSerializer,
)


class HomepageBackendItemViewSet(BaseView):
    queryset = HomepageBackendItem.objects.all()
    serializer_class = HomepageBackendItemSerializer
    permission_classes = BaseView.permission_classes + [HomepageBackendItemPermissions]


class HomepageTaskViewSet(BaseView):
    queryset = HomepageTask.objects.all()
    serializer_class = HomepageTaskSerializer
    permission_classes = BaseView.permission_classes + [HomepageBackendItemPermissions]


class HomepageFlowViewSet(BaseView):
    queryset = HomepageFlow.objects.all()
    serializer_class = HomepageFlowSerializer
    permission_classes = BaseView.permission_classes + [HomepageBackendItemPermissions]


class HomepagePreferenceViewSet(BaseView):
    queryset = HomepagePreference.objects.all()
    serializer_class = HomepagePreferenceSerializer
    permission_classes = BaseView.permission_classes + [HomepageBackendItemPermissions]


class HomepageActionViewSet(BaseView):
    queryset = HomepageAction.objects.all()
    serializer_class = HomepageActionSerializer
    permission_classes = BaseView.permission_classes + [HomepageBackendItemPermissions]


class HomepageOverviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_flow = HomepageFlow.objects.filter(owner=request.user).order_by("-updated_at").first()
        preferences = HomepagePreference.objects.filter(owner=request.user).order_by("-updated_at").first()
        tasks = HomepageTask.objects.filter(owner=request.user).order_by("status", "-updated_at")[:10]

        return Response(
            {
                "welcome": "Your daily overview",
                "flow": HomepageFlowSerializer(latest_flow).data if latest_flow else None,
                "tasks": HomepageTaskSerializer(tasks, many=True).data,
                "settings": HomepagePreferenceSerializer(preferences).data if preferences else None,
                "quick_actions": [
                    {"id": 1, "label": "Start Flow", "key": "start_flow"},
                    {"id": 2, "label": "Open Taskboard", "key": "open_taskboard"},
                ],
            }
        )


class HomepagePresentationSlidesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        manifest_path = (
            Path(settings.BASE_DIR)
            / "docs"
            / "architecture"
            / "presentation"
            / "ui"
            / "generated"
            / "manifest.json"
        )
        payload = {
            "generated_at": "",
            "slides": [],
            "manifest_path": str(manifest_path),
        }

        if manifest_path.exists():
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                payload["manifest_path"] = str(manifest_path)
            except Exception:
                payload["slides"] = []
                payload["generated_at"] = ""

        return Response(payload)


class HomepageAppView(LoginRequiredMixin, TemplateView):
    template_name = "homepage_backend/app.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vite_dev_server = os.environ.get("HOMEPAGE_VITE_DEV_SERVER", "http://127.0.0.1:5173")
        use_vite_dev_server = os.environ.get("HOMEPAGE_USE_VITE_DEV_SERVER", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        context["vite_dev_server"] = vite_dev_server
        context["debug"] = settings.DEBUG
        context["use_vite_dev_server"] = settings.DEBUG and use_vite_dev_server
        return context
