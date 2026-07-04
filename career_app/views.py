from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.cache import cache
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from hashlib import md5
from collections import Counter
import csv
import json

from .models import CareerPath, CareerFilterPreset

# ReportLab core document generation libraries
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- REPORTLAB SHAPES & PIE CHART GRAPHICS LIBS ---
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend

def _seed_if_empty():
    if CareerPath.objects.exists():
        return

    raw_data = [
        {"subject": "Computer Science", "degree_level_code": 1, "degree_name": "Associate Degree", "career_title": "IT Support Specialist", "salary_metric": "$54,000"},
        {"subject": "Computer Science", "degree_level_code": 1, "degree_name": "Associate Degree", "career_title": "Web Developer", "salary_metric": "$78,000"},
        {"subject": "Computer Science", "degree_level_code": 1, "degree_name": "Associate Degree", "career_title": "Help Desk Technician", "salary_metric": "$48,000"},
        {"subject": "Computer Science", "degree_level_code": 2, "degree_name": "Bachelor Degree", "career_title": "Software Engineer", "salary_metric": "$115,000"},
        {"subject": "Computer Science", "degree_level_code": 2, "degree_name": "Bachelor Degree", "career_title": "Data Analyst", "salary_metric": "$75,000"},
        {"subject": "Computer Science", "degree_level_code": 2, "degree_name": "Bachelor Degree", "career_title": "Systems Administrator", "salary_metric": "$88,000"},
        {"subject": "Computer Science", "degree_level_code": 3, "degree_name": "Master Degree", "career_title": "AI Engineer", "salary_metric": "$145,000"},
        {"subject": "Computer Science", "degree_level_code": 3, "degree_name": "Master Degree", "career_title": "Cybersecurity Architect", "salary_metric": "$135,000"},
        {"subject": "Computer Science", "degree_level_code": 3, "degree_name": "Master Degree", "career_title": "Data Scientist", "salary_metric": "$128,000"},
        {"subject": "Computer Science", "degree_level_code": 4, "degree_name": "Doctoral Degree", "career_title": "Computer Science Professor", "salary_metric": "$92,000"},
        {"subject": "Computer Science", "degree_level_code": 4, "degree_name": "Doctoral Degree", "career_title": "R&D Scientist", "salary_metric": "$160,000"},
        {"subject": "Computer Science", "degree_level_code": 4, "degree_name": "Doctoral Degree", "career_title": "Principal AI Researcher", "salary_metric": "$195,000"},
    ]
    CareerPath.objects.bulk_create([CareerPath(**row) for row in raw_data])


def _serialize_rows(queryset):
    return [
        {
            'Subject': row['subject'],
            'Degree_Level_Code': row['degree_level_code'],
            'Degree_Name': row['degree_name'],
            'Career_Title': row['career_title'],
            'Salary_Metric': row['salary_metric'],
        }
        for row in queryset.values(
            'subject',
            'degree_level_code',
            'degree_name',
            'career_title',
            'salary_metric',
        )
    ]


def _salary_to_int(salary_text):
    digits_only = ''.join(ch for ch in str(salary_text) if ch.isdigit())
    return int(digits_only) if digits_only else 0


def _apply_sort(rows, sort_by):
    if sort_by == 'career_asc':
        return sorted(rows, key=lambda r: r['Career_Title'].lower())
    if sort_by == 'career_desc':
        return sorted(rows, key=lambda r: r['Career_Title'].lower(), reverse=True)
    if sort_by == 'degree_asc':
        return sorted(rows, key=lambda r: int(r['Degree_Level_Code']))
    if sort_by == 'degree_desc':
        return sorted(rows, key=lambda r: int(r['Degree_Level_Code']), reverse=True)
    if sort_by == 'salary_asc':
        return sorted(rows, key=lambda r: _salary_to_int(r['Salary_Metric']))
    # default sort: salary_desc
    return sorted(rows, key=lambda r: _salary_to_int(r['Salary_Metric']), reverse=True)


