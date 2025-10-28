from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Cliente, Producto, Inventario, Pedido, 
    Produccion, MovimientoInventario, PerfilUsuario,
    Proveedor, Compra, Trabajo
)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'email', 'es_frecuente', 'cantidad_pedidos', 'descuento_badge', 'fecha_registro']
    list_filter = ['es_frecuente', 'fecha_registro']
    search_fields = ['nombre', 'email', 'telefono', 'nit_ci']
    readonly_fields = ['cantidad_pedidos', 'fecha_registro']
    ordering = ['-fecha_registro']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'nit_ci', 'telefono', 'email', 'direccion')
        }),
        ('Estado del Cliente', {
            'fields': ('es_frecuente', 'cantidad_pedidos', 'fecha_registro')
        }),
    )
    
    def descuento_badge(self, obj):
        descuento = obj.obtener_descuento()
        if descuento > 0:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">{} %</span>',
                descuento
            )
        return format_html('<span style="color: #6c757d;">Sin descuento</span>')
    descuento_badge.short_description = 'Descuento'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'precio_unitario', 'activo', 'imagen_thumbnail']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['precio_unitario', 'activo']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'tipo', 'descripcion', 'precio_unitario')
        }),
        ('Multimedia', {
            'fields': ('imagen',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def imagen_thumbnail(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.imagen.url)
        return format_html('<span style="color: #6c757d;">Sin imagen</span>')
    imagen_thumbnail.short_description = 'Imagen'


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cantidad', 'unidad', 'estado_stock_badge', 'proveedor', 'precio_unitario', 'ultima_actualizacion']
    list_filter = ['unidad', 'proveedor']
    search_fields = ['nombre', 'descripcion', 'proveedor']
    readonly_fields = ['ultima_actualizacion']
    
    fieldsets = (
        ('Información del Material', {
            'fields': ('nombre', 'descripcion', 'unidad')
        }),
        ('Stock', {
            'fields': ('cantidad', 'cantidad_minima')
        }),
        ('Proveedor y Precio', {
            'fields': ('proveedor', 'precio_unitario')
        }),
        ('Actualización', {
            'fields': ('ultima_actualizacion',)
        }),
    )
    
    def estado_stock_badge(self, obj):
        estado = obj.estado_stock()
        colors = {
            'agotado': '#dc3545',
            'bajo': '#ffc107',
            'normal': '#28a745'
        }
        labels = {
            'agotado': 'AGOTADO',
            'bajo': 'BAJO STOCK',
            'normal': 'NORMAL'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors[estado],
            labels[estado]
        )
    estado_stock_badge.short_description = 'Estado'


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'inventario', 'cantidad', 'precio_total', 'estado_badge', 'fecha_creacion', 'fecha_entrega']
    list_filter = ['estado', 'fecha_creacion', 'fecha_entrega']
    search_fields = ['cliente__nombre', 'inventario__nombre', 'descripcion']
    readonly_fields = ['precio_total', 'fecha_creacion', 'usuario_registro']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('cliente', 'inventario', 'cantidad', 'descripcion')
        }),
        ('Precios', {
            'fields': ('precio_unitario', 'descuento', 'precio_total')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_entrega', 'fecha_entregado')
        }),
        ('Estado', {
            'fields': ('estado', 'usuario_registro')
        }),
    )
    
    def estado_badge(self, obj):
        colors = {
            'pendiente': '#6c757d',
            'en_proceso': '#17a2b8',
            'en_produccion': '#ffc107',
            'terminado': '#28a745',
            'entregado': '#007bff',
            'cancelado': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.estado, '#6c757d'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'estado_badge', 'empleado', 'tiempo_estimado', 'tiempo_real', 'fecha_inicio', 'fecha_finalizacion']
    list_filter = ['estado', 'empleado', 'fecha_inicio']
    search_fields = ['pedido__cliente__nombre', 'empleado__username', 'observaciones']
    readonly_fields = ['tiempo_real']
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Información de Producción', {
            'fields': ('pedido', 'estado', 'empleado')
        }),
        ('Tiempos', {
            'fields': ('tiempo_estimado', 'tiempo_real', 'fecha_inicio', 'fecha_finalizacion')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )
    
    def estado_badge(self, obj):
        colors = {
            'no_iniciado': '#6c757d',
            'en_proceso': '#ffc107',
            'pausado': '#fd7e14',
            'terminado': '#28a745'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.estado, '#6c757d'),
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['inventario', 'tipo_badge', 'cantidad', 'motivo', 'usuario', 'fecha']
    list_filter = ['tipo', 'fecha', 'inventario']
    search_fields = ['inventario__nombre', 'motivo', 'usuario__username']
    readonly_fields = ['fecha']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('inventario', 'tipo', 'cantidad', 'motivo')
        }),
        ('Relaciones', {
            'fields': ('produccion', 'usuario')
        }),
        ('Fecha', {
            'fields': ('fecha',)
        }),
    )
    
    def tipo_badge(self, obj):
        colors = {
            'entrada': '#28a745',
            'salida': '#dc3545',
            'ajuste': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.tipo, '#6c757d'),
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol_badge', 'telefono', 'activo', 'foto_thumbnail']
    list_filter = ['rol', 'activo']
    search_fields = ['user__username', 'user__email', 'telefono']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'rol')
        }),
        ('Información de Contacto', {
            'fields': ('telefono',)
        }),
        ('Multimedia', {
            'fields': ('foto',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def rol_badge(self, obj):
        colors = {
            'administrador': '#dc3545',
            'empleado': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.rol, '#6c757d'),
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'
    
    def foto_thumbnail(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.foto.url)
        return format_html('<span style="color: #6c757d;">Sin foto</span>')
    foto_thumbnail.short_description = 'Foto'
    

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'contacto', 'telefono', 'email', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'contacto', 'email', 'telefono']
    ordering = ['nombre']


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'proveedor', 'inventario', 'cantidad', 'precio_unitario', 'costo_total', 'estado', 'fecha_creacion', 'fecha_estimada', 'stock_aplicado']
    list_filter = ['estado', 'fecha_creacion', 'proveedor']
    search_fields = ['proveedor__nombre', 'inventario__nombre', 'observaciones']
    readonly_fields = ['costo_total', 'fecha_creacion', 'usuario_registro', 'stock_aplicado']
    date_hierarchy = 'fecha_creacion'

    fieldsets = (
        ('Información de la Compra', {
            'fields': ('proveedor', 'inventario', 'cantidad', 'precio_unitario', 'costo_total')
        }),
        ('Fechas y Estado', {
            'fields': ('estado', 'fecha_estimada', 'fecha_recepcion')
        }),
        ('Registro', {
            'fields': ('usuario_registro', 'stock_aplicado', 'observaciones')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'producto', 'cantidad', 'precio_total', 'estado', 'fecha_creacion', 'fecha_entrega']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['cliente__nombre', 'producto__nombre', 'descripcion']
    readonly_fields = ['precio_total', 'fecha_creacion', 'usuario_registro']
    date_hierarchy = 'fecha_creacion'

    fieldsets = (
        ('Información del Trabajo', {
            'fields': ('cliente', 'producto', 'cantidad', 'descripcion')
        }),
        ('Precios', {
            'fields': ('precio_unitario', 'descuento', 'precio_total')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_entrega', 'fecha_entregado')
        }),
        ('Estado', {
            'fields': ('estado', 'usuario_registro')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


admin.site.site_header = "Imprenta Capital - Administración"
admin.site.site_title = "Imprenta Capital"
admin.site.index_title = "Panel de Control"
