from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
class Cliente(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre completo")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Correo electrónico")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    nit_ci = models.CharField(max_length=20, blank=True, null=True, verbose_name="NIT/CI")
    es_frecuente = models.BooleanField(default=False, verbose_name="Cliente frecuente")
    cantidad_pedidos = models.IntegerField(default=0, verbose_name="Cantidad de pedidos")
    fecha_registro = models.DateField(auto_now_add=True, verbose_name="Fecha de registro")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return self.nombre
    
    def actualizar_frecuencia(self):
        umbral = getattr(settings, 'CLIENTE_FRECUENTE_UMBRAL', 5)
        es_frecuente_nuevo = self.cantidad_pedidos >= umbral
        if self.es_frecuente != es_frecuente_nuevo:
            self.es_frecuente = es_frecuente_nuevo
            self.save(update_fields=['es_frecuente'])
    
    def obtener_descuento(self):
        return 10 if self.es_frecuente else 0


class Producto(models.Model):
    TIPOS_PRODUCTO = [
        ('tarjetas', 'Tarjetas de presentación'),
        ('volantes', 'Volantes'),
        ('banners', 'Banners'),
        ('folletos', 'Folletos'),
        ('libros', 'Libros'),
        ('revistas', 'Revistas'),
        ('otros', 'Otros'),
    ]
    
    nombre = models.CharField(max_length=255, verbose_name="Nombre del producto")
    tipo = models.CharField(max_length=100, choices=TIPOS_PRODUCTO, verbose_name="Tipo de producto")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio unitario"
    )
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True, verbose_name="Imagen")
    activo = models.BooleanField(default=True, verbose_name="Producto activo")
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_display()}"


class Inventario(models.Model):
    UNIDADES = [
        ('unidad', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('litro', 'Litro'),
        ('resma', 'Resma'),
        ('caja', 'Caja'),
    ]
    
    nombre = models.CharField(max_length=255, verbose_name="Nombre del material")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    cantidad = models.IntegerField(default=0, verbose_name="Cantidad disponible")
    cantidad_minima = models.IntegerField(default=10, verbose_name="Cantidad mínima")
    unidad = models.CharField(max_length=50, choices=UNIDADES, default='unidad', verbose_name="Unidad de medida")
    proveedor = models.CharField(max_length=255, blank=True, null=True, verbose_name="Proveedor")
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Precio unitario"
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    class Meta:
        verbose_name = "Material de Inventario"
        verbose_name_plural = "Inventario"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.cantidad} {self.unidad})"
    
    def necesita_reposicion(self):
        return self.cantidad <= self.cantidad_minima
    
    def estado_stock(self):
        if self.cantidad == 0:
            return 'agotado'
        elif self.necesita_reposicion():
            return 'bajo'
        else:
            return 'normal'


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('en_produccion', 'En Producción'),
        ('terminado', 'Terminado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos', verbose_name="Cliente")
    inventario = models.ForeignKey(Inventario, on_delete=models.SET_NULL, null=True, related_name='pedidos', verbose_name="Material")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    descripcion = models.TextField(verbose_name="Descripción del pedido")
    
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Descuento (%)")
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio total")
    
    estado = models.CharField(max_length=50, choices=ESTADOS, default='pendiente', verbose_name="Estado")
    
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_entrega = models.DateField(verbose_name="Fecha de entrega estimada")
    fecha_entregado = models.DateField(blank=True, null=True, verbose_name="Fecha de entrega real")
    
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pedidos_registrados', verbose_name="Registrado por")
    
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        mat = getattr(self, 'inventario', None)
        mat_name = mat.nombre if mat else 'Sin material'
        return f"Pedido #{self.id} - {self.cliente.nombre} - {mat_name} - {self.estado}"
    
    def save(self, *args, **kwargs):
        subtotal = self.precio_unitario * self.cantidad
        descuento_monto = subtotal * (self.descuento / 100)
        self.precio_total = subtotal - descuento_monto
        
        super().save(*args, **kwargs)

        self.cliente.cantidad_pedidos = self.cliente.pedidos.filter(estado='entregado').count()
        self.cliente.save(update_fields=['cantidad_pedidos'])
        self.cliente.actualizar_frecuencia()


class Produccion(models.Model):
    ESTADOS_PRODUCCION = [
        ('no_iniciado', 'No Iniciado'),
        ('en_proceso', 'En Proceso'),
        ('pausado', 'Pausado'),
        ('terminado', 'Terminado'),
    ]
    
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='produccion', verbose_name="Pedido")
    estado = models.CharField(max_length=50, choices=ESTADOS_PRODUCCION, default='no_iniciado', verbose_name="Estado de producción")
    empleado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='producciones', verbose_name="Empleado asignado")
    
    tiempo_estimado = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Tiempo estimado (horas)")
    tiempo_real = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True, verbose_name="Tiempo real (horas)")
    
    fecha_inicio = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de inicio")
    fecha_finalizacion = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de finalización")
    
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        verbose_name = "Producción"
        verbose_name_plural = "Producciones"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Producción de {self.pedido}"
    
    def iniciar_produccion(self):
        from django.utils import timezone
        self.estado = 'en_proceso'
        self.fecha_inicio = timezone.now()
        self.save()
        
        self.pedido.estado = 'en_produccion'
        self.pedido.save()
    
    def finalizar_produccion(self):
        from django.utils import timezone
        self.estado = 'terminado'
        self.fecha_finalizacion = timezone.now()
        
        if self.fecha_inicio:
            delta = self.fecha_finalizacion - self.fecha_inicio
            self.tiempo_real = round(delta.total_seconds() / 3600, 2)
        
        self.save()
        
        self.pedido.estado = 'terminado'
        self.pedido.save()


