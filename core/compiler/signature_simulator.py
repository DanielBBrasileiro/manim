def simulate_signature(plan: dict) -> dict:
    '''Constrói o preview virtual antes do render.'''
    interp = plan.get('interpretation', {})
    return {
        'structure': plan.get('archetype'),
        'motion': interp.get('motion_signature'),
        'density': 'high' if plan.get('entropy', {}).get('physical', 0) > 0.6 else 'low',
        'rhythm': interp.get('rhythm', 'regular')
    }
