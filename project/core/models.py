from django.db import models
from django.dispatch import receiver
from django.forms import ValidationError
from project.choices import EstadoEntidades, EstadoCuenta
import uuid
from django.db.models.signals import post_save, post_delete
from django.db.models import Sum
from django.utils import timezone

class TipoDocumento(models.Model):
    tipo_documento_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'tipos_documento'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    proveedor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    ruc = models.CharField(max_length=11, unique=True)
    direccion = models.CharField(max_length=255, null=True)
    correo = models.EmailField(max_length=255, null=True)
    telefono = models.CharField(max_length=15, null=True)
    estado = models.IntegerField(choices=EstadoEntidades.choices, default=EstadoEntidades.ACTIVO)

    class Meta:
        db_table = 'proveedores'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Estados de la cuenta
class EstadoCuenta(models.IntegerChoices):
    ACTIVA = 1, 'Activa'
    CANCELADA = 2, 'Cancelada'
    VENCIDA = 3, 'Vencida'


class CuentaPorPagar(models.Model):
    cuenta_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.RESTRICT, db_column='proveedor_id')
    tipo_documento = models.ForeignKey('TipoDocumento', on_delete=models.RESTRICT)
    nro_documento = models.CharField(max_length=20)
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)

    monto_abonado_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Calculados automáticamente
    monto_abonado = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    estado = models.IntegerField(choices=EstadoCuenta.choices, default=EstadoCuenta.ACTIVA)

    class Meta:
        db_table = 'cuentas_por_pagar'
        ordering = ['fecha_vencimiento']

    def save(self, *args, **kwargs):
        # Calcular monto_abonado como: inicial + suma de pagos
        suma_pagos = self.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
        self.monto_abonado = self.monto_abonado_inicial + suma_pagos

        # Calcular saldo pendiente
        self.saldo_pendiente = max(self.monto_total - self.monto_abonado, 0)

        # Determinar estado
        hoy = timezone.now().date()
        if self.saldo_pendiente == 0:
            self.estado = EstadoCuenta.CANCELADA
        elif self.fecha_vencimiento < hoy:
            self.estado = EstadoCuenta.VENCIDA
        else:
            self.estado = EstadoCuenta.ACTIVA

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nro_documento} - {self.proveedor.nombre}'



class Pago(models.Model):
    pago_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cuenta = models.ForeignKey(CuentaPorPagar, on_delete=models.CASCADE, related_name='pagos', db_column='cuenta_id')
    fecha_pago = models.DateField()
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'pagos'
        ordering = ['fecha_pago']

    def clean(self):
        saldo_actual = self.cuenta.saldo_pendiente
        if self.pk:
            try:
                pago_actual = Pago.objects.get(pk=self.pk)
                saldo_actual += pago_actual.monto_pagado
            except Pago.DoesNotExist:
                pass

        if self.monto_pagado > saldo_actual:
            raise ValidationError(f'El monto pagado ({self.monto_pagado}) no puede ser mayor al saldo pendiente ({saldo_actual}).')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Pago {self.monto_pagado} - {self.fecha_pago}'


@receiver(post_save, sender=Pago)
@receiver(post_delete, sender=Pago)
def actualizar_monto_abonado(sender, instance, **kwargs):
    cuenta = instance.cuenta
    suma_pagos = cuenta.pagos.aggregate(total=Sum('monto_pagado'))['total'] or 0
    cuenta.monto_abonado = cuenta.monto_abonado_inicial + suma_pagos
    cuenta.save()