from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import re
from collections import defaultdict

from .markdown_parser import StoryMarkdownParser, StoryEntry, FORMAT_CHOICES
from .models import StorySession, SemanticPreset
from .git_integration import get_git_integration


def _parse_metadata_map(block: str) -> dict:
    """Parse markdown bullet metadata like '- Key: Value' into a normalized dict."""
    parsed = {}
    for line in str(block or "").split("\n"):
        match = re.match(r"^\s*-\s*([^:]+):\s*(.+?)\s*$", line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if key:
            parsed[key] = value
    return parsed


def _infer_timeline_phase(timeline_cell: str) -> str:
    token = str(timeline_cell or "").strip().lower().replace("_", "-")

    if token in {"present-past", "present to past", "present/past"}:
        return "present-past"
    if token in {"present-future", "present to future", "present/future"}:
        return "present-future"

    if token == "past":
        return "past"
    if token == "future":
        return "future"

    # Backward compatibility for legacy values that only encoded "present".
    if token == "present":
        return "present-past"

    if "present" in token and "past" in token:
        return "present-past"
    if "present" in token and "future" in token:
        return "present-future"
    if "past" in token:
        return "past"
    if "future" in token:
        return "future"
    return "unknown"


def _parse_dchd_atoms(summary: str) -> list:
    text = str(summary or "").strip()
    if not text or text == "none":
        return []
    atoms = [part.strip() for part in re.split(r"\||,", text) if part.strip()]
    return atoms


def _semantic_anchor_for_story(story: StoryEntry) -> dict:
    semantic_map = _parse_metadata_map(story.semantic_metadata)
    version_map = _parse_metadata_map(story.version_metadata)

    semantic_intent = (
        semantic_map.get("semantic intent")
        or semantic_map.get("semantic intent id")
        or ""
    )

    dchd_summary = semantic_map.get("dchd atom summary", "")
    scaffold_version_text = version_map.get("scaffold version", "")
    try:
        scaffold_version = int(scaffold_version_text)
    except (TypeError, ValueError):
        scaffold_version = None

    timeline_cell = semantic_map.get("timeline cell", "")

    return {
        "entry_id": story.entry_id,
        "title": story.title,
        "status": story.status,
        "mlas_color": semantic_map.get("mlas color", ""),
        "timeline_cell": timeline_cell,
        "timeline_phase": _infer_timeline_phase(timeline_cell),
        "semantic_path": semantic_map.get("semantic path", ""),
        "semantic_intent": semantic_intent,
        "hierarchy_node_key": semantic_map.get("hierarchy node key", "") or version_map.get("node key", ""),
        "scaffold_version": scaffold_version,
        "dchd_atom_summary": dchd_summary,
        "dchd_atoms": _parse_dchd_atoms(dchd_summary),
        "root_tier_id": version_map.get("root tier id", ""),
        "export_timestamp": version_map.get("export timestamp", ""),
        "chapter_count": len(story.chapters or []),
    }


@login_required
def dashboard(request):
    """Display all stories with status overview."""
    stories = StoryMarkdownParser.load_all_stories()
    
    # Calculate summary stats
    total = len(stories)
    completed = sum(1 for s in stories if s.status == 'complete')
    in_progress = sum(1 for s in stories if s.status == 'in_progress')
    pending = sum(1 for s in stories if s.status == 'pending')
    avg_progress = sum(s.calculate_progress() for s in stories) / total if total > 0 else 0
    
    context = {
        'stories': stories,
        'stats': {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'avg_progress': int(avg_progress),
        }
    }
    
    return render(request, 'storytelling_dashboard/dashboard.html', context)


@login_required
def story_detail(request, entry_id):
    """Display and edit a single story."""
    story = StoryMarkdownParser.get_story_by_id(entry_id)
    
    if not story:
        return HttpResponse('Story not found', status=404)
    
    # Get or create session
    session, created = StorySession.objects.get_or_create(
        entry_id=entry_id,
        defaults={
            'title': story.title,
            'status': story.status,
            'format': story.format,
            'progress': story.calculate_progress(),
        }
    )
    
    context = {
        'story': story,
        'session': session,
        'format_choices': FORMAT_CHOICES,
        'progress': session.progress,
    }
    
    return render(request, 'storytelling_dashboard/story_detail.html', context)


@require_http_methods(["GET"])
@login_required
def api_stories(request):
    """API endpoint: Get all stories."""
    stories = StoryMarkdownParser.load_all_stories()
    return JsonResponse({
        'success': True,
        'count': len(stories),
        'stories': [s.to_dict() for s in stories]
    })


@require_http_methods(["GET"])
@login_required
def api_story(request, entry_id):
    """API endpoint: Get single story."""
    story = StoryMarkdownParser.get_story_by_id(entry_id)
    
    if not story:
        return JsonResponse({'success': False, 'error': 'Story not found'}, status=404)
    
    return JsonResponse({
        'success': True,
        'story': story.to_dict()
    })


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def api_story_save(request, entry_id):
    """API endpoint: Save story edits."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    story = StoryMarkdownParser.get_story_by_id(entry_id)
    
    if not story:
        return JsonResponse({'success': False, 'error': 'Story not found'}, status=404)
    
    # Update story fields
    if 'title' in data:
        story.title = data['title']
    if 'talking_points' in data:
        story.talking_points = data.get('talking_points', [])
    if 'core_concept' in data:
        story.core_concept = data['core_concept']
    if 'synopsis' in data:
        story.synopsis = data['synopsis']
    if 'chapters' in data:
        story.chapters = data.get('chapters', [])
    if 'soundtrack_timeline' in data:
        story.soundtrack_timeline = data.get('soundtrack_timeline', [])
    if 'dynamic_navigation' in data:
        story.dynamic_navigation = data['dynamic_navigation']
    if 'semantic_metadata' in data:
        story.semantic_metadata = data['semantic_metadata']
    if 'version_metadata' in data:
        story.version_metadata = data['version_metadata']
    if 'character_profiles' in data:
        story.character_profiles = data.get('character_profiles', [])
    if 'research_file' in data:
        story.research_file = data['research_file']
    if 'future_timeline' in data:
        story.future_timeline = data['future_timeline']
    if 'table_of_contents' in data:
        story.table_of_contents = data['table_of_contents']
    if 'bibliography' in data:
        story.bibliography = data['bibliography']
    if 'anti_plagiarism' in data:
        story.anti_plagiarism = data['anti_plagiarism']
    if 'format' in data:
        story.format = data['format']
    if 'status' in data:
        story.status = data['status']
    
    # Save to markdown
    success = StoryMarkdownParser.save_entry(story)
    
    if success:
        # Update session
        session, _ = StorySession.objects.get_or_create(entry_id=entry_id)
        session.title = story.title
        session.status = story.status
        session.format = story.format
        session.talking_points = json.dumps(story.talking_points)
        session.core_concept = story.core_concept
        session.synopsis = story.synopsis
        session.progress = story.calculate_progress()
        session.last_edited_by = request.user
        session.save()
        
        # Commit changes to git
        git = get_git_integration()
        if git.is_available():
            git_message = f"📖 Update story #{entry_id}: {story.title}"
            git.commit_story_changes(entry_id, story.title, data)
            # Note: Not pushing automatically - user can do manual pushes
        
        return JsonResponse({
            'success': True,
            'message': 'Story saved successfully',
            'progress': session.progress,
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Failed to save story'
        }, status=500)


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def api_story_validate(request, entry_id):
    """API endpoint: Validate story against ENGINE_SCHEMA.md rules."""
    story = StoryMarkdownParser.get_story_by_id(entry_id)
    
    if not story:
        return JsonResponse({'success': False, 'error': 'Story not found'}, status=404)
    
    # Validation checks
    issues = []
    warnings = []
    
    # PART 2: 13 Sections check
    if not story.title:
        issues.append('Title is required')
    if not story.talking_points:
        issues.append('Talking Points required (3–5 hooks)')
    if not story.core_concept:
        issues.append('Core Concept required')
    if not story.synopsis:
        issues.append('Synopsis required (200–300 words)')
    if not story.chapters or len(story.chapters) < 12:
        warnings.append(f'Expected 12+ chapters, found {len(story.chapters)}')
    elif len(story.chapters) < 36 or len(story.chapters) > 72:
        warnings.append(f'Chapter count {len(story.chapters)} outside recommended ranges for chosen format')
    
    # PART 6: Format validation
    if story.format == 'short_series' and len(story.chapters) > 24:
        warnings.append('Short series typically 12–24 chapters; consider different format')
    elif story.format == 'one_hour_series' and (len(story.chapters) < 24 or len(story.chapters) > 36):
        warnings.append('1-Hour series typically 24–36 chapters')
    elif story.format == 'movie' and (len(story.chapters) < 36 or len(story.chapters) > 60):
        warnings.append('Movie typically 36–60 chapters')
    elif story.format == 'epic_movie' and len(story.chapters) < 60:
        warnings.append('Epic movie typically 60–72+ chapters')
    
    return JsonResponse({
        'success': True,
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'progress': story.calculate_progress(),
    })


@require_http_methods(["GET"])
@login_required
def api_git_history(request, entry_id: int):
    """API endpoint: Get git commit history for story."""
    story = StoryMarkdownParser.get_story_by_id(entry_id)
    
    if not story:
        return JsonResponse({'success': False, 'error': 'Story not found'}, status=404)
    
    git = get_git_integration()
    
    if not git.is_available():
        return JsonResponse({
            'success': False,
            'message': 'Git integration not available',
            'available': False
        })
    
    # Get commit history for MASTER_DOCUMENT.md (correct path with hyphen)
    history = git.get_commit_history(
        file_path='storytelling-engine/MASTER_DOCUMENT.md',
        max_count=10
    )
    
    git_status = git.get_status()
    
    return JsonResponse({
        'success': True,
        'available': True,
        'history': history,
        'status': git_status,
    })


@require_http_methods(["POST"])
@login_required
@csrf_exempt
def api_git_push(request):
    """API endpoint: Push commits to remote repository."""
    git = get_git_integration()
    
    if not git.is_available():
        return JsonResponse({
            'success': False,
            'message': 'Git integration not available'
        })
    
    try:
        # Push to origin/main (or whatever the current branch is)
        success = git.push_to_remote()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Changes pushed to remote successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to push changes'
            }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Push error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def api_git_status(request):
    """API endpoint: Get current git status."""
    git = get_git_integration()
    
    if not git.is_available():
        return JsonResponse({
            'success': False,
            'available': False,
            'message': 'Git integration not available'
        })
    
    status = git.get_status()
    
    return JsonResponse({
        'success': True,
        'available': True,
        'status': status
    })


@require_http_methods(["GET"])
@login_required
def api_semantic_search(request):
    """Semantic search across story anchors extracted from MASTER_DOCUMENT metadata."""
    stories = StoryMarkdownParser.load_all_stories()
    anchors = [_semantic_anchor_for_story(story) for story in stories]

    filters = {
        "mlas_color": request.GET.get("mlas_color", "").strip().lower(),
        "timeline_cell": request.GET.get("timeline_cell", "").strip().lower(),
        "semantic_intent": request.GET.get("semantic_intent", "").strip().lower(),
        "scaffold_version": request.GET.get("scaffold_version", "").strip(),
        "dchd_atom": request.GET.get("dchd_atom", "").strip().lower(),
        "status": request.GET.get("status", "").strip().lower(),
        "semantic_path": request.GET.get("semantic_path", "").strip().lower(),
    }

    results = anchors

    if filters["mlas_color"]:
        results = [item for item in results if filters["mlas_color"] in str(item.get("mlas_color", "")).lower()]
    if filters["timeline_cell"]:
        results = [item for item in results if filters["timeline_cell"] in str(item.get("timeline_cell", "")).lower()]
    if filters["semantic_intent"]:
        results = [item for item in results if filters["semantic_intent"] in str(item.get("semantic_intent", "")).lower()]
    if filters["semantic_path"]:
        results = [item for item in results if filters["semantic_path"] in str(item.get("semantic_path", "")).lower()]
    if filters["status"]:
        results = [item for item in results if filters["status"] == str(item.get("status", "")).lower()]
    if filters["dchd_atom"]:
        results = [
            item for item in results
            if any(filters["dchd_atom"] in atom.lower() for atom in item.get("dchd_atoms", []))
        ]

    if filters["scaffold_version"]:
        try:
            target_version = int(filters["scaffold_version"])
            results = [item for item in results if item.get("scaffold_version") == target_version]
        except ValueError:
            return JsonResponse({
                "success": False,
                "error": "scaffold_version must be an integer",
            }, status=400)

    return JsonResponse({
        "success": True,
        "count": len(results),
        "filters": filters,
        "results": results,
    })


@require_http_methods(["GET"])
@login_required
def api_semantic_clusters(request):
    """Cluster stories into semantic constellations across the story universe."""
    cluster_by = request.GET.get("by", "mlas").strip().lower()
    allowed = {"mlas", "timeline_phase", "semantic_path", "scaffold_version", "dchd_cluster"}
    if cluster_by not in allowed:
        return JsonResponse({
            "success": False,
            "error": f"Invalid cluster mode '{cluster_by}'. Allowed: {', '.join(sorted(allowed))}",
        }, status=400)

    stories = StoryMarkdownParser.load_all_stories()
    anchors = [_semantic_anchor_for_story(story) for story in stories]

    buckets = defaultdict(list)
    for item in anchors:
        if cluster_by == "mlas":
            key = item.get("mlas_color") or "unknown"
        elif cluster_by == "timeline_phase":
            key = item.get("timeline_phase") or "unknown"
        elif cluster_by == "semantic_path":
            key = item.get("semantic_path") or "unknown"
        elif cluster_by == "scaffold_version":
            key = str(item.get("scaffold_version") if item.get("scaffold_version") is not None else "unknown")
        else:
            atoms = item.get("dchd_atoms") or []
            key = " | ".join(sorted(atoms[:3])) if atoms else "none"
        buckets[key].append(item)

    clusters = []
    for key, items in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        clusters.append({
            "cluster_key": key,
            "count": len(items),
            "entries": [
                {
                    "entry_id": item["entry_id"],
                    "title": item["title"],
                    "status": item["status"],
                    "semantic_path": item.get("semantic_path", ""),
                    "scaffold_version": item.get("scaffold_version"),
                }
                for item in items
            ],
        })

    return JsonResponse({
        "success": True,
        "cluster_by": cluster_by,
        "cluster_count": len(clusters),
        "clusters": clusters,
    })


@require_http_methods(["GET"])
@login_required
def api_semantic_diff(request):
    """Cross-story semantic diffing for consistency checks."""
    source_id = request.GET.get("source_id")
    target_id = request.GET.get("target_id")
    if not source_id or not target_id:
        return JsonResponse({
            "success": False,
            "error": "source_id and target_id are required",
        }, status=400)

    try:
        source_id_int = int(source_id)
        target_id_int = int(target_id)
    except ValueError:
        return JsonResponse({
            "success": False,
            "error": "source_id and target_id must be integers",
        }, status=400)

    source_story = StoryMarkdownParser.get_story_by_id(source_id_int)
    target_story = StoryMarkdownParser.get_story_by_id(target_id_int)

    if not source_story or not target_story:
        return JsonResponse({
            "success": False,
            "error": "One or both stories not found",
        }, status=404)

    source_anchor = _semantic_anchor_for_story(source_story)
    target_anchor = _semantic_anchor_for_story(target_story)

    source_semantic_map = _parse_metadata_map(source_story.semantic_metadata)
    target_semantic_map = _parse_metadata_map(target_story.semantic_metadata)
    semantic_keys = sorted(set(source_semantic_map.keys()) | set(target_semantic_map.keys()))
    semantic_changes = []
    for key in semantic_keys:
        source_value = source_semantic_map.get(key, "")
        target_value = target_semantic_map.get(key, "")
        if source_value != target_value:
            semantic_changes.append({
                "key": key,
                "source": source_value,
                "target": target_value,
            })

    source_chapters = source_story.chapters or []
    target_chapters = target_story.chapters or []
    source_titles = [str(ch.get("title", "")).strip() for ch in source_chapters]
    target_titles = [str(ch.get("title", "")).strip() for ch in target_chapters]

    source_atoms = set(source_anchor.get("dchd_atoms", []))
    target_atoms = set(target_anchor.get("dchd_atoms", []))

    return JsonResponse({
        "success": True,
        "source": {
            "entry_id": source_story.entry_id,
            "title": source_story.title,
            "scaffold_version": source_anchor.get("scaffold_version"),
            "chapter_count": len(source_chapters),
        },
        "target": {
            "entry_id": target_story.entry_id,
            "title": target_story.title,
            "scaffold_version": target_anchor.get("scaffold_version"),
            "chapter_count": len(target_chapters),
        },
        "diff": {
            "scaffold_version_delta": {
                "source": source_anchor.get("scaffold_version"),
                "target": target_anchor.get("scaffold_version"),
            },
            "semantic_metadata_changes": semantic_changes,
            "chapter_structure_changes": {
                "chapter_count_delta": len(target_chapters) - len(source_chapters),
                "added_titles": sorted(set(target_titles) - set(source_titles)),
                "removed_titles": sorted(set(source_titles) - set(target_titles)),
            },
            "rationale_changes": {
                "note": "Rationale is not currently persisted per story entry; dynamic_navigation is used as the closest authored narrative rationale signal.",
                "source_dynamic_navigation": source_story.dynamic_navigation,
                "target_dynamic_navigation": target_story.dynamic_navigation,
                "changed": source_story.dynamic_navigation != target_story.dynamic_navigation,
            },
            "dchd_atom_shifts": {
                "added": sorted(target_atoms - source_atoms),
                "removed": sorted(source_atoms - target_atoms),
                "unchanged": sorted(source_atoms & target_atoms),
            },
        },
    })


@require_http_methods(["GET", "POST"])
@login_required
@csrf_exempt
def api_semantic_presets(request):
    """List or create semantic operation presets for the authenticated user."""
    if request.method == "GET":
        presets = SemanticPreset.objects.filter(owner=request.user).order_by('preset_type', 'name')
        results = [
            {
                "id": preset.id,
                "name": preset.name,
                "preset_type": preset.preset_type,
                "payload": preset.payload,
                "updated_at": preset.updated_at.isoformat(),
            }
            for preset in presets
        ]
        return JsonResponse({
            "success": True,
            "count": len(results),
            "results": results,
        })

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    name = str(data.get("name") or "").strip()
    preset_type = str(data.get("preset_type") or "").strip().lower()
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}

    if not name:
        return JsonResponse({"success": False, "error": "name is required"}, status=400)
    if preset_type not in {"search", "cluster"}:
        return JsonResponse({"success": False, "error": "preset_type must be search or cluster"}, status=400)

    preset, created = SemanticPreset.objects.update_or_create(
        owner=request.user,
        name=name,
        preset_type=preset_type,
        defaults={"payload": payload},
    )

    return JsonResponse({
        "success": True,
        "created": created,
        "preset": {
            "id": preset.id,
            "name": preset.name,
            "preset_type": preset.preset_type,
            "payload": preset.payload,
            "updated_at": preset.updated_at.isoformat(),
        },
    })


@require_http_methods(["POST", "DELETE"])
@login_required
@csrf_exempt
def api_semantic_preset_detail(request, preset_id: int):
    """Update or delete an existing semantic preset."""
    try:
        preset = SemanticPreset.objects.get(pk=preset_id, owner=request.user)
    except SemanticPreset.DoesNotExist:
        return JsonResponse({"success": False, "error": "Preset not found"}, status=404)

    if request.method == "DELETE":
        preset.delete()
        return JsonResponse({"success": True})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    name = data.get("name")
    payload = data.get("payload")

    if name is not None:
        normalized_name = str(name).strip()
        if not normalized_name:
            return JsonResponse({"success": False, "error": "name cannot be empty"}, status=400)
        preset.name = normalized_name
    if isinstance(payload, dict):
        preset.payload = payload

    preset.save()
    return JsonResponse({
        "success": True,
        "preset": {
            "id": preset.id,
            "name": preset.name,
            "preset_type": preset.preset_type,
            "payload": preset.payload,
            "updated_at": preset.updated_at.isoformat(),
        },
    })
