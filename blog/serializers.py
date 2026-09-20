
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, Patient, TimeSlot, Appointment


class UserSerializer(serializers.ModelSerializer):
    """用户序"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']


class DoctorSerializer(serializers.ModelSerializer):
    """医生"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialty', 'phone', 'bio']


class PatientSerializer(serializers.ModelSerializer):
    """患者"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'phone']


class AppointmentSlotSerializer(serializers.ModelSerializer):
    """时间段"""
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'date', 'start_time', 'is_available']


class AppointmentSerializer(serializers.ModelSerializer):
    """预约"""
    patient = PatientSerializer(read_only=True)
    time_slot = AppointmentSlotSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'time_slot', 'status', 'notes', 'created_at']