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
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder

from .models import Cliente, Producto, Pedido, Inventario, Produccion, MovimientoInventario, Proveedor, Compra
from .forms import (
    LoginForm, ClienteForm, ProductoForm, PedidoForm, 
    InventarioForm, ProduccionForm, MovimientoInventarioForm,
    ProveedorForm, CompraForm
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
    
    # Compras
    compras_pendientes = Compra.objects.filter(estado='pendiente').count()
    compras_ordenadas = Compra.objects.filter(estado='ordenado').count()
    compras_recibidas = Compra.objects.filter(estado='recibido').count()
    
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
        'compras_pendientes': compras_pendientes,
        'compras_ordenadas': compras_ordenadas,
        'compras_recibidas': compras_recibidas,
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
    """[Deshabilitado] Crear material solo vía Compras"""
    messages.warning(request, 'La creación de materiales ahora se realiza desde Compras.')
    return redirect('core:compras_lista')


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
        },
        'compras': {
            'total': Compra.objects.count(),
            'pendientes': Compra.objects.filter(estado='pendiente').count(),
            'ordenadas': Compra.objects.filter(estado='ordenado').count(),
            'recibidas': Compra.objects.filter(estado='recibido').count(),
        },
    }
    
    return Response(stats)


@login_required
@administrador_o_empleado
def compra_marcar_recibido(request, pk):
    """Marcar una compra como recibida y actualizar stock"""
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        compra.estado = 'recibido'
        if not compra.fecha_recepcion:
            compra.fecha_recepcion = timezone.now().date()
        compra.save()
        messages.success(request, f'Compra #{compra.id} marcada como recibida. Stock actualizado.')
    return redirect('core:compras_lista')


# ============= PROVEEDORES =============

@login_required
@administrador_o_empleado
def proveedores_lista(request):
    """Lista de proveedores"""
    query = request.GET.get('q', '')
    proveedores = Proveedor.objects.all()
    if query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=query) |
            Q(contacto__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query)
        )
    proveedores = proveedores.order_by('nombre')
    return render(request, 'proveedores/lista.html', {'proveedores': proveedores, 'query': query})


@login_required
@administrador_o_empleado
def proveedor_crear(request):
    """Crear nuevo proveedor"""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f'Proveedor {proveedor.nombre} creado exitosamente')
            return redirect('core:proveedores_lista')
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/formulario.html', {'form': form, 'accion': 'Crear'})


@login_required
@administrador_o_empleado
def proveedor_editar(request, pk):
    """Editar proveedor"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Proveedor {proveedor.nombre} actualizado exitosamente')
            return redirect('core:proveedores_lista')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'proveedores/formulario.html', {'form': form, 'accion': 'Editar', 'proveedor': proveedor})


@login_required
@solo_administrador
def proveedor_eliminar(request, pk):
    """Eliminar proveedor (solo administradores)"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor {nombre} eliminado exitosamente')
        return redirect('core:proveedores_lista')
    return render(request, 'proveedores/eliminar.html', {'proveedor': proveedor})


# ============= COMPRAS =============

@login_required
@administrador_o_empleado
def compras_lista(request):
    """Lista de compras a proveedores"""
    estado_filtro = request.GET.get('estado', '')
    query = request.GET.get('q', '')
    compras = Compra.objects.select_related('proveedor', 'inventario').all()
    if estado_filtro:
        compras = compras.filter(estado=estado_filtro)
    if query:
        compras = compras.filter(
            Q(proveedor__nombre__icontains=query) |
            Q(inventario__nombre__icontains=query) |
            Q(observaciones__icontains=query)
        )
    compras = compras.order_by('-fecha_creacion')
    return render(request, 'compras/lista.html', {
        'compras': compras,
        'estado_filtro': estado_filtro,
        'query': query
    })


