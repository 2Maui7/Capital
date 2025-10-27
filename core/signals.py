from django.db.models.signals import post_save
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
