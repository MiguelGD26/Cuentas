from django.db import models

class EstadoEntidades(models.IntegerChoices):
    ACTIVO = 1, "ACTIVO"
    DE_BAJA = 9, "INACTIVO"

class EstadoCuenta(models.IntegerChoices):
    ACTIVA = 1, "ACTIVA"
    CANCELADA = 2, "CANCELADA"
