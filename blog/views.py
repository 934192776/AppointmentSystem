from django.shortcuts import render

# Create your views here.
# clinic/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Doctor, AppointmentSlot, Appointment
from .forms import (
    PatientRegistrationForm, DoctorForm,
    AppointmentSlotForm, AppointmentForm
)


# ============================================
# 辅助函数：检查是否是管理员
# ============================================

def is_admin(user):
    """检查用户是否是管理员（员工）"""
    return user.is_staff


def is_patient(user):
    """检查用户是否是患者（非员工）"""
    return not user.is_staff


# ============================================
# 患者功能
# ============================================

def home(request):
    """
    首页
    显示欢迎信息和可预约的医生
    """
    # 获取所有医生
    doctors = Doctor.objects.all()

    context = {
        'doctors': doctors,
        'user': request.user,
    }
    return render(request, 'clinic/home.html', context)


def doctor_list(request):
    """
    医生列表页
    显示所有医生和他们的科室
    """
    doctors = Doctor.objects.all()
    return render(request, 'clinic/doctor_list.html', {'doctors': doctors})


def doctor_detail(request, doctor_id):
    """
    医生详情页
    显示医生的信息和可预约时间段
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # 获取该医生未来可用的时间段
    today = timezone.now().date()
    available_slots = AppointmentSlot.objects.filter(
        doctor=doctor,
        date__gte=today,  # 今天或以后
        is_available=True  # 可预约的
    ).order_by('date', 'time')

    context = {
        'doctor': doctor,
        'available_slots': available_slots,
    }
    return render(request, 'clinic/doctor_detail.html', context)


@login_required
def book_appointment(request, slot_id):
    """
    预约功能
    患者预约某个时间段
    需要登录才能访问
    """
    # 获取时间段
    slot = get_object_or_404(AppointmentSlot, id=slot_id)

    # 检查时间段是否可用
    if not slot.is_available:
        messages.error(request, '该时间段已被预约')
        return redirect('doctor_detail', doctor_id=slot.doctor.id)

    # 检查是否已经预约过这个时间段
    if Appointment.objects.filter(slot=slot).exists():
        messages.error(request, '该时间段已被预约')
        return redirect('doctor_detail', doctor_id=slot.doctor.id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # 创建预约
            appointment = form.save(commit=False)
            appointment.patient = request.user  # 设置患者
            appointment.slot = slot  # 设置时间段
            appointment.save()

            # 标记时间段为不可用
            slot.is_available = False
            slot.save()

            messages.success(request, '预约成功！')
            return redirect('my_appointments')
    else:
        form = AppointmentForm()

    context = {
        'slot': slot,
        'form': form,
    }
    return render(request, 'clinic/book_appointment.html', context)


@login_required
def my_appointments(request):
    """
    我的预约
    显示当前用户的所有预约
    """
    # 获取当前用户的所有预约
    appointments = Appointment.objects.filter(
        patient=request.user
    ).order_by('-slot__date', '-slot__time')

    context = {
        'appointments': appointments,
    }
    return render(request, 'clinic/my_appointments.html', context)


@login_required
def edit_appointment(request, appointment_id):
    """
    编辑预约
    患者可以编辑自己的预约（只能改备注）
    """
    # 获取预约，确保是当前用户的
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user
    )

    # 检查预约状态
    if appointment.status == 'cancelled':
        messages.error(request, '已取消的预约不能编辑')
        return redirect('my_appointments')

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, '预约已更新！')
            return redirect('my_appointments')
    else:
        form = AppointmentForm(instance=appointment)

    context = {
        'appointment': appointment,
        'form': form,
    }
    return render(request, 'clinic/edit_appointment.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    """
    取消预约
    患者可以取消自己的预约
    """
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=request.user
    )

    if request.method == 'POST':
        # 标记预约为已取消
        appointment.status = 'cancelled'
        appointment.save()

        # 释放时间段
        appointment.slot.is_available = True
        appointment.slot.save()

        messages.success(request, '预约已取消')
        return redirect('my_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'clinic/cancel_appointment.html', context)


# ============================================
# 用户注册/登录
# ============================================

def register(request):
    """
    患者注册
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # 保存用户
            user = form.save()

            # 自动登录
            login(request, user)

            messages.success(request, '注册成功！')
            return redirect('home')
    else:
        form = PatientRegistrationForm()

    return render(request, 'clinic/register.html', {'form': form})


