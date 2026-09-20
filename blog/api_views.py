from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Doctor, TimeSlot, Appointment
from .serializers import (
    DoctorSerializer,
    AppointmentSlotSerializer,
    AppointmentSerializer
)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    医生API
    GET /api/doctors/          - 获取所有医生
    GET /api/doctors/1/        - 获取单个医生
    POST /api/doctors/         - 创建医生
    PUT /api/doctors/1/        - 更新医生
    DELETE /api/doctors/1/     - 删除医生
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AppointmentSlotViewSet(viewsets.ModelViewSet):
    """
    时间段API
    GET /api/slots/            - 获取所有时间段
    GET /api/slots/1/          - 获取单个时间段
    """
    queryset = TimeSlot.objects.all()
    serializer_class = AppointmentSlotSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    预约API
    根据用户角色返回不同的预约
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            # 管理员：所有预约
            return Appointment.objects.all()
        elif user.is_staff:
            # 医生：自己的预约
            return Appointment.objects.filter(time_slot__doctor__user=user)
        else:
            # 患者：自己的预约
            return Appointment.objects.filter(patient__user=user)


@api_view(['GET'])
def available_slots(request, doctor_id):
    """
    获取某医生的可用时间段
    GET /api/doctors/1/available-slots/
    """
    slots = TimeSlot.objects.filter(
        doctor_id=doctor_id,
        is_available=True
    )
    serializer = AppointmentSlotSerializer(slots, many=True)
    return Response(serializer.data)