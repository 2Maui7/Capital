from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Pedido, Produccion, Trabajo


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


@receiver(post_save, sender=Pedido)
def crear_produccion_automatica(sender, instance, created, **kwargs):
    if created:
        Produccion.objects.get_or_create(
            pedido=instance,
            defaults={'tiempo_estimado': 0}
        )


@receiver(post_delete, sender=Pedido)
def actualizar_contador_cliente_al_eliminar_pedido(sender, instance, **kwargs):
    cliente = getattr(instance, 'cliente', None)
    if not cliente:
        return
    from .models import Cliente as ClienteModel
    if not ClienteModel.objects.filter(pk=cliente.pk).exists():
        return
    pedidos_entregados = cliente.pedidos.filter(estado='entregado').count()
    trabajos_entregados = cliente.trabajos.filter(estado='entregado').count()
    cliente.cantidad_pedidos = pedidos_entregados + trabajos_entregados
    cliente.save(update_fields=['cantidad_pedidos'])
    cliente.actualizar_frecuencia()


@receiver(post_delete, sender=Trabajo)
def actualizar_contador_cliente_al_eliminar_trabajo(sender, instance, **kwargs):
    cliente = getattr(instance, 'cliente', None)
    if not cliente:
        return
    from .models import Cliente as ClienteModel
    if not ClienteModel.objects.filter(pk=cliente.pk).exists():
        return
    pedidos_entregados = cliente.pedidos.filter(estado='entregado').count()
    trabajos_entregados = cliente.trabajos.filter(estado='entregado').count()
    cliente.cantidad_pedidos = pedidos_entregados + trabajos_entregados
    cliente.save(update_fields=['cantidad_pedidos'])
    cliente.actualizar_frecuencia()
