from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Proveedores
    path('proveedores/', views.listar_proveedores, name='listar_proveedores'),
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/editar/<uuid:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<uuid:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    # Cuentas por pagar
    path('cuentas/', views.listar_cuentas, name='listar_cuentas'),
    path('cuentas/nueva/', views.crear_cuenta, name='crear_cuenta'),
    path('cuentas/editar/<uuid:pk>/', views.editar_cuenta, name='editar_cuenta'),
    path('cuentas/eliminar/<uuid:pk>/', views.eliminar_cuenta, name='eliminar_cuenta'),

    # Pagos
    path('pagos/', views.listar_pagos, name='listar_pagos'),
    path('pagos/nuevo/', views.crear_pago, name='crear_pago'),
    path('pagos/eliminar/<uuid:pk>/', views.eliminar_pago, name='eliminar_pago'),
    path('obtener-saldo/', views.obtener_saldo, name='obtener_saldo'),

]