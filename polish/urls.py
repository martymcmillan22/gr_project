from django.urls import include, path

from .views import (
    PolishDashboardView,
    TaskManagerAdminView,
    TaskManagerAssignmentActionView,
    TaskManagerAssignmentCreateView,
    TaskManagerAnalyticsCsvExportView,
    TaskManagerAnalyticsPdfExportView,
    TaskManagerAssignmentReportView,
    TaskManagerAttachmentDownloadView,
    TaskManagerAttachItemView,
    TaskManagerItemActionView,
    TaskManagerQuarantineListView,
    TaskManagerQuarantineActionView,
)

app_name = "polish"

task_manager_patterns = (
    [
        path("assignments/create/", TaskManagerAssignmentCreateView.as_view(), name="create-assignment"),
        path("analytics/export/csv/", TaskManagerAnalyticsCsvExportView.as_view(), name="export-analytics-csv"),
        path("analytics/export/pdf/", TaskManagerAnalyticsPdfExportView.as_view(), name="export-analytics-pdf"),
        path("assignments/<int:assignment_id>/attach-item/", TaskManagerAttachItemView.as_view(), name="attach-item"),
        path("attachments/<int:attachment_id>/download/", TaskManagerAttachmentDownloadView.as_view(), name="download-attachment"),
        path("quarantine/", TaskManagerQuarantineListView.as_view(), name="quarantine-list"),
        path("quarantine/<int:quarantine_id>/", TaskManagerQuarantineListView.as_view(), name="quarantine-detail"),
        path("quarantine/<int:quarantine_id>/actions/", TaskManagerQuarantineActionView.as_view(), name="quarantine-actions"),
        path("assignments/<int:assignment_id>/actions/", TaskManagerAssignmentActionView.as_view(), name="assignment-actions"),
        path("assignments/<int:assignment_id>/report/", TaskManagerAssignmentReportView.as_view(), name="assignment-report"),
        path("items/<int:item_id>/actions/", TaskManagerItemActionView.as_view(), name="item-actions"),
    ],
    "task-manager",
)

urlpatterns = [
    path("", PolishDashboardView.as_view(), name="dashboard"),
    path("task-manager/", include(task_manager_patterns, namespace="task-manager")),
]
