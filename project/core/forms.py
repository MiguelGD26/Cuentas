from datetime import date
from django import forms

from project.choices import EstadoCuenta, EstadoEntidades
from .models import Proveedor, CuentaPorPagar, Pago, TipoDocumento
from django.core.exceptions import ValidationError

class ProveedorForm(forms.ModelForm):
    estado = forms.BooleanField(required=False, label="Estado (activo/inactivo)")

    class Meta:
        model = Proveedor
        fields = ['nombre', 'ruc', 'direccion', 'correo', 'telefono', 'estado']

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'nombre',
                'placeholder': 'Ingrese el nombre del proveedor'
            }),
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'ruc',
                'placeholder': 'Ingrese el RUC (11 dígitos)'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'direccion',
                'placeholder': 'Ingrese la dirección'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'correo',
                'placeholder': 'Ingrese un correo válido'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'telefono',
                'placeholder': 'Ingrese teléfono (9 dígitos, inicia con 9)'
            }),
            'estado': forms.CheckboxInput(attrs={
                'id': 'estado',
            }),
        }
    
    def clean_estado(self):
        checked = self.cleaned_data.get('estado', False)
        return EstadoEntidades.ACTIVO if checked else EstadoEntidades.DE_BAJA
    
    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
         # Validar que el RUC no esté duplicado (excepto en edición)
        queryset = Proveedor.objects.filter(ruc=ruc)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError("Este RUC ya está registrado.")

        return ruc


class CuentaPorPagarForm(forms.ModelForm):
    proveedor_nombre_display = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'id': 'proveedor_search_input', 
            'placeholder': 'Escriba para buscar proveedor...'
        })
    )
    tipo_documento = forms.ModelChoiceField(
    queryset=TipoDocumento.objects.all(),
    empty_label="Selecciona tipo de documento",
    widget=forms.Select(attrs={
        'class': 'form-control',
        'id': 'tipo_documento'
    })
    )


    nro_documento = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'nro_documento',
            'placeholder': 'Ingrese el número del documento'
        })
    )

    fecha_emision = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'id': 'fecha_emision',
            'autocomplete': 'off',
            'placeholder': 'Ingresa Fecha de emisión'
            
        })
    )

    fecha_vencimiento = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'id': 'fecha_vencimiento',
            'autocomplete': 'off' ,
            'placeholder': 'Ingresa Fecha de vencimiento'
            
        })
    )

    monto_total = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'monto_total',
            'placeholder': 'Ingrese el monto total'
        })
    )

    monto_abonado_inicial = forms.DecimalField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'monto_abonado_inicial',
            'placeholder': 'Ingrese el monto abonado inicial'
        })
    )
    class Meta:
        model = CuentaPorPagar
        fields = [
            'proveedor', 'tipo_documento', 'nro_documento',
            'fecha_emision', 'fecha_vencimiento',
            'monto_total', 'monto_abonado_inicial'
        ]
        widgets = {
            'proveedor': forms.HiddenInput(),
         }

        proveedor_nombre_display = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'proveedor_search_input', 'placeholder': 'Escriba para buscar proveedor...'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Reordenar campos si es necesario
        field_order = list(self.fields.keys())
        if 'proveedor_nombre_display' in field_order and 'proveedor' in field_order:
            pnd_idx = field_order.index('proveedor_nombre_display')
            p_idx = field_order.index('proveedor')
            if pnd_idx > p_idx: # Si el display está después del hidden, moverlo antes
                field_order.pop(pnd_idx)
                field_order.insert(p_idx, 'proveedor_nombre_display')
                self.order_fields(field_order)

        # Pre-rellenar el nombre del proveedor en modo edición
        # self.instance es el objeto CuentaPorPagar que se está editando, o uno nuevo si es creación.
        # self.instance.pk será None si es un objeto nuevo.
        if self.instance and self.instance.pk:  # Solo si es una instancia existente (modo edición)
            try:
                # Intentamos acceder al proveedor solo si la instancia ya existe.
                # Si self.instance.proveedor es None (p.ej. ForeignKey con null=True y no seteado),
                # esto no dará error, pero self.instance.proveedor.nombre sí lo daría.
                if self.instance.proveedor: # Comprueba que el campo ForeignKey 'proveedor' no sea None
                    self.fields['proveedor_nombre_display'].initial = self.instance.proveedor.nombre
            except Proveedor.DoesNotExist: # O la excepción genérica RelatedObjectDoesNotExist
                 # Esto podría pasar si el ID del proveedor en la BD es inválido, aunque es raro
                 # con ForeignKeys bien definidos.
                 self.fields['proveedor_nombre_display'].initial = "" # O un mensaje de error
            # No necesitas un `else` aquí, si `self.instance.proveedor` es `None`, no se establece `initial`.

        # Aplicar clases a otros campos (tu lógica existente)
        for field_name, field in self.fields.items():
            if field_name not in ['proveedor', 'proveedor_nombre_display', 'fecha_emision', 'fecha_vencimiento']:
                current_class = field.widget.attrs.get('class', '')
                is_select = isinstance(field.widget, forms.Select)
                target_class = 'form-select' if is_select else 'form-control'
                
                if target_class not in current_class and not isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = f'{current_class} {target_class}'.strip()
                    
    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("monto_total")
        abonado = cleaned_data.get("monto_abonado_inicial")
        fecha_emision = cleaned_data.get("fecha_emision")
        fecha_vencimiento = cleaned_data.get("fecha_vencimiento")

        if total is not None and abonado is not None and abonado > total:
            raise forms.ValidationError("El monto abonado inicial no puede ser mayor que el monto total.")
        
        if fecha_emision and fecha_vencimiento and fecha_emision > fecha_vencimiento:
            raise forms.ValidationError("La fecha de emisión no puede ser posterior a la fecha de vencimiento.")
        
        return cleaned_data

class PagoForm(forms.ModelForm):
    cuenta = forms.ModelChoiceField(
        queryset=CuentaPorPagar.objects.all(),
        required=True
    )
    fecha_pago = forms.DateField(
    
    widget=forms.DateInput(attrs={
        'type': 'text',
        'class': 'form-control',
        'id': 'fecha_pago',
        'autocomplete': 'off',
        'placeholder': 'Ingresa Fecha'
    })
)

    class Meta:
        model = Pago
        fields = ['cuenta', 'fecha_pago', 'monto_pagado']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'fecha_pago'
            }),
            'cuenta': forms.Select(attrs={
                'class': 'form-control', 
                'disabled': 'disabled'  
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'cuenta' in self.initial:
            self.fields['cuenta'].disabled = True

    def clean_monto_pagado(self):
        monto = self.cleaned_data['monto_pagado']
        cuenta = self.cleaned_data.get('cuenta') or self.initial.get('cuenta')

        if isinstance(cuenta, int):
            cuenta = CuentaPorPagar.objects.get(pk=cuenta)

        if monto <= 0:
            raise ValidationError("El monto debe ser mayor que 0.")

        if cuenta and monto > cuenta.saldo_pendiente:
            raise ValidationError(f"El monto no puede ser mayor al saldo pendiente: S/ {cuenta.saldo_pendiente}.")

        return monto

    def clean(self):
        cleaned_data = super().clean()
        cuenta = cleaned_data.get("cuenta")
        monto = cleaned_data.get("monto_pagado")
        fecha_pago = cleaned_data.get("fecha_pago")

        if not fecha_pago:
            raise ValidationError("La fecha de pago es obligatoria.")

        if cuenta is None or monto is None:
            return cleaned_data

        if monto <= 0:
            raise ValidationError("El monto pagado debe ser mayor a cero.")

        return cleaned_data
