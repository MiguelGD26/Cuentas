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
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(),
        empty_label="Selecciona proveedor",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'proveedor'
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
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),

            'proveedor': forms.Select(attrs={
                'class': 'form-control',
                'id': 'proveedor'

            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control',
                'id': 'tipo_documento'
            }),
            'nro_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'nro_documento',
                'placeholder': 'Ingrese el número del documento'
            }),
            'fecha_emision': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'fecha_emision'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'fecha_vencimiento'
            }),
            'monto_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'monto_total',
                'placeholder': 'Ingrese el monto total'
            }),
            'monto_abonado_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'monto_abonado_inicial',
                'placeholder': 'Ingrese el monto abonado inicial'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("monto_total")
        abonado = cleaned_data.get("monto_abonado_inicial")
        if total is not None and abonado is not None and abonado > total:
            raise forms.ValidationError("El monto abonado inicial no puede ser mayor que el monto total.")

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['cuenta', 'fecha_pago', 'monto_pagado']
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
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

        if cuenta is None or monto is None:
            return cleaned_data

        if monto <= 0:
            raise ValidationError("El monto pagado debe ser mayor a cero.")

        return cleaned_data