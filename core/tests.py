from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Proveedor
from .models import Cliente, Producto, Pedido
from decimal import Decimal


class ComprasUITest(TestCase):
	def setUp(self):
		# Usuario autenticado
		self.user = User.objects.create_user(username='tester', password='secret123')
		# Proveedores de ejemplo
		Proveedor.objects.create(nombre='Papelera Andina')
		Proveedor.objects.create(nombre='Tintas SRL')

	def test_compra_crear_muestra_listbox_proveedores(self):
		# Login
		self.client.login(username='tester', password='secret123')
		# Ir a crear compra
		url = reverse('core:compra_crear')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# Debe existir el listbox (select) con id proveedor_material
		html = resp.content.decode('utf-8')
		self.assertIn('<select', html)
		self.assertIn('id="proveedor_material"', html)
		# Debe listar proveedores creados
		self.assertIn('Papelera Andina', html)
		self.assertIn('Tintas SRL', html)


class ClientePedidosCountTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='seller', password='s3cret')
		self.cliente = Cliente.objects.create(nombre='ACME')
		self.producto = Producto.objects.create(
			nombre='Tarjetas', tipo='tarjetas', descripcion='x', precio_unitario=Decimal('10.00'), activo=True
		)

	def _nuevo_pedido(self, estado):
		pedido = Pedido.objects.create(
			cliente=self.cliente,
			producto=self.producto,
			cantidad=1,
			descripcion='Test',
			especificaciones='',
			precio_unitario=Decimal('10.00'),
			descuento=Decimal('0'),
			fecha_entrega='2025-10-30',
			estado=estado,
			usuario_registro=self.user,
		)
		return pedido

	def test_contador_incrementa_solo_entregados(self):
		# Inicialmente 0
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		# Pedido pendiente no cuenta
		p1 = self._nuevo_pedido('pendiente')
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		# Terminado no cuenta
		p1.estado = 'terminado'
		p1.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		# Entregado sí cuenta
		p1.estado = 'entregado'
		p1.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

		# Otro pedido cancelado tampoco cuenta
		self._nuevo_pedido('cancelado')
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

	def test_es_frecuente_al_quinto_entregado(self):
		# Crear 5 pedidos entregados
		for _ in range(5):
			p = self._nuevo_pedido('entregado')
			# ensure save triggers counter and frequent flag
			p.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 5)
		self.assertTrue(self.cliente.es_frecuente)

	def test_frecuente_se_desmarca_al_bajar_de_umbral(self):
		# Hacer cliente frecuente (5 entregados)
		pedidos = []
		for _ in range(5):
			p = self._nuevo_pedido('entregado')
			p.save()
			pedidos.append(p)
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 5)
		self.assertTrue(self.cliente.es_frecuente)

		# Eliminar uno: debe quedar en 4 y desmarcar frecuente
		pedidos[0].delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 4)
		self.assertFalse(self.cliente.es_frecuente)

	@override_settings(CLIENTE_FRECUENTE_UMBRAL=3)
	def test_umbral_configurable(self):
		# Con umbral en 3, dos entregados aún no es frecuente
		p1 = self._nuevo_pedido('entregado'); p1.save()
		p2 = self._nuevo_pedido('entregado'); p2.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)
		self.assertFalse(self.cliente.es_frecuente)

		# Al tercero, debe pasar a frecuente
		p3 = self._nuevo_pedido('entregado'); p3.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 3)
		self.assertTrue(self.cliente.es_frecuente)

		# Si eliminamos uno, vuelve a no frecuente
		p3.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)
		self.assertFalse(self.cliente.es_frecuente)

	def test_decrementa_al_eliminar_pedido_entregado(self):
		# Crear 2 pedidos entregados
		p1 = self._nuevo_pedido('entregado')
		p2 = self._nuevo_pedido('entregado')
		p1.save(); p2.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)

		# Eliminar uno y debe decrementar a 1
		p1.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)
		# Aún no debe ser frecuente (umbral 5)
		self.assertFalse(self.cliente.es_frecuente)

	def test_eliminar_no_entregado_no_afecta_contador(self):
		# Crear un entregado y uno pendiente
		p_ent = self._nuevo_pedido('entregado'); p_ent.save()
		p_pen = self._nuevo_pedido('pendiente'); p_pen.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

		# Eliminar el pendiente no debe cambiar el contador
		p_pen.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

# Create your tests here.
