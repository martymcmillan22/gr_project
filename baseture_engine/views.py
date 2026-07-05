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
from .models import GeneratedTier, TierDefinition, IndustryProfile, SVEMTier, CCCPTier, DCHDTier, StoryScaffold


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
        
        # Save the generated tier to the database
        if result['valid']:
            try:
                # Find a matching TierDefinition for this MLAS color
                tier_def = TierDefinition.objects.filter(
                    mlas_color=mlas_color,
                    tier_level=tier_level
                ).first()
                
                if tier_def:
                    generated_tier = GeneratedTier.objects.create(
                        seed_input=seed_input,
                        tier_definition=tier_def,
                        output=result['output'],
                        status='generated',
                        rationale=result.get('rationale', ''),
                    )
                    tier_id = generated_tier.id
                else:
                    tier_id = None
            except Exception as e:
                tier_id = None
        else:
            tier_id = None
        
        return JsonResponse({
            'success': result['valid'],
            'output': result['output'],
            'rationale': result['rationale'],
            'errors': result['errors'],
            'log': result.get('log', []),
            'tier_id': tier_id,
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


@require_http_methods(["POST"])
@login_required
def api_generate_dchd_subcells(request):
    """
    API endpoint to generate DCHD subcells from a CCCP compartment.
    
    POST /api/baseture/hierarchy/generate-dchd/
    {
        "cccp_tier_id": 1
    }
    """
    try:
        data = json.loads(request.body)
        cccp_tier_id = data.get('cccp_tier_id')
        
        try:
            cccp_tier = CCCPTier.objects.get(pk=cccp_tier_id)
        except CCCPTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'CCCPTier {cccp_tier_id} not found',
            }, status=404)
        
        # Generate DCHD subcells
        hierarchy_gen = get_hierarchy_generator()
        dchd_output = hierarchy_gen.generate_dchd(
            parent_cccp_output=cccp_tier.output,
            cccp_compartment_number=cccp_tier.compartment_number,
            seed_input=cccp_tier.seed_input,
            mlas_color=cccp_tier.mlas_color,
            industry=cccp_tier.industry,
        )
        
        # Save DCHD tiers to database
        dchd_tiers = []
        for subcell_num in range(1, 5):
            dchd_tier = DCHDTier.objects.create(
                parent_cccp_tier=cccp_tier,
                subcell_number=subcell_num,
                seed_input=cccp_tier.seed_input,
                mlas_color=cccp_tier.mlas_color,
                industry=cccp_tier.industry,
                output=dchd_output,
                rationale=f"DCHD subcell {subcell_num} generated from CCCP compartment {cccp_tier_id}",
                created_by=request.user,
            )
            dchd_tiers.append(dchd_tier)
        
        return JsonResponse({
            'success': True,
            'dchd_tier_ids': [t.id for t in dchd_tiers],
            'output': dchd_output,
            'message': f'Generated 4 DCHD subcells (IDs: {[t.id for t in dchd_tiers]})',
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
                    'dchd_subcells': [],
                }
                
                # Get all DCHD subcells for this CCCP compartment
                dchd_tiers = DCHDTier.objects.filter(parent_cccp_tier=cccp).order_by('subcell_number')
                
                for dchd in dchd_tiers:
                    dchd_data = {
                        'id': dchd.id,
                        'subcell_number': dchd.subcell_number,
                        'seed_input': dchd.seed_input,
                        'created_at': dchd.created_at.isoformat(),
                    }
                    cccp_data['dchd_subcells'].append(dchd_data)
                
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
def api_get_expansion_status(request, root_id):
    """
    API endpoint to get expansion status for all tiers.
    
    GET /api/hierarchy/status/<generated_tier_id>/
    
    Returns:
    {
        "success": true,
        "root_id": 1,
        "status": {
            "svem_count": 4,
            "svem_generated": 1,
            "cccp_count": 16,
            "cccp_generated": 4,
            "dchd_count": 64,
            "dchd_generated": 4,
            "branches": [
                {
                    "branch_number": 1,
                    "generated": true,
                    "compartments": [
                        {
                            "compartment_number": 1,
                            "generated": true,
                            "dchd_count": 4
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    }
    """
    try:
        try:
            root_tier = GeneratedTier.objects.get(pk=root_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {root_id} not found',
            }, status=404)
        
        # Calculate expansion counts
        all_svem = SVEMTier.objects.filter(parent_tier=root_tier).count()
        all_cccp = CCCPTier.objects.filter(parent_svem_tier__parent_tier=root_tier).count()
        all_dchd = DCHDTier.objects.filter(parent_cccp_tier__parent_svem_tier__parent_tier=root_tier).count()
        
        # Build branch status
        branches = []
        for branch_num in range(1, 5):
            svem = SVEMTier.objects.filter(parent_tier=root_tier, branch_number=branch_num).first()
            branch_data = {
                'branch_number': branch_num,
                'generated': svem is not None,
                'compartments': [],
            }
            
            if svem:
                for comp_num in range(1, 5):
                    cccp = CCCPTier.objects.filter(parent_svem_tier=svem, compartment_number=comp_num).first()
                    dchd_count = 0
                    if cccp:
                        dchd_count = DCHDTier.objects.filter(parent_cccp_tier=cccp).count()
                    
                    branch_data['compartments'].append({
                        'compartment_number': comp_num,
                        'generated': cccp is not None,
                        'dchd_count': dchd_count,
                    })
            
            branches.append(branch_data)
        
        return JsonResponse({
            'success': True,
            'root_id': root_id,
            'status': {
                'svem_count': 4,
                'svem_generated': all_svem,
                'cccp_count': 16,
                'cccp_generated': all_cccp,
                'dchd_count': 64,
                'dchd_generated': all_dchd,
                'branches': branches,
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def api_expand_all_branches(request, root_id):
    """
    Batch endpoint to expand all remaining SVEM branches.
    Calls generate_cccp for each SVEM branch that doesn't have compartments yet.
    
    POST /api/hierarchy/expand-all-branches/<generated_tier_id>/
    """
    try:
        try:
            root_tier = GeneratedTier.objects.get(pk=root_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {root_id} not found',
            }, status=404)
        
        data = json.loads(request.body) if request.body else {}
        gen = get_hierarchy_generator()
        expanded_count = 0
        errors = []
        
        # Get all SVEM branches
        all_svem = SVEMTier.objects.filter(parent_tier=root_tier).order_by('branch_number')
        
        for svem in all_svem:
            # Check if this branch already has compartments
            existing_cccp = CCCPTier.objects.filter(parent_svem_tier=svem).count()
            if existing_cccp > 0:
                continue
            
            # Generate CCCP for this branch
            try:
                # Fetch parent SVEM output to get the structure
                cccp_output = gen.generate_cccp(
                    parent_svem_output={'tier_type': 'SVEM'},
                    svem_branch_number=svem.branch_number,
                    seed_input=svem.seed_input,
                    mlas_color=svem.mlas_color,
                    industry=svem.industry,
                )
                
                # Create CCCP tier records
                if 'compartments' in cccp_output:
                    for comp_num, comp_data in cccp_output['compartments'].items():
                        CCCPTier.objects.create(
                            parent_svem_tier=svem,
                            compartment_number=comp_data.get('compartment_number'),
                            seed_input=svem.seed_input,
                            mlas_color=svem.mlas_color,
                            industry=svem.industry,
                            output=json.dumps(comp_data),
                            status='generated',
                            constraints_validated=True,
                        )
                    expanded_count += 1
            except Exception as e:
                errors.append(f"Branch {svem.branch_number}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'expanded_count': expanded_count,
            'total_branches': len(all_svem),
            'errors': errors if errors else None,
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def api_expand_all_compartments(request, root_id):
    """
    Batch endpoint to expand all remaining CCCP compartments with DCHD subcells.
    Calls generate_dchd for each compartment that doesn't have subcells yet.
    
    POST /api/hierarchy/expand-all-compartments/<generated_tier_id>/
    """
    try:
        try:
            root_tier = GeneratedTier.objects.get(pk=root_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {root_id} not found',
            }, status=404)
        
        data = json.loads(request.body) if request.body else {}
        gen = get_hierarchy_generator()
        expanded_count = 0
        errors = []
        
        # Get all CCCP compartments
        all_cccp = CCCPTier.objects.filter(parent_svem_tier__parent_tier=root_tier).order_by('parent_svem_tier', 'compartment_number')
        
        for cccp in all_cccp:
            # Check if this compartment already has subcells
            existing_dchd = DCHDTier.objects.filter(parent_cccp_tier=cccp).count()
            if existing_dchd > 0:
                continue
            
            # Generate DCHD for this compartment
            try:
                dchd_output = gen.generate_dchd(
                    parent_cccp_output={'tier_type': 'CCCP'},
                    cccp_compartment_number=cccp.compartment_number,
                    seed_input=cccp.seed_input,
                    mlas_color=cccp.mlas_color,
                    industry=cccp.industry,
                )
                
                # Create DCHD tier records
                if 'subcells' in dchd_output:
                    for subcell_num, subcell_data in dchd_output['subcells'].items():
                        DCHDTier.objects.create(
                            parent_cccp_tier=cccp,
                            subcell_number=subcell_data.get('subcell_number'),
                            seed_input=cccp.seed_input,
                            mlas_color=cccp.mlas_color,
                            industry=cccp.industry,
                            output=json.dumps(subcell_data),
                            status='generated',
                            constraints_validated=True,
                        )
                    expanded_count += 1
            except Exception as e:
                errors.append(f"Compartment {cccp.id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'expanded_count': expanded_count,
            'total_compartments': len(list(all_cccp)),
            'errors': errors if errors else None,
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@login_required
def api_get_story_scaffolds(request, root_id):
    """Return all saved scaffolds for a root hierarchy tier."""
    try:
        try:
            root_tier = GeneratedTier.objects.get(pk=root_id)
        except GeneratedTier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'GeneratedTier {root_id} not found',
            }, status=404)

        scaffolds = StoryScaffold.objects.filter(root_tier=root_tier).order_by('node_key')
        results = [
            {
                'id': scaffold.id,
                'root_tier_id': scaffold.root_tier_id,
                'node_key': scaffold.node_key,
                'node_type': scaffold.node_type,
                'node_id': scaffold.node_id,
                'timeline_lattice_index': scaffold.timeline_lattice_index,
                'timeline_label': scaffold.timeline_label,
                'semantic_intent_id': scaffold.semantic_intent_id,
                'talking_points': scaffold.talking_points,
                'core_concept': scaffold.core_concept,
                'synopsis': scaffold.synopsis,
                'chapter_structure': scaffold.chapter_structure,
                'dchd_atoms': scaffold.dchd_atoms,
                'scaffold_version': scaffold.scaffold_version,
                'decision': scaffold.decision,
                'updated_at': scaffold.updated_at.isoformat(),
            }
            for scaffold in scaffolds
        ]

        return JsonResponse({
            'success': True,
            'root_id': root_id,
            'results': results,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
def api_upsert_story_scaffold(request):
    """Create or update a story scaffold mapped to a hierarchy node."""
    try:
        data = json.loads(request.body)
        root_tier_id = data.get('root_tier_id')
        node_key = str(data.get('node_key') or '').strip()
        node_type = str(data.get('node_type') or '').strip().lower()
        node_id = data.get('node_id')

        if not root_tier_id:
            return JsonResponse({'success': False, 'error': 'root_tier_id is required'}, status=400)
        if not node_key:
            return JsonResponse({'success': False, 'error': 'node_key is required'}, status=400)

        if node_type not in {'root', 'svem', 'cccp', 'dchd'}:
            node_type = node_key.split(':', 1)[0].strip().lower() if ':' in node_key else 'root'
        if node_type not in {'root', 'svem', 'cccp', 'dchd'}:
            return JsonResponse({'success': False, 'error': 'node_type must be one of root, svem, cccp, dchd'}, status=400)

        try:
            root_tier = GeneratedTier.objects.get(pk=int(root_tier_id))
        except (ValueError, TypeError, GeneratedTier.DoesNotExist):
            return JsonResponse({'success': False, 'error': f'GeneratedTier {root_tier_id} not found'}, status=404)

        try:
            normalized_node_id = int(node_id) if node_id is not None else None
        except (TypeError, ValueError):
            normalized_node_id = None

        defaults = {
            'node_type': node_type,
            'node_id': normalized_node_id,
            'timeline_lattice_index': data.get('timeline_lattice_index'),
            'timeline_label': str(data.get('timeline_label') or ''),
            'semantic_intent_id': str(data.get('semantic_intent_id') or ''),
            'talking_points': str(data.get('talking_points') or ''),
            'core_concept': str(data.get('core_concept') or ''),
            'synopsis': str(data.get('synopsis') or ''),
            'chapter_structure': str(data.get('chapter_structure') or ''),
            'dchd_atoms': data.get('dchd_atoms') if isinstance(data.get('dchd_atoms'), list) else [],
            'decision': str(data.get('decision') or 'draft').lower(),
            'updated_by': request.user,
        }

        if defaults['decision'] not in {'draft', 'approved', 'rejected'}:
            defaults['decision'] = 'draft'

        scaffold = StoryScaffold.objects.filter(root_tier=root_tier, node_key=node_key).first()
        created = scaffold is None
        if created:
            scaffold = StoryScaffold(
                root_tier=root_tier,
                node_key=node_key,
                created_by=request.user,
                scaffold_version=1,
                **defaults,
            )
        else:
            for field, value in defaults.items():
                setattr(scaffold, field, value)
            scaffold.scaffold_version = int(scaffold.scaffold_version or 1) + 1

        scaffold.save()

        return JsonResponse({
            'success': True,
            'created': created,
            'scaffold': {
                'id': scaffold.id,
                'root_tier_id': scaffold.root_tier_id,
                'node_key': scaffold.node_key,
                'node_type': scaffold.node_type,
                'node_id': scaffold.node_id,
                'timeline_lattice_index': scaffold.timeline_lattice_index,
                'timeline_label': scaffold.timeline_label,
                'semantic_intent_id': scaffold.semantic_intent_id,
                'talking_points': scaffold.talking_points,
                'core_concept': scaffold.core_concept,
                'synopsis': scaffold.synopsis,
                'chapter_structure': scaffold.chapter_structure,
                'dchd_atoms': scaffold.dchd_atoms,
                'scaffold_version': scaffold.scaffold_version,
                'decision': scaffold.decision,
                'updated_at': scaffold.updated_at.isoformat(),
            },
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
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