def _build_analytics(rows):
    total_results = len(rows)
    if total_results == 0:
        return {
            'total_results': 0,
            'avg_salary_display': '$0',
            'top_subject': 'N/A',
            'degree_counts': [
                {'name': 'Associate Degree', 'count': 0},
                {'name': 'Bachelor Degree', 'count': 0},
                {'name': 'Master Degree', 'count': 0},
                {'name': 'Doctoral Degree', 'count': 0},
            ],
        }

    salary_values = [_salary_to_int(r['Salary_Metric']) for r in rows]
    avg_salary = int(sum(salary_values) / total_results)
    subject_counts = Counter(r['Subject'] for r in rows)
    degree_counts_raw = Counter(int(r['Degree_Level_Code']) for r in rows)

    return {
        'total_results': total_results,
        'avg_salary_display': f"${avg_salary:,}",
        'top_subject': subject_counts.most_common(1)[0][0],
        'degree_counts': [
            {'name': 'Associate Degree', 'count': degree_counts_raw.get(1, 0)},
            {'name': 'Bachelor Degree', 'count': degree_counts_raw.get(2, 0)},
            {'name': 'Master Degree', 'count': degree_counts_raw.get(3, 0)},
            {'name': 'Doctoral Degree', 'count': degree_counts_raw.get(4, 0)},
        ],
    }

def search_careers(request):
    selected_subjects = request.GET.getlist('selected_subjects')
    degree_query = request.GET.get('degree_query', '').strip()
    sort_by = request.GET.get('sort_by', 'salary_desc').strip() or 'salary_desc'
    page_number = request.GET.get('page', '1').strip() or '1'

    _seed_if_empty()

    query_signature = f"{','.join(sorted(selected_subjects))}|{degree_query or 'all'}|{sort_by}"
    query_cache_key = f"career_rows:{md5(query_signature.encode('utf-8')).hexdigest()}"
    all_results = cache.get(query_cache_key)

    if all_results is None:
        queryset = CareerPath.objects.all()
        if selected_subjects:
            queryset = queryset.filter(subject__in=selected_subjects)
        if degree_query:
            try:
                queryset = queryset.filter(degree_level_code=int(degree_query))
            except ValueError:
                pass

        all_results = _serialize_rows(queryset)
        all_results = _apply_sort(all_results, sort_by)
        cache.set(query_cache_key, all_results, timeout=300)

    cache.set('active_pdf_snapshot', all_results, timeout=300)

    analytics = _build_analytics(all_results)
    paginator = Paginator(all_results, 9)
    page_obj = paginator.get_page(page_number)
    results = list(page_obj.object_list)

    subjects = cache.get('career_subjects')
    if subjects is None:
        subjects = list(CareerPath.objects.values_list('subject', flat=True).distinct().order_by('subject'))
        cache.set('career_subjects', subjects, timeout=3600)

    context = {
        'results': results,
        'subjects': subjects,
        'selected_subjects': selected_subjects,
        'degree_query': str(degree_query),
        'sort_by': sort_by,
        'analytics': analytics,
        'page_obj': page_obj,
        'preset_api_url': reverse('filter_presets'),
    }
    return render(request, 'career_app/search.html', context)


