from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder

from .models import Cliente, Producto, Pedido, Inventario, Produccion, MovimientoInventario, Proveedor, Compra, Trabajo
from .forms import (
    LoginForm, ClienteForm, PedidoForm,
    ProveedorForm, CompraForm, TrabajoForm
)
from .decorators import administrador_o_empleado, solo_administrador

def user_login(request):
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
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('core:login')


@login_required
@administrador_o_empleado
def dashboard(request):
    
    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.filter(activo=True).count()
    
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_en_produccion = Pedido.objects.filter(estado='en_produccion').count()
    pedidos_hoy = Pedido.objects.filter(fecha_creacion=timezone.now().date()).count()
    
    trabajos_pendientes = Trabajo.objects.filter(estado='pendiente').count()
    trabajos_en_produccion = Trabajo.objects.filter(estado='en_produccion').count()
    trabajos_hoy = Trabajo.objects.filter(fecha_creacion=timezone.now().date()).count()
    
    compras_pendientes = Compra.objects.filter(estado='pendiente').count()
    compras_ordenadas = Compra.objects.filter(estado='ordenado').count()
    compras_recibidas = Compra.objects.filter(estado='recibido').count()
    
    from django.db.models import F
    materiales_bajo_stock = Inventario.objects.filter(
        cantidad__lte=F('cantidad_minima')
    ).count()
    
    produccion_activa = Produccion.objects.filter(estado='en_proceso').count()
    
    ultimos_pedidos = Pedido.objects.select_related('cliente', 'inventario').order_by('-fecha_creacion')[:5]
    ultimos_trabajos = Trabajo.objects.select_related('cliente', 'producto').order_by('-fecha_creacion')[:5]
    
    materiales_criticos = Inventario.objects.filter(
        cantidad__lte=F('cantidad_minima')
    ).order_by('cantidad')[:5]
    
    context = {
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_en_produccion': pedidos_en_produccion,
        'pedidos_hoy': pedidos_hoy,
        'trabajos_pendientes': trabajos_pendientes,
        'trabajos_en_produccion': trabajos_en_produccion,
        'trabajos_hoy': trabajos_hoy,
        'compras_pendientes': compras_pendientes,
        'compras_ordenadas': compras_ordenadas,
        'compras_recibidas': compras_recibidas,
        'materiales_bajo_stock': materiales_bajo_stock,
        'produccion_activa': produccion_activa,
        'ultimos_pedidos': ultimos_pedidos,
        'ultimos_trabajos': ultimos_trabajos,
        'materiales_criticos': materiales_criticos,
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
@administrador_o_empleado
def clientes_lista(request):
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
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f'Cliente {nombre} eliminado exitosamente')
        return redirect('core:clientes_lista')
    
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})


