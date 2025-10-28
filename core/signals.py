from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Pedido, Produccion


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crear perfil de usuario automáticamente cuando se crea un nuevo usuario"""
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guardar el perfil cuando se actualiza el usuario"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


@receiver(post_save, sender=Pedido)
def crear_produccion_automatica(sender, instance, created, **kwargs):
    """Crear registro de producción automáticamente cuando se crea un pedido"""
    if created:
        Produccion.objects.get_or_create(
            pedido=instance,
            defaults={'tiempo_estimado': 0}
        )


@receiver(post_delete, sender=Pedido)
def actualizar_contador_cliente_al_eliminar_pedido(sender, instance, **kwargs):
    """Recalcular cantidad de pedidos del cliente al eliminar un pedido.
    Solo cuentan pedidos con estado 'entregado'.
    """
    cliente = getattr(instance, 'cliente', None)
    if not cliente:
        return
    # Evitar errores si el cliente fue eliminado en cascada
    from .models import Cliente as ClienteModel
    if not ClienteModel.objects.filter(pk=cliente.pk).exists():
        return
    cliente.cantidad_pedidos = cliente.pedidos.filter(estado='entregado').count()
    cliente.save(update_fields=['cantidad_pedidos'])
    cliente.actualizar_frecuencia()
