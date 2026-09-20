from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin 仅用于开发和测试，不作为系统的管理员界面
    # 管理员界面是自定义的 /admin-dashboard/
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),
]