def user_login(request):
    """
    用户登录
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{username}！')
            return redirect('home')
        else:
            messages.error(request, '用户名或密码错误')

    return render(request, 'clinic/login.html')


def user_logout(request):
    """
    用户登出
    """
    logout(request)
    messages.success(request, '已成功登出')
    return redirect('home')


# ============================================
# 管理员功能（自定义仪表盘）
# ============================================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    管理员仪表盘
    显示统计信息
    """
    # 统计数据
    total_doctors = Doctor.objects.count()
    total_patients = User.objects.filter(is_staff=False).count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()

    # 最近预约
    recent_appointments = Appointment.objects.all().order_by('-created_at')[:5]

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


# ===== 医生管理 =====

@login_required
@user_passes_test(is_admin)
def manage_doctors(request):
    """
    管理医生列表
    """
    doctors = Doctor.objects.all()
    return render(request, 'admin_dashboard/manage_doctors.html', {'doctors': doctors})


@login_required
@user_passes_test(is_admin)
def add_doctor(request):
    """
    添加医生
    """
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '医生添加成功！')
            return redirect('manage_doctors')
    else:
        form = DoctorForm()

    return render(request, 'admin_dashboard/add_doctor.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def edit_doctor(request, doctor_id):
    """
    编辑医生
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, '医生信息已更新！')
            return redirect('manage_doctors')
    else:
        form = DoctorForm(instance=doctor)

    return render(request, 'admin_dashboard/edit_doctor.html', {
        'form': form,
        'doctor': doctor
    })


@login_required
@user_passes_test(is_admin)
def delete_doctor(request, doctor_id):
    """
    删除医生
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == 'POST':
        doctor.delete()
        messages.success(request, '医生已删除')
        return redirect('manage_doctors')

    return render(request, 'admin_dashboard/delete_doctor.html', {'doctor': doctor})


# ===== 时间段管理 =====

@login_required
@user_passes_test(is_admin)
def manage_slots(request):
    """
    管理预约时间段
    """
    slots = AppointmentSlot.objects.all().order_by('-date', '-time')
    return render(request, 'admin_dashboard/manage_slots.html', {'slots': slots})


@login_required
@user_passes_test(is_admin)
def add_slot(request):
    """
    添加时间段
    """
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '时间段添加成功！')
            return redirect('manage_slots')
    else:
        form = AppointmentSlotForm()

    return render(request, 'admin_dashboard/add_slot.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def delete_slot(request, slot_id):
    """
    删除时间段
    """
    slot = get_object_or_404(AppointmentSlot, id=slot_id)

    if request.method == 'POST':
        slot.delete()
        messages.success(request, '时间段已删除')
        return redirect('manage_slots')

    return render(request, 'admin_dashboard/delete_slot.html', {'slot': slot})


# ===== 预约管理 =====

@login_required
@user_passes_test(is_admin)
def manage_appointments(request):
    """
    管理所有预约
    """
    appointments = Appointment.objects.all().order_by('-created_at')
    return render(request, 'admin_dashboard/manage_appointments.html', {
        'appointments': appointments
    })


@login_required
@user_passes_test(is_admin)
def admin_edit_appointment(request, appointment_id):
    """
    管理员编辑预约
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        # 获取表单数据
        status = request.POST.get('status')
        notes = request.POST.get('notes')

        appointment.status = status
        appointment.notes = notes
        appointment.save()

        # 如果取消预约，释放时间段
        if status == 'cancelled':
            appointment.slot.is_available = True
            appointment.slot.save()

        messages.success(request, '预约已更新！')
        return redirect('manage_appointments')

    return render(request, 'admin_dashboard/edit_appointment.html', {
        'appointment': appointment,
        'status_choices': Appointment.STATUS_CHOICES
    })


@login_required
@user_passes_test(is_admin)
def admin_cancel_appointment(request, appointment_id):
    """
    管理员取消预约
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()

        # 释放时间段
        appointment.slot.is_available = True
        appointment.slot.save()

        messages.success(request, '预约已取消')
        return redirect('manage_appointments')

    return render(request, 'admin_dashboard/cancel_appointment.html', {
        'appointment': appointment
    })


# ===== 患者管理 =====

@login_required
@user_passes_test(is_admin)
def manage_patients(request):
    """
    管理患者账号
    """
    patients = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'admin_dashboard/manage_patients.html', {
        'patients': patients
    })


@login_required
@user_passes_test(is_admin)
def toggle_patient(request, patient_id):
    """
    启用/禁用患者账号
    """
    patient = get_object_or_404(User, id=patient_id)

    if request.method == 'POST':
        patient.is_active = not patient.is_active
        patient.save()

        status = "启用" if patient.is_active else "禁用"
        messages.success(request, f'患者账号已{status}')
        return redirect('manage_patients')

    return render(request, 'admin_dashboard/toggle_patient.html', {
        'patient': patient
    })