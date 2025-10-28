from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .models import Cliente, Producto, Pedido, Inventario, Proveedor, Compra, Trabajo


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión personalizado"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )


class ClienteForm(forms.ModelForm):
    """Formulario para gestión de clientes"""
    class Meta:
        model = Cliente
        fields = ['nombre', 'nit_ci', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'nit_ci': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIT/CI'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
        }


class PedidoForm(forms.ModelForm):
    """Formulario para gestión de pedidos"""
    class Meta:
        model = Pedido
        fields = ['cliente', 'inventario', 'cantidad', 'descripcion',
                  'precio_unitario', 'descuento', 'fecha_entrega', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'inventario': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asegurar que el selector muestre solo materiales disponibles (cantidad > 0).
        # En modo edición, incluir también el material actual aunque tenga 0 para no invalidar el formulario.
        if self.instance and getattr(self.instance, 'inventario_id', None):
            qs = Inventario.objects.filter(Q(cantidad__gt=0) | Q(pk=self.instance.inventario_id)).order_by('nombre')
        else:
            qs = Inventario.objects.filter(cantidad__gt=0).order_by('nombre')
        self.fields['inventario'].queryset = qs
        # Mostrar como listbox con varias filas visibles para hacer evidente que hay más opciones
        self.fields['inventario'].widget.attrs.update({'size': '12'})
        # Si hay un cliente seleccionado, aplicar descuento automáticamente
        if self.instance and self.instance.pk and hasattr(self.instance, 'cliente'):
            try:
                self.initial['descuento'] = self.instance.cliente.obtener_descuento()
            except:
                pass


 


class TrabajoForm(forms.ModelForm):
    """Formulario para gestión de trabajos (productos/servicios)"""
    class Meta:
        model = Trabajo
        fields = ['cliente', 'producto', 'cantidad', 'descripcion', 'precio_unitario', 'descuento', 'fecha_entrega', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True).order_by('nombre')
        # Mostrar como listbox alto
        self.fields['producto'].widget.attrs.update({'size': '12'})
        # Descuento automático si aplica
        if self.instance and self.instance.pk and hasattr(self.instance, 'cliente'):
            try:
                self.initial['descuento'] = self.instance.cliente.obtener_descuento()
            except Exception:
                pass

 
class ProveedorForm(forms.ModelForm):
    """Formulario para gestión de proveedores"""
    class Meta:
        model = Proveedor
        fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CompraForm(forms.ModelForm):
    """Formulario para compras a proveedores"""
    class Meta:
        model = Compra
        fields = ['proveedor', 'inventario', 'cantidad', 'precio_unitario', 'estado', 'fecha_recepcion', 'observaciones']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'inventario': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_recepcion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('nombre')

