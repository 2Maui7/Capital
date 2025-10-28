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

    # Trabajos (Productos/Servicios)
    path('trabajos/', views.trabajos_lista, name='trabajos_lista'),
    path('trabajos/crear/', views.trabajo_crear, name='trabajo_crear'),
    path('trabajos/<int:pk>/', views.trabajo_detalle, name='trabajo_detalle'),
    path('trabajos/<int:pk>/editar/', views.trabajo_editar, name='trabajo_editar'),
    path('trabajos/<int:pk>/eliminar/', views.trabajo_eliminar, name='trabajo_eliminar'),
    
    # Inventario
    path('inventario/', views.inventario_lista, name='inventario_lista'),
    # La creación de inventario se realiza desde Compras
    
    # Proveedores
    path('proveedores/', views.proveedores_lista, name='proveedores_lista'),
    path('proveedores/crear/', views.proveedor_crear, name='proveedor_crear'),
    path('proveedores/<int:pk>/editar/', views.proveedor_editar, name='proveedor_editar'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_eliminar, name='proveedor_eliminar'),

    # Compras
    path('compras/', views.compras_lista, name='compras_lista'),
    path('compras/crear/', views.compra_crear, name='compra_crear'),
    path('compras/<int:pk>/editar/', views.compra_editar, name='compra_editar'),
    path('compras/<int:pk>/eliminar/', views.compra_eliminar, name='compra_eliminar'),
    path('compras/<int:pk>/recibir/', views.compra_marcar_recibido, name='compra_marcar_recibido'),
    path('compras/reportes/', views.compras_reportes, name='compras_reportes'),

    # Producción
    path('produccion/', views.produccion_panel, name='produccion_panel'),
    path('produccion/<int:pk>/iniciar/', views.produccion_iniciar, name='produccion_iniciar'),
    
    # API
    path('api/status/', views.api_status, name='api_status'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
]
