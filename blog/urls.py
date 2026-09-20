
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

# API路由
router = DefaultRouter()
router.register(r'doctors', api_views.DoctorViewSet, basename='doctor')
router.register(r'slots', api_views.AppointmentSlotViewSet, basename='slot')
router.register(r'appointments', api_views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    # ===== 患者功能 =====
    path('', views.home, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctor/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('book/<int:slot_id>/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('appointment/<int:appointment_id>/edit/', views.edit_appointment, name='edit_appointment'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),

    # ===== 用户认证 =====
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # ===== 医生功能 =====
    path('doctor/set-slot/', views.doctor_set_slot, name='doctor_set_slot'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/slot/<int:slot_id>/delete/', views.delete_slot, name='delete_slot'),

    # ===== 管理员功能 =====
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # 医生管理
    path('admin-dashboard/doctors/', views.manage_doctors, name='manage_doctors'),
    path('admin-dashboard/doctors/add/', views.add_doctor, name='add_doctor'),
    path('admin-dashboard/doctors/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),

    # 时间段管理
    path('admin-dashboard/slots/', views.manage_slots, name='manage_slots'),
    path('admin-dashboard/slots/add/', views.add_slot, name='add_slot'),
    path('admin-dashboard/slots/<int:slot_id>/delete/', views.admin_delete_slot, name='admin_delete_slot'),

    # 预约管理
    path('admin-dashboard/appointments/', views.manage_appointments, name='manage_appointments'),
    path('admin-dashboard/appointments/<int:appointment_id>/edit/', views.admin_edit_appointment,
         name='admin_edit_appointment'),
    path('admin-dashboard/appointments/<int:appointment_id>/cancel/', views.admin_cancel_appointment,
         name='admin_cancel_appointment'),

    # 患者管理
    path('admin-dashboard/patients/', views.manage_patients, name='manage_patients'),
    path('admin-dashboard/patients/<int:patient_id>/toggle/', views.toggle_patient, name='toggle_patient'),


    #  API
    path('api/', include(router.urls)),
    path('api/doctors/<int:doctor_id>/available-slots/', api_views.available_slots, name='api_available_slots'),
]