@login_required
@administrador_o_empleado
def compra_crear(request):
    """Crear nueva compra"""
    if request.method == 'POST':
        # Detectar si se crea material nuevo primero
        material_nuevo = request.POST.get('material_nuevo') in ['on', 'true', '1']
        if material_nuevo:
            nombre = request.POST.get('nombre_material')
            if not nombre:
                messages.error(request, 'Debes ingresar el nombre del nuevo material.')
                # Mostrar formulario nuevamente
                form = CompraForm(request.POST)
                return render(request, 'compras/formulario.html', {
                    'form': form,
                    'accion': 'Crear',
                    'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
                    'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
                })

            descripcion = request.POST.get('descripcion_material') or ''
            unidad = request.POST.get('unidad_material') or 'unidad'
            cantidad_minima = int(request.POST.get('cantidad_minima_material') or 10)
            proveedor_txt = request.POST.get('proveedor_material') or ''
            precio_unit_material = Decimal(request.POST.get('precio_unitario_material') or '0')

            # Crear inventario primero para poder validar el formulario con referencia válida
            inv = Inventario.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                unidad=unidad,
                cantidad=0,
                cantidad_minima=cantidad_minima,
                proveedor=proveedor_txt,
                precio_unitario=precio_unit_material,
            )
            # Inyectar el id de inventario creado en los datos del formulario
            post_data = request.POST.copy()
            post_data['inventario'] = str(inv.id)
            form = CompraForm(post_data)
            if form.is_valid():
                compra = form.save(commit=False)
                compra.usuario_registro = request.user
                compra.save()
                messages.success(request, f'Compra #{compra.id} creada exitosamente')
                return redirect('core:compras_lista')
            else:
                # Si el formulario no es válido, eliminar el inventario creado para evitar huérfanos
                inv.delete()
                return render(request, 'compras/formulario.html', {
                    'form': form,
                    'accion': 'Crear',
                    'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
                    'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
                })
        else:
            form = CompraForm(request.POST)
            if form.is_valid():
                compra = form.save(commit=False)
                compra.usuario_registro = request.user
                compra.save()
                messages.success(request, f'Compra #{compra.id} creada exitosamente')
                return redirect('core:compras_lista')
    else:
        form = CompraForm()

    return render(request, 'compras/formulario.html', {
        'form': form,
        'accion': 'Crear',
        'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
        'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
    })


@login_required
@administrador_o_empleado
def compra_editar(request, pk):
    """Editar compra"""
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        # Permitir crear material nuevo también al editar
        material_nuevo = request.POST.get('material_nuevo') in ['on', 'true', '1']
        if material_nuevo:
            nombre = request.POST.get('nombre_material')
            if not nombre:
                form = CompraForm(request.POST, instance=compra)
                messages.error(request, 'Debes ingresar el nombre del nuevo material.')
                return render(request, 'compras/formulario.html', {
                    'form': form,
                    'accion': 'Editar',
                    'compra': compra,
                    'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
                    'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
                })

            descripcion = request.POST.get('descripcion_material') or ''
            unidad = request.POST.get('unidad_material') or 'unidad'
            cantidad_minima = int(request.POST.get('cantidad_minima_material') or 10)
            proveedor_txt = request.POST.get('proveedor_material') or ''
            precio_unit_material = Decimal(request.POST.get('precio_unitario_material') or '0')

            inv = Inventario.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                unidad=unidad,
                cantidad=0,
                cantidad_minima=cantidad_minima,
                proveedor=proveedor_txt,
                precio_unitario=precio_unit_material,
            )
            post_data = request.POST.copy()
            post_data['inventario'] = str(inv.id)
            form = CompraForm(post_data, instance=compra)
            if form.is_valid():
                compra = form.save(commit=False)
                compra.save()
                messages.success(request, f'Compra #{compra.id} actualizada exitosamente')
                return redirect('core:compras_lista')
            else:
                inv.delete()
                return render(request, 'compras/formulario.html', {
                    'form': form,
                    'accion': 'Editar',
                    'compra': compra,
                    'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
                    'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
                })
        else:
            form = CompraForm(request.POST, instance=compra)
            if form.is_valid():
                compra = form.save(commit=False)
                compra.save()
                messages.success(request, f'Compra #{compra.id} actualizada exitosamente')
                return redirect('core:compras_lista')
    else:
        form = CompraForm(instance=compra)
    return render(request, 'compras/formulario.html', {
        'form': form,
        'accion': 'Editar',
        'compra': compra,
        'inventarios_json': json.dumps(list(Inventario.objects.values('id', 'precio_unitario', 'proveedor')), cls=DjangoJSONEncoder),
        'proveedores_nombres': list(Proveedor.objects.filter(activo=True).order_by('nombre').values_list('nombre', flat=True))
    })


