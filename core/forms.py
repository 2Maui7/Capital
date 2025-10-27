from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Cliente, Producto, Pedido, Inventario, Produccion, MovimientoInventario, PerfilUsuario


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


class ProductoForm(forms.ModelForm):
    """Formulario para gestión de productos"""
    class Meta:
        model = Producto
        fields = ['nombre', 'tipo', 'descripcion', 'precio_unitario', 'imagen', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PedidoForm(forms.ModelForm):
    """Formulario para gestión de pedidos"""
    class Meta:
        model = Pedido
        fields = ['cliente', 'producto', 'cantidad', 'descripcion', 'especificaciones', 
                  'precio_unitario', 'descuento', 'fecha_entrega', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'especificaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descuento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay un cliente seleccionado, aplicar descuento automáticamente
        if self.instance and self.instance.pk and hasattr(self.instance, 'cliente'):
            try:
                self.initial['descuento'] = self.instance.cliente.obtener_descuento()
            except:
                pass


class InventarioForm(forms.ModelForm):
    """Formulario para gestión de inventario"""
    class Meta:
        model = Inventario
        fields = ['nombre', 'descripcion', 'cantidad', 'cantidad_minima', 'unidad', 'proveedor', 'precio_unitario']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'cantidad_minima': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ProduccionForm(forms.ModelForm):
    """Formulario para gestión de producción"""
    class Meta:
        model = Produccion
        fields = ['pedido', 'estado', 'empleado', 'tiempo_estimado', 'observaciones']
        widgets = {
            'pedido': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'tiempo_estimado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MovimientoInventarioForm(forms.ModelForm):
    """Formulario para movimientos de inventario"""
    class Meta:
        model = MovimientoInventario
        fields = ['inventario', 'tipo', 'cantidad', 'motivo', 'produccion']
        widgets = {
            'inventario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'produccion': forms.Select(attrs={'class': 'form-select'}),
        }


class UsuarioForm(UserCreationForm):
    """Formulario para crear usuarios"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para editar perfil de usuario"""
    class Meta:
        model = PerfilUsuario
        fields = ['rol', 'telefono', 'foto', 'activo']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
