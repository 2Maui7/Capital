from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Proveedor


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

# Create your tests here.
