from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime
from django.core.paginator import Paginator
from django.db.models import Q
import uuid

from .models import Proveedor, CuentaPorPagar, TipoDocumento, Pago
from .forms import ProveedorForm, CuentaPorPagarForm, PagoForm

def dashboard(request):
    return render(request, 'core/dashboard.html')

# Página de inicio
def home(request):
    return render(request, 'core/home.html')

# Login de usuario
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Sesión iniciada correctamente")
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales incorrectas")
            return redirect('login')
    return render(request, 'core/login/login.html')

# Logout
def logout_user(request):
    logout(request)
    messages.success(request, "Sesión cerrada")
    return redirect('home')

# Listado de proveedores
@login_required
def listar_proveedores(request):
    nombre = request.GET.get('nombre', '')
    ruc = request.GET.get('ruc', '')
    estado = request.GET.get('estado', '')

    proveedores_list = Proveedor.objects.all()

    if nombre:
        proveedores_list = proveedores_list.filter(nombre__icontains=nombre)
    if ruc:
        proveedores_list = proveedores_list.filter(ruc__icontains=ruc)
    if estado:
        proveedores_list = proveedores_list.filter(estado=int(estado))


    paginator = Paginator(proveedores_list, 5)
    page = request.GET.get('page')
    proveedores = paginator.get_page(page)

    return render(request, 'core/proveedores/listar.html', {
        'proveedores': proveedores,
        'nombre': nombre,
        'ruc': ruc,
        'estado': estado,
    })


# Crear proveedor
@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.estado = True  # Forzar estado como activo
            proveedor.save()
            messages.success(request, "Proveedor registrado")
            return redirect('listar_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'core/proveedores/formulario.html', {
        'form': form,
        'es_edicion': False,
    })


# Editar proveedor
@login_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        messages.success(request, "Proveedor actualizado")
        return redirect('listar_proveedores')
    return render(request, 'core/proveedores/formulario.html', {
    'form': form,
    'es_edicion': True,
})

# Eliminar proveedor
@login_required
def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.delete()
    messages.success(request, "Proveedor eliminado")
    return redirect('listar_proveedores')

# Listar cuentas por pagar con filtros y alertas
@login_required
def listar_cuentas(request):
    cuentas = CuentaPorPagar.objects.select_related('proveedor', 'tipo_documento').all()
    proveedores = Proveedor.objects.all()

    # Filtros
    # Obtener filtros desde GET
    query = request.GET.get('q', '')
    proveedor_id = request.GET.get('proveedor')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')

    # Filtro de búsqueda general (proveedor o número de documento)
    if query:
        cuentas = cuentas.filter(
            Q(proveedor__nombre__icontains=query) |
            Q(nro_documento__icontains=query)
        )


    # Filtro por proveedor
    if proveedor_id:
        cuentas = cuentas.filter(proveedor_id=proveedor_id)

    # Filtro por estado
    if estado:
        try:
            estado_int = int(estado)
            cuentas = cuentas.filter(estado=estado_int)
        except ValueError:
            pass  # Ignorar si no es un número válido

    # Filtro por fecha de emisión
    if fecha_desde:
        try:
            desde_date = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            cuentas = cuentas.filter(fecha_emision__gte=desde_date)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            hasta_date = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            cuentas = cuentas.filter(fecha_emision__lte=hasta_date)
        except ValueError:
            pass

    # Ordenar por fecha de emisión
    cuentas = cuentas.order_by('fecha_emision')

    # Alerta: cuentas por vencer en los próximos 7 días
    hoy = date.today()
    proximo_limite = hoy + timedelta(days=7)
    cuentas_por_vencer = cuentas.filter(
        fecha_vencimiento__range=(hoy, proximo_limite),
        saldo_pendiente__gt=0
    )

    # Paginación
    paginator = Paginator(cuentas, 5)
    page = request.GET.get('page')
    cuentas_paginadas = paginator.get_page(page)

    context = {
        'cuentas': cuentas_paginadas,
        'cuentas_por_vencer': cuentas_por_vencer,
        'proveedores': proveedores,
        'query': query,
        'proveedor_id': proveedor_id,
        'estado': estado,
        'desde': fecha_desde,
        'hasta': fecha_hasta,
    }

    return render(request, 'core/cuentas/listar.html', context)


# Crear cuenta por pagar
@login_required
def crear_cuenta(request):
    if request.method == 'POST':
        form = CuentaPorPagarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta por pagar registrada")
            return redirect('listar_cuentas')
    else:
        form = CuentaPorPagarForm()
    return render(request, 'core/cuentas/formulario.html',  {
    'form': form,
    'es_edicion': False,
})


# Editar cuenta
@login_required
def editar_cuenta(request, pk):
    cuenta = get_object_or_404(CuentaPorPagar, pk=pk)
    form = CuentaPorPagarForm(request.POST or None, instance=cuenta)
    if form.is_valid():
        form.save()
        messages.success(request, "Cuenta por pagar actualizada")
        return redirect('listar_cuentas')
    return render(request, 'core/cuentas/formulario.html',  {
    'form': form,
    'es_edicion': True,
})
# Eliminar cuenta
@login_required
def eliminar_cuenta(request, pk):
    cuenta = get_object_or_404(CuentaPorPagar, pk=pk)
    cuenta.delete()
    messages.success(request, "Cuenta por pagar eliminada")
    return redirect('listar_cuentas')

# Listar pagos
@login_required
def listar_pagos(request):
    pagos = Pago.objects.select_related('cuenta__proveedor', 'cuenta__tipo_documento').all()
    proveedores = Proveedor.objects.all()

    # Obtener filtros desde GET
    proveedor_id = request.GET.get('proveedor')
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')

    # Filtro por proveedor (validar UUID)
    if proveedor_id:
        try:
            proveedor_uuid = uuid.UUID(proveedor_id)
            pagos = pagos.filter(cuenta__proveedor_id=proveedor_uuid)
        except ValueError:
            pass  # proveedor_id inválido, ignorar filtro
        
    # Filtro por fecha de pago
    if fecha_desde:
        try:
            desde_date = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            pagos = pagos.filter(fecha_pago__gte=desde_date)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            hasta_date = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            pagos = pagos.filter(fecha_pago__lte=hasta_date)
        except ValueError:
            pass

    # Ordenar por fecha de pago descendente (los últimos primero)
    pagos = pagos.order_by('-fecha_pago')

    # Paginación (ejemplo: 10 por página)
    paginator = Paginator(pagos, 5)
    page = request.GET.get('page')
    pagos_paginados = paginator.get_page(page)

    context = {
        'pagos': pagos_paginados,
        'proveedores': proveedores,
        'proveedor_id': proveedor_id,
        'desde': fecha_desde,
        'hasta': fecha_hasta,
    }

    return render(request, 'core/pagos/listar.html', context)

# Crear pago
@login_required
def crear_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago registrado")
            return redirect('listar_pagos')
    else:
        form = PagoForm()
    return render(request, 'core/pagos/formulario.html', {'form': form})

# Eliminar pago
@login_required
def eliminar_pago(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    pago.delete()
    messages.success(request, "Pago eliminado")
    return redirect('listar_pagos')

# Obtener saldo restante de una cuenta
@login_required
def obtener_saldo(request):
    cuenta_id = request.GET.get('cuenta_id')
    try:
        cuenta = CuentaPorPagar.objects.get(pk=cuenta_id)
        return JsonResponse({'saldo': cuenta.saldo_pendiente})
    except CuentaPorPagar.DoesNotExist:
        return JsonResponse({'error': 'Cuenta no encontrada'}, status=404)
