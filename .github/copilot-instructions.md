# Instrucciones para agentes (Copilot) — Proyecto Capital (Django)

Resumen rápido
- Framework: Django 4.2 (apps: `core`), DRF para endpoints simples, SQLite por defecto.
- Idioma y convenciones: español en nombres de modelos, vistas y plantillas. UI con mensajes de Django y formularios con clases Bootstrap.
- Entorno: variables con `python-decouple` (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`). CORS habilitado para localhost:3000.

Arquitectura y flujos clave
- Modelos principales en `core/models.py`:
  - `Cliente`, `Producto`, `Inventario` y `MovimientoInventario` (este último ajusta `Inventario.cantidad` en `save` según `tipo`: entrada/salida/ajuste).
  - `Pedido`: calcula `precio_total` en `save` (subtotal − descuento) y actualiza métrica del `Cliente` (`cantidad_pedidos` + `es_frecuente`). No setear `precio_total` desde formularios; se computa solo.
  - `Produccion` (OneToOne con `Pedido`): métodos `iniciar_produccion()` y `finalizar_produccion()` cambian estado del pedido y tiempos.
  - `PerfilUsuario` extiende `User` (roles: `administrador` | `empleado`).
- Señales en `core/signals.py`:
  - Al crear un `User` ⇒ se crea `PerfilUsuario`.
  - Al crear un `Pedido` ⇒ se crea automáticamente su `Produccion`.
- Permisos y contexto:
  - Decoradores en `core/decorators.py`: `solo_administrador`, `solo_empleado`, `administrador_o_empleado` (usa `PerfilUsuario.rol`).
  - Context processor `core.context_processors.user_profile` inyecta `es_administrador`, `es_empleado` y `perfil_usuario` a todas las plantillas.

Vistas, URLs y plantillas
- Namespace de URLs: `app_name = 'core'` en `core/urls.py` (usa nombres como `core:clientes_lista`, `core:dashboard`).
- Rutas clave: login/logout, dashboard, CRUD de clientes/pedidos/inventario, panel de producción, y dos endpoints API: `api/status/` y `api/dashboard/stats/`.
- Plantillas en `templates/` organizadas por módulo: `clientes/`, `pedidos/`, `inventario/`, `produccion/`, etc. Formularios en `core/forms.py` ya incluyen widgets con clases Bootstrap.

APIs y configuración
- DRF activado (permisos por defecto `AllowAny` en `settings.py`). `api_dashboard_stats` exige autenticación con `@login_required`.
- `LANGUAGE_CODE = 'es-es'`, `TIME_ZONE = 'America/New_York'`. Estáticos en `static/` y media en `media/` (Pillow instalado para imágenes).

Workflows de desarrollo (PowerShell)
- Instalar deps: `pip install -r requirements.txt`.
- Variables de entorno (archivo `.env` recomendado):
  - `SECRET_KEY=...`; `DEBUG=True`; `ALLOWED_HOSTS=localhost,127.0.0.1`.
- Migraciones y datos: `python manage.py migrate`; crear superusuario: `python manage.py createsuperuser`.
- Ejecutar: `python manage.py runserver` (admin en `/admin`, app en `/`).
- Tests: `python manage.py test core`.

Patrones a seguir al contribuir
- Mantener nombres y textos en español; usar nombres de URL con el namespace `core:` para redirecciones y `reverse`.
- Para vistas protegidas: combinar `@login_required` con el decorador de rol apropiado.
- Si agregas lógica que afecta inventario, sigue el patrón de `MovimientoInventario.save` para mantener consistencia.
- Si agregas estados de pedido o flujos de producción, revisa interacciones con `Produccion` y señales existentes antes de duplicar lógica.
- Preferir lógica de negocio en métodos de modelo (`save`, helpers) sobre vistas; evita duplicación (ej.: cálculo de totales o cambios de estado).

Ejemplos rápidos
- Nueva vista CRUD protegida:
  - URL en `core/urls.py` con nombre `core:...`.
  - Vista con `@login_required` + `@administrador_o_empleado`.
  - Formulario en `core/forms.py` y plantilla en `templates/<modulo>/formulario.html` reutilizando estilo existente.
- Nuevo endpoint API: usa `@api_view([...])` de DRF; si requiere login, añade `@login_required`.

Referencias de archivos
- Configuración: `capital_project/settings.py`, `capital_project/urls.py`.
- App principal: `core/models.py`, `core/views.py`, `core/forms.py`, `core/urls.py`, `core/decorators.py`, `core/context_processors.py`, `core/signals.py`.
- Plantillas: `templates/**`.

Notas y gotchas
- `Pedido.save` recalcula `precio_total` y actualiza métricas de cliente en cada guardado.
- `Produccion` se crea por señal; no lo crees manualmente al crear pedidos.
- `MovimientoInventario.save` siempre persiste cambio en `Inventario`; valida bien `tipo` y `cantidad` en formularios.
