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

from .generator import get_generator, get_hierarchy_generator
from .models import GeneratedTier, TierDefinition, IndustryProfile, SVEMTier, CCCPTier


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


@require_http_methods(["POST"])
@login_required
def api_generate_svem_branches(request):
    """
    API endpoint to generate SVEM branches from a GeneratedTier.
    
    POST /api/baseture/hierarchy/generate-svem/
    {
        "generated_tier_id": 1
    }
    """
    try:
        data = json.loads(request.body)
        generated_tier_id = data.get('generated_tier_id')
        
        try:
            generated_tier = GeneratedTier.objects.get(pk=generated_tier_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {generated_tier_id} not found',
            }, status=404)
        
        # Generate SVEM branches
        hierarchy_gen = get_hierarchy_generator()
        svem_output = hierarchy_gen.generate_svem(
            parent_tier_output=generated_tier.output,
            seed_input=generated_tier.seed_input,
            mlas_color=generated_tier.tier_definition.mlas_color,
            industry=generated_tier.tier_definition.industry.industry,
        )
        
        # Save SVEM tiers to database
        svem_tiers = []
        for branch_num in range(1, 5):
            svem_tier = SVEMTier.objects.create(
                parent_tier=generated_tier,
                branch_number=branch_num,
                seed_input=generated_tier.seed_input,
                mlas_color=generated_tier.tier_definition.mlas_color,
                industry=generated_tier.tier_definition.industry.industry,
                output=svem_output,
                rationale=f"SVEM branch {branch_num} generated from parent tier {generated_tier_id}",
                created_by=request.user,
            )
            svem_tiers.append(svem_tier)
        
        return JsonResponse({
            'success': True,
            'svem_tier_ids': [t.id for t in svem_tiers],
            'output': svem_output,
            'message': f'Generated 4 SVEM branches (IDs: {[t.id for t in svem_tiers]})',
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def api_generate_cccp_compartments(request):
    """
    API endpoint to generate CCCP compartments from an SVEM branch.
    
    POST /api/baseture/hierarchy/generate-cccp/
    {
        "svem_tier_id": 1
    }
    """
    try:
        data = json.loads(request.body)
        svem_tier_id = data.get('svem_tier_id')
        
        try:
            svem_tier = SVEMTier.objects.get(pk=svem_tier_id)
        except SVEMTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'SVEMTier {svem_tier_id} not found',
            }, status=404)
        
        # Generate CCCP compartments
        hierarchy_gen = get_hierarchy_generator()
        cccp_output = hierarchy_gen.generate_cccp(
            parent_svem_output=svem_tier.output,
            svem_branch_number=svem_tier.branch_number,
            seed_input=svem_tier.seed_input,
            mlas_color=svem_tier.mlas_color,
            industry=svem_tier.industry,
        )
        
        # Save CCCP tiers to database
        cccp_tiers = []
        for comp_num in range(1, 5):
            cccp_tier = CCCPTier.objects.create(
                parent_svem_tier=svem_tier,
                compartment_number=comp_num,
                seed_input=svem_tier.seed_input,
                mlas_color=svem_tier.mlas_color,
                industry=svem_tier.industry,
                output=cccp_output,
                rationale=f"CCCP compartment {comp_num} generated from SVEM branch {svem_tier_id}",
                created_by=request.user,
            )
            cccp_tiers.append(cccp_tier)
        
        return JsonResponse({
            'success': True,
            'cccp_tier_ids': [t.id for t in cccp_tiers],
            'output': cccp_output,
            'message': f'Generated 4 CCCP compartments (IDs: {[t.id for t in cccp_tiers]})',
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@login_required
def api_get_hierarchy_tree(request, root_id):
    """
    API endpoint to retrieve complete hierarchy tree from root GeneratedTier.
    
    GET /api/baseture/hierarchy/tree/<generated_tier_id>/
    """
    try:
        try:
            root_tier = GeneratedTier.objects.get(pk=root_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {root_id} not found',
            }, status=404)
        
        # Build hierarchy tree
        tree = {
            'root_tier': {
                'id': root_tier.id,
                'seed_input': root_tier.seed_input,
                'mlas_color': root_tier.tier_definition.mlas_color,
                'industry': root_tier.tier_definition.industry.industry,
                'created_at': root_tier.created_at.isoformat(),
            },
            'svem_branches': [],
        }
        
        # Get all SVEM branches
        svem_tiers = SVEMTier.objects.filter(parent_tier=root_tier).order_by('branch_number')
        
        for svem in svem_tiers:
            svem_data = {
                'id': svem.id,
                'branch_number': svem.branch_number,
                'seed_input': svem.seed_input,
                'created_at': svem.created_at.isoformat(),
                'cccp_compartments': [],
            }
            
            # Get all CCCP compartments for this SVEM branch
            cccp_tiers = CCCPTier.objects.filter(parent_svem_tier=svem).order_by('compartment_number')
            
            for cccp in cccp_tiers:
                cccp_data = {
                    'id': cccp.id,
                    'compartment_number': cccp.compartment_number,
                    'seed_input': cccp.seed_input,
                    'created_at': cccp.created_at.isoformat(),
                }
                svem_data['cccp_compartments'].append(cccp_data)
            
            tree['svem_branches'].append(svem_data)
        
        return JsonResponse({
            'success': True,
            'tree': tree,
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