@login_required
@administrador_o_empleado
def pedidos_lista(request):
    estado_filtro = request.GET.get('estado', '')
    query = request.GET.get('q', '')
    
    pedidos = Pedido.objects.select_related('cliente', 'inventario').all()
    
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)
    
    if query:
        pedidos = pedidos.filter(
            Q(cliente__nombre__icontains=query) |
            Q(inventario__nombre__icontains=query) |
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
def trabajos_lista(request):
    estado_filtro = request.GET.get('estado', '')
    query = request.GET.get('q', '')

    trabajos = Trabajo.objects.select_related('cliente', 'producto').all()

    if estado_filtro:
        trabajos = trabajos.filter(estado=estado_filtro)

    if query:
        trabajos = trabajos.filter(
            Q(cliente__nombre__icontains=query) |
            Q(producto__nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )

    trabajos = trabajos.order_by('-fecha_creacion')

    return render(request, 'trabajos/lista.html', {
        'trabajos': trabajos,
        'estado_filtro': estado_filtro,
        'query': query,
    })


@login_required
@administrador_o_empleado
def trabajo_crear(request):
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.usuario_registro = request.user
            trabajo.save()
            messages.success(request, f'Trabajo #{trabajo.id} creado exitosamente')
            return redirect('core:trabajos_lista')
    else:
        form = TrabajoForm()

    productos_data = list(Producto.objects.filter(activo=True).values('id', 'precio_unitario'))
    productos_json = json.dumps(productos_data, cls=DjangoJSONEncoder)
    productos_count = Producto.objects.filter(activo=True).count()

    return render(request, 'trabajos/formulario.html', {
        'form': form,
        'accion': 'Crear',
        'productos_data_json': productos_json,
        'productos_count': productos_count,
    })


@login_required
@administrador_o_empleado
def trabajo_editar(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)

    if request.method == 'POST':
        form = TrabajoForm(request.POST, instance=trabajo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Trabajo #{trabajo.id} actualizado exitosamente')
            return redirect('core:trabajo_detalle', pk=trabajo.pk)
    else:
        form = TrabajoForm(instance=trabajo)

    productos_data = list(Producto.objects.filter(activo=True).values('id', 'precio_unitario'))
    productos_json = json.dumps(productos_data, cls=DjangoJSONEncoder)
    productos_count = Producto.objects.filter(activo=True).count()

    return render(request, 'trabajos/formulario.html', {
        'form': form,
        'accion': 'Editar',
        'trabajo': trabajo,
        'productos_data_json': productos_json,
        'productos_count': productos_count,
    })


@login_required
@administrador_o_empleado
def trabajo_detalle(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    return render(request, 'trabajos/detalle.html', {'trabajo': trabajo})


@login_required
@solo_administrador
def trabajo_eliminar(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    if request.method == 'POST':
        trabajo_id = trabajo.id
        trabajo.delete()
        messages.success(request, f'Trabajo #{trabajo_id} eliminado exitosamente')
        return redirect('core:trabajos_lista')
    return render(request, 'trabajos/eliminar.html', {'trabajo': trabajo})


@login_required
@administrador_o_empleado
def pedido_crear(request):
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

    from django.core.serializers.json import DjangoJSONEncoder
    import json
    qs_inv = Inventario.objects.filter(cantidad__gt=0)
    productos_data = list(qs_inv.values('id', 'precio_unitario'))
    productos_json = json.dumps(productos_data, cls=DjangoJSONEncoder)
    productos_count = qs_inv.count()
    
    return render(request, 'pedidos/formulario.html', {
        'form': form,
        'accion': 'Crear',
        'productos_data_json': productos_json,
        'productos_count': productos_count,
    })


@login_required
@administrador_o_empleado
def pedido_editar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pedido #{pedido.id} actualizado exitosamente')
            return redirect('core:pedido_detalle', pk=pedido.pk)
    else:
        form = PedidoForm(instance=pedido)

    from django.core.serializers.json import DjangoJSONEncoder
    import json
    qs_inv = Inventario.objects.filter(Q(cantidad__gt=0) | Q(pk=pedido.inventario_id))
    productos_data = list(qs_inv.values('id', 'precio_unitario'))
    productos_json = json.dumps(productos_data, cls=DjangoJSONEncoder)
    productos_count = qs_inv.count()

    return render(request, 'pedidos/formulario.html', {
        'form': form,
        'accion': 'Editar',
        'pedido': pedido,
        'productos_data_json': productos_json,
        'productos_count': productos_count,
    })


@login_required
@administrador_o_empleado
def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    return render(request, 'pedidos/detalle.html', {'pedido': pedido})


@login_required
@solo_administrador
def pedido_eliminar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        pedido_id = pedido.id
        pedido.delete()
        messages.success(request, f'Pedido #{pedido_id} eliminado exitosamente')
        return redirect('core:pedidos_lista')
    
    return render(request, 'pedidos/eliminar.html', {'pedido': pedido})


@login_required
@administrador_o_empleado
def inventario_lista(request):
    ocultar_agotados = request.GET.get('ocultar_agotados') in ['1', 'true', 'on']
    qs = Inventario.objects.all()
    if ocultar_agotados:
        qs = qs.filter(cantidad__gt=0)
    inventario = qs.order_by('nombre')
    return render(request, 'inventario/lista.html', {
        'inventario': inventario,
        'ocultar_agotados': ocultar_agotados,
    })


 
@login_required
@administrador_o_empleado
def produccion_panel(request):
    producciones = Produccion.objects.select_related('pedido__cliente', 'empleado').exclude(
        estado='terminado'
    ).order_by('-fecha_inicio')
    
    return render(request, 'produccion/panel.html', {'producciones': producciones})


@login_required
@administrador_o_empleado
def produccion_iniciar(request, pk):
    produccion = get_object_or_404(Produccion, pk=pk)
    
    if request.method == 'POST':
        produccion.iniciar_produccion()
        messages.success(request, f'Producción del pedido #{produccion.pedido.id} iniciada')
        return redirect('core:produccion_panel')
    
    return render(request, 'produccion/iniciar.html', {'produccion': produccion})


@api_view(['GET'])
def api_status(request):
    return Response({
        'status': 'online',
        'message': 'API de Imprenta Capital funcionando correctamente',
        'version': '1.0.0'
    })


@api_view(['GET'])
@login_required
def api_dashboard_stats(request):
    from django.db.models import F
    
    stats = {
        'pedidos': {
            'total': Pedido.objects.count(),
            'pendientes': Pedido.objects.filter(estado='pendiente').count(),
            'en_produccion': Pedido.objects.filter(estado='en_produccion').count(),
            'terminados': Pedido.objects.filter(estado='terminado').count(),
        },
        'trabajos': {
            'total': Trabajo.objects.count(),
            'pendientes': Trabajo.objects.filter(estado='pendiente').count(),
            'en_produccion': Trabajo.objects.filter(estado='en_produccion').count(),
            'terminados': Trabajo.objects.filter(estado='terminado').count(),
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
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        from django.utils import timezone
        compra.estado = 'recibido'
        if not compra.fecha_recepcion:
            compra.fecha_recepcion = timezone.now().date()
        compra.save()
        messages.success(request, f'Compra #{compra.id} marcada como recibida. Stock actualizado.')
    return redirect('core:compras_lista')


@login_required
@administrador_o_empleado
def proveedores_lista(request):
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
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor {nombre} eliminado exitosamente')
        return redirect('core:proveedores_lista')
    return render(request, 'proveedores/eliminar.html', {'proveedor': proveedor})


@login_required
@administrador_o_empleado
def compras_lista(request):
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
    if request.method == 'POST':
        material_nuevo = request.POST.get('material_nuevo') in ['on', 'true', '1']
        if material_nuevo:
            nombre = request.POST.get('nombre_material')
            if not nombre:
                messages.error(request, 'Debes ingresar el nombre del nuevo material.')
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
            form = CompraForm(post_data)
            if form.is_valid():
                compra = form.save(commit=False)
                compra.usuario_registro = request.user
                compra.save()
                messages.success(request, f'Compra #{compra.id} creada exitosamente')
                return redirect('core:compras_lista')
            else:
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
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
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
    from django.utils.dateparse import parse_date
    from django.http import HttpResponse
    from io import BytesIO

    qs = Compra.objects.select_related('proveedor', 'inventario').all()

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

    resumen = {
        'total': qs.count(),
        'pendientes': qs.filter(estado='pendiente').count(),
        'ordenadas': qs.filter(estado='ordenado').count(),
        'recibidas': qs.filter(estado='recibido').count(),
        'canceladas': qs.filter(estado='cancelado').count(),
        'costo_total': qs.aggregate(total=Sum('costo_total'))['total'] or Decimal('0'),
    }

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
            
            title = Paragraph('Reporte de Compras', styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 8))
            filtros_txt = f"Rango: {start_date or '-'} a {end_date or '-'} | Estado: {estado or 'Todos'}"
            elements.append(Paragraph(filtros_txt, styles['Normal']))
            elements.append(Spacer(1, 12))
            
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
