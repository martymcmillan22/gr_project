from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .markdown_parser import StoryMarkdownParser, StoryEntry, FORMAT_CHOICES
from .models import StorySession
from .git_integration import get_git_integration


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
    
    # Get commit history for MASTER_DOCUMENT.md
    history = git.get_commit_history(
        file_path='storytelling_dashboard/MASTER_DOCUMENT.md',
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
