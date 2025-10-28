from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Proveedor
from .models import Cliente, Inventario, Pedido
from decimal import Decimal


class ComprasUITest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='tester', password='secret123')
		Proveedor.objects.create(nombre='Papelera Andina')
		Proveedor.objects.create(nombre='Tintas SRL')

	def test_compra_crear_muestra_listbox_proveedores(self):
		self.client.login(username='tester', password='secret123')
		url = reverse('core:compra_crear')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		html = resp.content.decode('utf-8')
		self.assertIn('<select', html)
		self.assertIn('id="proveedor_material"', html)
		self.assertIn('Papelera Andina', html)
		self.assertIn('Tintas SRL', html)


class PedidoProductoChoicesTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='seller2', password='s3cret')
		self.cliente = Cliente.objects.create(nombre='Foo')
		for i in range(12):
			Inventario.objects.create(
				nombre=f'Mat {i:02d}', descripcion='x', cantidad=10, cantidad_minima=1, unidad='unidad', proveedor='Prov', precio_unitario=Decimal('1.00')
			)

	def test_form_pedido_lista_todos_los_productos(self):
		from .forms import PedidoForm
		form = PedidoForm()
		qs = form.fields['inventario'].queryset
		self.assertEqual(qs.count(), 12)


class ClientePedidosCountTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='seller', password='s3cret')
		self.cliente = Cliente.objects.create(nombre='ACME')
		self.material = Inventario.objects.create(
			nombre='Cartulina', descripcion='x', cantidad=100, cantidad_minima=5, unidad='unidad', proveedor='Local', precio_unitario=Decimal('10.00')
		)

	def _nuevo_pedido(self, estado):
		pedido = Pedido.objects.create(
			cliente=self.cliente,
			inventario=self.material,
			cantidad=1,
			descripcion='Test',
			precio_unitario=Decimal('10.00'),
			descuento=Decimal('0'),
			fecha_entrega='2025-10-30',
			estado=estado,
			usuario_registro=self.user,
		)
		return pedido

	def test_contador_incrementa_solo_entregados(self):
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		p1 = self._nuevo_pedido('pendiente')
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		p1.estado = 'terminado'
		p1.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 0)

		p1.estado = 'entregado'
		p1.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

		self._nuevo_pedido('cancelado')
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

	def test_es_frecuente_al_quinto_entregado(self):
		for _ in range(5):
			p = self._nuevo_pedido('entregado')
			p.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 5)
		self.assertTrue(self.cliente.es_frecuente)

	def test_frecuente_se_desmarca_al_bajar_de_umbral(self):
		pedidos = []
		for _ in range(5):
			p = self._nuevo_pedido('entregado')
			p.save()
			pedidos.append(p)
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 5)
		self.assertTrue(self.cliente.es_frecuente)

		pedidos[0].delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 4)
		self.assertFalse(self.cliente.es_frecuente)

	@override_settings(CLIENTE_FRECUENTE_UMBRAL=3)
	def test_umbral_configurable(self):
		p1 = self._nuevo_pedido('entregado'); p1.save()
		p2 = self._nuevo_pedido('entregado'); p2.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)
		self.assertFalse(self.cliente.es_frecuente)

		p3 = self._nuevo_pedido('entregado'); p3.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 3)
		self.assertTrue(self.cliente.es_frecuente)

		p3.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)
		self.assertFalse(self.cliente.es_frecuente)

	def test_decrementa_al_eliminar_pedido_entregado(self):
		p1 = self._nuevo_pedido('entregado')
		p2 = self._nuevo_pedido('entregado')
		p1.save(); p2.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 2)

		p1.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)
		self.assertFalse(self.cliente.es_frecuente)

	def test_eliminar_no_entregado_no_afecta_contador(self):
		p_ent = self._nuevo_pedido('entregado'); p_ent.save()
		p_pen = self._nuevo_pedido('pendiente'); p_pen.save()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

		p_pen.delete()
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.cantidad_pedidos, 1)

