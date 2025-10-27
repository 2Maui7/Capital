from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Cliente, Producto, Pedido, Inventario, Produccion, MovimientoInventario
from .forms import (
    LoginForm, ClienteForm, ProductoForm, PedidoForm, 
    InventarioForm, ProduccionForm, MovimientoInventarioForm
)
from .decorators import administrador_o_empleado, solo_administrador


# ============= VISTAS DE AUTENTICACIÓN =============

def user_login(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.first_name or user.username}!')
                return redirect('core:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


@login_required
def user_logout(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('core:login')


# ============= DASHBOARD Y VISTAS PRINCIPALES =============

@login_required
@administrador_o_empleado
def dashboard(request):
    """Dashboard principal con estadísticas"""
    # Estadísticas generales
    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.filter(activo=True).count()
    
    # Pedidos
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_en_produccion = Pedido.objects.filter(estado='en_produccion').count()
    pedidos_hoy = Pedido.objects.filter(fecha_creacion=timezone.now().date()).count()
    
    # Inventario con alertas
    from django.db.models import F
    materiales_bajo_stock = Inventario.objects.filter(
        cantidad__lte=F('cantidad_minima')
    ).count()
    
    # Producción
    produccion_activa = Produccion.objects.filter(estado='en_proceso').count()
    
    # Últimos pedidos
    ultimos_pedidos = Pedido.objects.select_related('cliente', 'producto').order_by('-fecha_creacion')[:5]
    
    # Materiales críticos
    materiales_criticos = Inventario.objects.filter(
        cantidad__lte=F('cantidad_minima')
    ).order_by('cantidad')[:5]
    
    context = {
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_en_produccion': pedidos_en_produccion,
        'pedidos_hoy': pedidos_hoy,
        'materiales_bajo_stock': materiales_bajo_stock,
        'produccion_activa': produccion_activa,
        'ultimos_pedidos': ultimos_pedidos,
        'materiales_criticos': materiales_criticos,
    }
    
    return render(request, 'dashboard/index.html', context)


# ============= GESTIÓN DE CLIENTES =============

@login_required
@administrador_o_empleado
def clientes_lista(request):
    """Lista de clientes"""
    query = request.GET.get('q', '')
    clientes = Cliente.objects.all()
    
    if query:
        clientes = clientes.filter(
            Q(nombre__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query) |
            Q(nit_ci__icontains=query)
        )
    
    clientes = clientes.order_by('-fecha_registro')
    
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'query': query})


@login_required
@administrador_o_empleado
def cliente_crear(request):
    """Crear nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nombre} creado exitosamente')
            return redirect('core:clientes_lista')
    else:
        form = ClienteForm()
    
    return render(request, 'clientes/formulario.html', {'form': form, 'accion': 'Crear'})


@login_required
@administrador_o_empleado
def cliente_editar(request, pk):
    """Editar cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Cliente {cliente.nombre} actualizado exitosamente')
            return redirect('core:clientes_lista')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'clientes/formulario.html', {'form': form, 'accion': 'Editar', 'cliente': cliente})


@login_required
@solo_administrador
def cliente_eliminar(request, pk):
    """Eliminar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f'Cliente {nombre} eliminado exitosamente')
        return redirect('core:clientes_lista')
    
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})


# ============= GESTIÓN DE PEDIDOS =============

@login_required
@administrador_o_empleado
def pedidos_lista(request):
    """Lista de pedidos"""
    estado_filtro = request.GET.get('estado', '')
    query = request.GET.get('q', '')
    
    pedidos = Pedido.objects.select_related('cliente', 'producto').all()
    
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)
    
    if query:
        pedidos = pedidos.filter(
            Q(cliente__nombre__icontains=query) |
            Q(producto__nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    pedidos = pedidos.order_by('-fecha_creacion')
    
    return render(request, 'pedidos/lista.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'query': query
    })


@login_required
@administrador_o_empleado
def pedido_crear(request):
    """Crear nuevo pedido"""
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.usuario_registro = request.user
            pedido.save()
            messages.success(request, f'Pedido #{pedido.id} creado exitosamente')
            return redirect('core:pedidos_lista')
    else:
        form = PedidoForm()
    
    return render(request, 'pedidos/formulario.html', {'form': form, 'accion': 'Crear'})


@login_required
@administrador_o_empleado
def pedido_editar(request, pk):
    """Editar pedido existente"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pedido #{pedido.id} actualizado exitosamente')
            return redirect('core:pedido_detalle', pk=pedido.pk)
    else:
        form = PedidoForm(instance=pedido)
    
    return render(request, 'pedidos/formulario.html', {
        'form': form, 
        'accion': 'Editar',
        'pedido': pedido
    })


