from django.contrib import admin
from .models import TipoDocumento, Proveedor, CuentaPorPagar, Pago

# Register your models here.
admin.site.register(TipoDocumento)
admin.site.register(Proveedor)
admin.site.register(CuentaPorPagar)
admin.site.register(Pago)