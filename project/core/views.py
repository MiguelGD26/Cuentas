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

def detalle_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(CuentaPorPagar, pk=cuenta_id)

    pagos = Pago.objects.filter(cuenta=cuenta).order_by('-fecha_pago')

    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')

    if desde:
        pagos = pagos.filter(fecha_pago__gte=desde)
    if hasta:
        pagos = pagos.filter(fecha_pago__lte=hasta)

    paginator = Paginator(pagos, 10)  # 10 pagos por página
    page_number = request.GET.get('page')
    pagos_page = paginator.get_page(page_number)

    context = {
        'cuenta': cuenta,
        'pagos': pagos_page,
        'desde': desde or '',
        'hasta': hasta or '',
    }
    return render(request, 'core/cuentas/detalle_cuenta.html', context)

# Listar pagos
@login_required
def listar_pagos(request, cuenta_id):
    cuenta = get_object_or_404(CuentaPorPagar, cuenta_id=cuenta_id)
    pagos = cuenta.pagos.all().order_by('-fecha_pago')

    # Filtros de fecha (opcional)
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')

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

    paginator = Paginator(pagos, 5)
    page = request.GET.get('page')
    pagos_paginados = paginator.get_page(page)

    context = {
        'cuenta': cuenta,
        'pagos': pagos_paginados,
        'desde': fecha_desde,
        'hasta': fecha_hasta,
    }

    return render(request, 'core/pagos/listar.html', context)


# Crear pago
def crear_pago_para_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(CuentaPorPagar, pk=cuenta_id)

    if request.method == 'POST':
        form = PagoForm(request.POST, initial={'cuenta': cuenta})
        if form.is_valid():
            pago = form.save(commit=False)
            pago.cuenta = cuenta  # ← ASIGNACIÓN EXPLÍCITA
            pago.save()
            return redirect('detalle_cuenta', cuenta_id=cuenta.pk)
    else:
        form = PagoForm(initial={'cuenta': cuenta})
        form.fields['cuenta'].queryset = CuentaPorPagar.objects.filter(pk=cuenta.pk)

    return render(request, 'core/pagos/formulario.html',{
    'form': form,
    'es_edicion': False,
    'cuenta': cuenta,
    'cuenta_id': cuenta.pk, 
    })
    
# Eliminar pago
@login_required
def eliminar_pago(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    cuenta_id = pago.cuenta.cuenta_id  # Obtener cuenta antes de eliminar
    pago.delete()
    messages.success(request, "Pago eliminado")
    return redirect('detalle_cuenta', cuenta_id=pago.cuenta.cuenta_id)  # Pasar cuenta_id para listar pagos de esa cuenta

# Obtener saldo restante de una cuenta
@login_required
def obtener_saldo(request):
    cuenta_id = request.GET.get('cuenta_id')
    try:
        cuenta = CuentaPorPagar.objects.get(pk=cuenta_id)
        return JsonResponse({'saldo': cuenta.saldo_pendiente})
    except CuentaPorPagar.DoesNotExist:
        return JsonResponse({'error': 'Cuenta no encontrada'}, status=404)