@login_required
@administrador_o_empleado
def pedido_detalle(request, pk):
    """Ver detalle del pedido"""
    pedido = get_object_or_404(Pedido, pk=pk)
    return render(request, 'pedidos/detalle.html', {'pedido': pedido})


@login_required
@solo_administrador
def pedido_eliminar(request, pk):
    """Eliminar pedido (solo administradores)"""
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        pedido_id = pedido.id
        pedido.delete()
        messages.success(request, f'Pedido #{pedido_id} eliminado exitosamente')
        return redirect('core:pedidos_lista')
    
    return render(request, 'pedidos/eliminar.html', {'pedido': pedido})


# ============= GESTIÓN DE INVENTARIO =============

@login_required
@administrador_o_empleado
def inventario_lista(request):
    """Lista de materiales en inventario"""
    inventario = Inventario.objects.all().order_by('nombre')
    return render(request, 'inventario/lista.html', {'inventario': inventario})


@login_required
@administrador_o_empleado
def inventario_crear(request):
    """Crear nuevo material en inventario"""
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material {material.nombre} agregado al inventario')
            return redirect('core:inventario_lista')
    else:
        form = InventarioForm()
    
    return render(request, 'inventario/formulario.html', {'form': form, 'accion': 'Agregar'})


# ============= PANEL DE PRODUCCIÓN =============

@login_required
@administrador_o_empleado
def produccion_panel(request):
    """Panel de producción"""
    producciones = Produccion.objects.select_related('pedido__cliente', 'empleado').exclude(
        estado='terminado'
    ).order_by('-fecha_inicio')
    
    return render(request, 'produccion/panel.html', {'producciones': producciones})


@login_required
@administrador_o_empleado
def produccion_iniciar(request, pk):
    """Iniciar producción"""
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST':
        produccion.iniciar_produccion()
        messages.success(request, f'Producción del pedido #{produccion.pedido.id} iniciada')
        return redirect('core:produccion_panel')
    
    return render(request, 'produccion/iniciar.html', {'produccion': produccion})


# ============= API ENDPOINTS =============

@api_view(['GET'])
def api_status(request):
    """Endpoint para verificar el estado de la API"""
    return Response({
        'status': 'online',
        'message': 'API de Imprenta Capital funcionando correctamente',
        'version': '1.0.0'
    })


@api_view(['GET'])
@login_required
def api_dashboard_stats(request):
    """API para obtener estadísticas del dashboard"""
    from django.db.models import F
    
    stats = {
        'pedidos': {
            'total': Pedido.objects.count(),
            'pendientes': Pedido.objects.filter(estado='pendiente').count(),
            'en_produccion': Pedido.objects.filter(estado='en_produccion').count(),
            'terminados': Pedido.objects.filter(estado='terminado').count(),
        },
        'inventario': {
            'total_materiales': Inventario.objects.count(),
            'bajo_stock': Inventario.objects.filter(cantidad__lte=F('cantidad_minima')).count(),
        },
        'clientes': {
            'total': Cliente.objects.count(),
            'frecuentes': Cliente.objects.filter(es_frecuente=True).count(),
        }
    }
    
    return Response(stats)
