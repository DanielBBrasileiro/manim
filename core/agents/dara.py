def build_scene(plan: dict):
    '''Persona Dara: Engine Orchestrator.'''
    from core.tools.render_tool import render_pipeline
    return render_pipeline(plan)