class MovimientoInventario(models.Model):
    TIPOS_MOVIMIENTO = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos', verbose_name="Material")
    tipo = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO, verbose_name="Tipo de movimiento")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    motivo = models.CharField(max_length=255, verbose_name="Motivo")
    produccion = models.ForeignKey(Produccion, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_inventario', verbose_name="Relacionado a producción")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.inventario.nombre} ({self.cantidad})"
    
    def save(self, *args, **kwargs):
        if self.tipo == 'entrada':
            self.inventario.cantidad += self.cantidad
        elif self.tipo == 'salida':
            self.inventario.cantidad -= self.cantidad
        elif self.tipo == 'ajuste':
            self.inventario.cantidad = self.cantidad
        
        self.inventario.save()
        super().save(*args, **kwargs)


class PerfilUsuario(models.Model):
    ROLES = [
        ('administrador', 'Administrador'),
        ('empleado', 'Personal de Producción'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil', verbose_name="Usuario")
    rol = models.CharField(max_length=20, choices=ROLES, default='empleado', verbose_name="Rol")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True, verbose_name="Foto de perfil")
    activo = models.BooleanField(default=True, verbose_name="Usuario activo")
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
    
    def es_administrador(self):
        return self.rol == 'administrador'
    
    def es_empleado(self):
        return self.rol == 'empleado'


class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del proveedor")
    contacto = models.CharField(max_length=255, blank=True, null=True, verbose_name="Persona de contacto")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Correo electrónico")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    activo = models.BooleanField(default=True, verbose_name="Proveedor activo")
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de registro")

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    ESTADOS_COMPRA = [
        ('pendiente', 'Pendiente'),
        ('ordenado', 'Ordenado'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras', verbose_name="Proveedor")
    inventario = models.ForeignKey(Inventario, on_delete=models.PROTECT, related_name='compras', verbose_name="Material")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Costo unitario")
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo total")

    estado = models.CharField(max_length=20, choices=ESTADOS_COMPRA, default='pendiente', verbose_name="Estado")
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_estimada = models.DateField(blank=True, null=True, verbose_name="Fecha estimada de recepción")
    fecha_recepcion = models.DateField(blank=True, null=True, verbose_name="Fecha real de recepción")

    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='compras_registradas', verbose_name="Registrado por")

    stock_aplicado = models.BooleanField(default=False, verbose_name="Stock aplicado")

    class Meta:
        verbose_name = "Compra a Proveedor"
        verbose_name_plural = "Compras a Proveedores"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor.nombre} - {self.inventario.nombre}"

    def save(self, *args, **kwargs):
        self.costo_total = (self.precio_unitario or Decimal('0')) * (self.cantidad or 0)
        estado_anterior = None
        if self.pk:
            try:
                estado_anterior = Compra.objects.only('estado', 'stock_aplicado').get(pk=self.pk).estado
            except Compra.DoesNotExist:
                estado_anterior = None

        super().save(*args, **kwargs)
        if self.estado == 'recibido' and not self.stock_aplicado:
            movimiento = MovimientoInventario(
                inventario=self.inventario,
                tipo='entrada',
                cantidad=self.cantidad,
                motivo=f'Compra #{self.id} recibida',
                usuario=self.usuario_registro
            )
            movimiento.save()
            Compra.objects.filter(pk=self.pk).update(stock_aplicado=True)


class Trabajo(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('en_produccion', 'En Producción'),
        ('terminado', 'Terminado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='trabajos', verbose_name="Cliente")
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, related_name='trabajos', verbose_name="Producto/Trabajo")
    cantidad = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    descripcion = models.TextField(verbose_name="Descripción del trabajo")

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Descuento (%)")
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio total")

    estado = models.CharField(max_length=50, choices=ESTADOS, default='pendiente', verbose_name="Estado")

    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_entrega = models.DateField(verbose_name="Fecha de entrega estimada")
    fecha_entregado = models.DateField(blank=True, null=True, verbose_name="Fecha de entrega real")

    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='trabajos_registrados', verbose_name="Registrado por")

    class Meta:
        verbose_name = "Trabajo"
        verbose_name_plural = "Trabajos"
        ordering = ['-fecha_creacion']

    def __str__(self):
        prod = getattr(self, 'producto', None)
        prod_name = prod.nombre if prod else 'Sin producto'
        return f"Trabajo #{self.id} - {self.cliente.nombre} - {prod_name} - {self.estado}"

    def save(self, *args, **kwargs):
        subtotal = self.precio_unitario * self.cantidad
        descuento_monto = subtotal * (self.descuento / 100)
        self.precio_total = subtotal - descuento_monto

        super().save(*args, **kwargs)
        self.cliente.cantidad_pedidos = self.cliente.pedidos.filter(estado='entregado').count() + \
                                        self.cliente.trabajos.filter(estado='entregado').count()
        self.cliente.save(update_fields=['cantidad_pedidos'])
        self.cliente.actualizar_frecuencia()