@login_required
@solo_administrador
def compra_eliminar(request, pk):
    """Eliminar compra (solo administradores)"""
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        compra_id = compra.id
        compra.delete()
        messages.success(request, f'Compra #{compra_id} eliminada exitosamente')
        return redirect('core:compras_lista')
    return render(request, 'compras/eliminar.html', {'compra': compra})


@login_required
@administrador_o_empleado
def compras_reportes(request):
    """Página de reportes de compras con filtros y exporte a PDF"""
    from django.utils.dateparse import parse_date
    from django.http import HttpResponse
    from io import BytesIO

    qs = Compra.objects.select_related('proveedor', 'inventario').all()

    # Filtros
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    estado = request.GET.get('estado')

    if start_date:
        sd = parse_date(start_date)
        if sd:
            qs = qs.filter(fecha_creacion__gte=sd)
    if end_date:
        ed = parse_date(end_date)
        if ed:
            qs = qs.filter(fecha_creacion__lte=ed)
    if estado:
        qs = qs.filter(estado=estado)

    # Resumen
    resumen = {
        'total': qs.count(),
        'pendientes': qs.filter(estado='pendiente').count(),
        'ordenadas': qs.filter(estado='ordenado').count(),
        'recibidas': qs.filter(estado='recibido').count(),
        'canceladas': qs.filter(estado='cancelado').count(),
        'costo_total': qs.aggregate(total=Sum('costo_total'))['total'] or Decimal('0'),
    }

    # Exportar solo PDF
    export = request.GET.get('export')
    if export == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
        except Exception:
            messages.error(request, 'Exportación a PDF no disponible. Instala la dependencia reportlab.')
        else:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
            elements = []
            styles = getSampleStyleSheet()

            # Título y filtros
            title = Paragraph('Reporte de Compras', styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 8))
            filtros_txt = f"Rango: {start_date or '-'} a {end_date or '-'} | Estado: {estado or 'Todos'}"
            elements.append(Paragraph(filtros_txt, styles['Normal']))
            elements.append(Spacer(1, 12))

            # Resumen
            res_data = [
                ['Total', 'Pendientes', 'Ordenadas', 'Recibidas', 'Canceladas', 'Costo Total (Bs.)'],
                [
                    str(resumen['total']),
                    str(resumen['pendientes']),
                    str(resumen['ordenadas']),
                    str(resumen['recibidas']),
                    str(resumen['canceladas']),
                    f"{resumen['costo_total']}",
                ]
            ]
            res_table = Table(res_data)
            res_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f3f5')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#495057')),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ]))
            elements.append(res_table)
            elements.append(Spacer(1, 16))

            # Tabla de compras
            headers = ['ID', 'Proveedor', 'Material', 'Cant.', 'Unit.', 'Total', 'Estado', 'F. Creación', 'F. Recepción']
            data = [headers]
            for c in qs.order_by('-fecha_creacion'):
                data.append([
                    str(c.id),
                    c.proveedor.nombre if c.proveedor else '',
                    c.inventario.nombre if c.inventario else '',
                    str(c.cantidad),
                    f"{c.precio_unitario}",
                    f"{c.costo_total}",
                    c.get_estado_display(),
                    c.fecha_creacion.strftime('%Y-%m-%d') if c.fecha_creacion else '',
                    c.fecha_recepcion.strftime('%Y-%m-%d') if c.fecha_recepcion else '',
                ])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9ecef')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#212529')),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(table)

            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            suffix = ''
            if start_date or end_date:
                suffix = f"_{start_date or ''}_a_{end_date or ''}"
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="compras{suffix}.pdf"'
            return response

    context = {
        'resumen': resumen,
        'start_date': start_date or '',
        'end_date': end_date or '',
        'estado': estado or '',
    }
    return render(request, 'compras/reportes.html', context)
