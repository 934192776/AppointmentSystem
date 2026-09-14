# AppointmentSystem/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),          # Django自带后台（仅开发用）
    path('', include('clinic.urls')),          # 我们的应用
]