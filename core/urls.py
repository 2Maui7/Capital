from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Autenticación
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Clientes
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/crear/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    
    # Pedidos
    path('pedidos/', views.pedidos_lista, name='pedidos_lista'),
    path('pedidos/crear/', views.pedido_crear, name='pedido_crear'),
    path('pedidos/<int:pk>/editar/', views.pedido_editar, name='pedido_editar'),
    path('pedidos/<int:pk>/eliminar/', views.pedido_eliminar, name='pedido_eliminar'),
    path('pedidos/<int:pk>/', views.pedido_detalle, name='pedido_detalle'),
    
    # Inventario
    path('inventario/', views.inventario_lista, name='inventario_lista'),
    path('inventario/crear/', views.inventario_crear, name='inventario_crear'),
    
    # Producción
    path('produccion/', views.produccion_panel, name='produccion_panel'),
    path('produccion/<int:pk>/iniciar/', views.produccion_iniciar, name='produccion_iniciar'),
    
    # API
    path('api/status/', views.api_status, name='api_status'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]
