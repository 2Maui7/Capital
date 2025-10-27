from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from functools import wraps


def rol_requerido(*roles):
    """
    Decorador para verificar que el usuario tenga uno de los roles especificados
    Uso: @rol_requerido('administrador', 'empleado')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            
            if hasattr(request.user, 'perfil'):
                if request.user.perfil.rol in roles:
                    return view_func(request, *args, **kwargs)
            
            # Si no tiene el rol requerido, redirigir al dashboard
            return redirect('core:dashboard')
        
        return _wrapped_view
    return decorator


def solo_administrador(view_func):
    """Decorador para vistas que solo puede acceder el administrador"""
    return rol_requerido('administrador')(view_func)


def solo_empleado(view_func):
    """Decorador para vistas que solo puede acceder el empleado"""
    return rol_requerido('empleado')(view_func)


def administrador_o_empleado(view_func):
    """Decorador para vistas que pueden acceder tanto administrador como empleado"""
    return rol_requerido('administrador', 'empleado')(view_func)
