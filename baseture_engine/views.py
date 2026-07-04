"""
BaseTrue Pattern Engine API Views

Provides HTTP endpoints for tier generation, preview, and approval workflows.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator

from .generator import get_generator
from .models import GeneratedTier, TierDefinition, IndustryProfile


@require_http_methods(["POST"])
@csrf_exempt
def api_generate_tier(request):
    """
    API endpoint to generate a new tier.
    
    POST /api/baseture/generate/
    {
        "seed_input": "Customer onboarding message",
        "mlas_color": "BLUE",
        "industry": "COMMUNICATIONS",
        "tier_level": 1
    }
    """
    try:
        data = json.loads(request.body)
        
        # Extract parameters
        seed_input = data.get('seed_input', '').strip()
        mlas_color = data.get('mlas_color', '').upper()
        industry = data.get('industry', '').upper()
        tier_level = int(data.get('tier_level', 1))
        
        # Validate required fields
        if not seed_input:
            return JsonResponse({
                'success': False,
                'error': 'seed_input is required',
            }, status=400)
        
        # Generate tier
        generator = get_generator()
        result = generator.generate(
            seed_input=seed_input,
            mlas_color=mlas_color,
            industry=industry,
            tier_level=tier_level,
        )
        
        return JsonResponse({
            'success': result['valid'],
            'output': result['output'],
            'rationale': result['rationale'],
            'errors': result['errors'],
            'log': result.get('log', []),
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)


@require_http_methods(["POST"])
@login_required
def api_save_generated_tier(request):
    """
    API endpoint to save a generated tier to database.
    
    POST /api/baseture/save/
    {
        "seed_input": "Customer onboarding message",
        "tier_definition_id": 1,
        "output": {...},
        "rationale": "..."
    }
    """
    try:
        data = json.loads(request.body)
        
        tier_def_id = data.get('tier_definition_id')
        seed_input = data.get('seed_input')
        output = data.get('output')
        rationale = data.get('rationale', '')
        
        try:
            tier_definition = TierDefinition.objects.get(pk=tier_def_id)
        except TierDefinition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'TierDefinition {tier_def_id} not found',
            }, status=404)
        
        # Save to database
        generated_tier = GeneratedTier.objects.create(
            seed_input=seed_input,
            tier_definition=tier_definition,
            output=output,
            rationale=rationale,
            created_by=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'generated_tier_id': generated_tier.id,
            'message': f'Tier saved (ID: {generated_tier.id})',
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@login_required
def api_list_generated_tiers(request):
    """
    API endpoint to list generated tiers.
    
    GET /api/baseture/list/?status=generated&limit=20
    """
    try:
        status = request.GET.get('status', 'generated')
        limit = int(request.GET.get('limit', 20))
        
        tiers = GeneratedTier.objects.filter(status=status).order_by('-created_at')[:limit]
        
        results = [
            {
                'id': t.id,
                'seed_input': t.seed_input,
                'tier_definition': str(t.tier_definition),
                'status': t.status,
                'created_at': t.created_at.isoformat(),
                'created_by': t.created_by.username if t.created_by else 'system',
            }
            for t in tiers
        ]
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'results': results,
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def api_approve_tier(request, tier_id):
    """
    API endpoint to approve a generated tier.
    
    POST /api/baseture/approve/<tier_id>/
    """
    try:
        try:
            tier = GeneratedTier.objects.get(pk=tier_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Tier {tier_id} not found',
            }, status=404)
        
        # Update status
        tier.status = 'approved'
        tier.approved_by = request.user
        tier.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Tier {tier_id} approved',
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@login_required
def tier_dashboard(request):
    """
    Dashboard view for BTPE.
    Displays tier generation interface and history.
    """
    industries = IndustryProfile.objects.all()
    recent_tiers = GeneratedTier.objects.order_by('-created_at')[:10]
    
    context = {
        'industries': industries,
        'recent_tiers': recent_tiers,
        'mlas_colors': ['RED', 'BLUE', 'YELLOW', 'GREEN', 'PURPLE', 'TEAL', 'ORANGE', 'LIME', 'PINK', 'CYAN', 'AMBER', 'GREEN_LIME'],
    }
    
    return render(request, 'baseture_engine/dashboard.html', context)
