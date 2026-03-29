def define_pacing(intent: str, archetype: str) -> str:
    '''Persona Kael: Temporização e Ritmo Master.'''
    intent_lower = intent.lower()
    if 'pacing slow' in intent_lower: return 'cinematic'
    if 'pacing fast' in intent_lower: return 'dynamic'
    return 'cinematic' if archetype == 'emergence' else 'dynamic'