def export_careers_pdf(request):
    """Generates an on-the-fly downloadable PDF document featuring a dynamic shapes pie chart."""
    rows = cache.get('active_pdf_snapshot')
    if not rows:
        return HttpResponse("No filtered data matrix available to compile.", status=400)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="career_path_report.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor("#1e3a8a"), spaceAfter=4)
    header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=11, bold=True, textColor=colors.white)
    cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=10, leading=13)

    story.append(Paragraph("Career Matrix Alignment Report", title_style))
    story.append(Paragraph("Custom data breakdown including visual metrics and academic tier assignments.", styles['Normal']))
    story.append(Spacer(1, 15))

    # =========================================================================
    # DYNAMIC PIE CHART DESIGN (REPORTLAB SHAPES)
    # =========================================================================
    # Calculate distributions based on subject parameters in current view snapshot
    subject_counts = Counter(row['Subject'] for row in rows)
    labels = list(subject_counts.keys())
    values = list(subject_counts.values())

    # 1. Instantiate Canvas Drawing Frame (Width, Height)
    chart_drawing = Drawing(540, 160)
    
    # 2. Build Pie Component Engine
    pie = Pie()
    pie.x = 40
    pie.y = 20
    pie.width = 120
    pie.height = 120
    pie.data = values
    pie.labels = [f"{v} ({int((v/sum(values))*100)}%)" for v in values] # Displays exact count & matching percentage
    pie.sideLabels = 1  # Draw call-out lines cleanly away from center slices

    # Set up a palette of distinct matching corporate hex tones for slices
    palette = [colors.HexColor("#2563eb"), colors.HexColor("#10b981"), colors.HexColor("#f59e0b"), colors.HexColor("#ef4444")]
    for idx, color in enumerate(palette[:len(values)]):
        pie.slices[idx].fillColor = color

    chart_drawing.add(pie)

    # 3. Build Legend Mapping Sidebar Node
    legend = Legend()
    legend.x = 280
    legend.y = 120
    legend.dx = 10
    legend.dy = 10
    legend.fontName = 'Helvetica'
    legend.fontSize = 10
    legend.boxAnchor = 'nw'
    legend.columnMaximum = 4
    legend.colorNamePairs = [(palette[i], labels[i]) for i in range(len(labels))]
    
    chart_drawing.add(legend)
    
    # Title overlay on top of shapes canvas
    chart_drawing.add(String(280, 142, "Distribution of Active Occupations by Subject Area", fontName='Helvetica-Bold', fontSize=11, fillColor=colors.HexColor("#475569")))

    # Append complete drawing directly into Flowable stream layout
    story.append(chart_drawing)
    story.append(Spacer(1, 20))
    # =========================================================================

    # Formulate Tabular Records Table Below Chart Diagram
    table_data = [[Paragraph("Subject Domain", header_style), Paragraph("Level", header_style), Paragraph("Degree Requirement", header_style), Paragraph("Career Title", header_style), Paragraph("Est. Salary", header_style)]]
    
    for row in rows:
        table_data.append([
            Paragraph(str(row['Subject']), cell_style),
            Paragraph(str(row['Degree_Level_Code']), cell_style),
            Paragraph(str(row['Degree_Name']), cell_style),
            Paragraph(f"<b>{row['Career_Title']}</b>", cell_style),
            Paragraph(str(row['Salary_Metric']), cell_style)
        ])

    career_table = Table(table_data, colWidths=[120, 45, 125, 170, 80])
    career_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    
    story.append(career_table)
    doc.build(story)
    return response


def export_careers_csv(request):
    """Exports the currently filtered rows as CSV."""
    rows = cache.get('active_pdf_snapshot')
    if not rows:
        return HttpResponse("No filtered data matrix available to export.", status=400)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="career_path_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Subject', 'Degree Level Code', 'Degree Name', 'Career Title', 'Salary Metric'])

    for row in rows:
        writer.writerow([
            row.get('Subject', ''),
            row.get('Degree_Level_Code', ''),
            row.get('Degree_Name', ''),
            row.get('Career_Title', ''),
            row.get('Salary_Metric', ''),
        ])

    return response

def clear_career_cache(request):
    cache.clear()
    cache.delete('active_pdf_snapshot')
    messages.success(request, "Database memory cache cleared and metrics updated!")
    return redirect('search_careers')


def _serialize_preset(preset):
    return {
        'id': preset.id,
        'name': preset.name,
        'state': {
            'degree_query': preset.degree_query,
            'sort_by': preset.sort_by,
            'selected_subjects': preset.selected_subjects,
        }
    }


@login_required
@require_http_methods(["GET", "POST"])
def filter_presets(request):
    if request.method == 'GET':
        presets = CareerFilterPreset.objects.filter(user=request.user).order_by('name')
        return JsonResponse({'presets': [_serialize_preset(p) for p in presets]})

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    name = str(payload.get('name', '')).strip()
    state = payload.get('state', {})
    if not name:
        return JsonResponse({'error': 'Preset name is required.'}, status=400)

    selected_subjects = state.get('selected_subjects', [])
    if not isinstance(selected_subjects, list):
        return JsonResponse({'error': 'selected_subjects must be a list.'}, status=400)

    preset, _created = CareerFilterPreset.objects.update_or_create(
        user=request.user,
        name=name,
        defaults={
            'degree_query': str(state.get('degree_query', '')),
            'sort_by': str(state.get('sort_by', 'salary_desc')),
            'selected_subjects': selected_subjects,
        }
    )

    return JsonResponse({'preset': _serialize_preset(preset)}, status=201)


@login_required
@require_http_methods(["DELETE"])
def filter_preset_detail(request, preset_id):
    deleted, _ = CareerFilterPreset.objects.filter(id=preset_id, user=request.user).delete()
    if not deleted:
        return JsonResponse({'error': 'Preset not found.'}, status=404)
    return JsonResponse({'deleted': True})
