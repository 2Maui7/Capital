def user_profile(request):
    context = {
        'es_administrador': False,
        'es_empleado': False,
        'perfil_usuario': None,
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        perfil = request.user.perfil
        context['perfil_usuario'] = perfil
        context['es_administrador'] = perfil.es_administrador()
        context['es_empleado'] = perfil.es_empleado()
    
    return context
