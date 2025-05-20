from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProveedorViewSet,
    TipoDocumentoViewSet,
    CuentaPorPagarViewSet,
    PagoViewSet
)

router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet)
router.register(r'tipos-documento', TipoDocumentoViewSet)
router.register(r'cuentas', CuentaPorPagarViewSet)
router.register(r'pagos', PagoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
