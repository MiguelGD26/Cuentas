from django.shortcuts import render
from rest_framework import viewsets
from core.models import Proveedor, CuentaPorPagar, TipoDocumento, Pago
from .serializers import (
    ProveedorSerializer,
    CuentaPorPagarSerializer,
    TipoDocumentoSerializer,
    PagoSerializer
)

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer

class TipoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer

class CuentaPorPagarViewSet(viewsets.ModelViewSet):
    queryset = CuentaPorPagar.objects.all()
    serializer_class = CuentaPorPagarSerializer

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
