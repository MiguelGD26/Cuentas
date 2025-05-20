from rest_framework import serializers
from core.models import Proveedor, CuentaPorPagar, TipoDocumento, Pago

class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'

class CuentaPorPagarSerializer(serializers.ModelSerializer):
    proveedor = ProveedorSerializer(read_only=True)
    tipo_documento = TipoDocumentoSerializer(read_only=True)
    proveedor_id = serializers.UUIDField(write_only=True)
    tipo_documento_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CuentaPorPagar
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    cuenta = CuentaPorPagarSerializer(read_only=True)
    cuenta_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Pago
        fields = '__all__'
