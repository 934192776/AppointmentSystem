

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from .models import Doctor, Patient, TimeSlot, Appointment
from .forms import (
    PatientRegistrationForm,
    DoctorCreationForm,
    TimeSlotForm,
    AppointmentForm
)


# 检查用户角色

def is_admin(user):
    """检查是否是管理员（超级用户）"""
    return user.is_superuser


def is_doctor(user):
    """检查是否是医生（员工但不是超级用户）"""
    return user.is_staff and not user.is_superuser


def is_patient(user):
    """检查是否是患者（普通用户）"""
    return not user.is_staff


# 患者功能

def home(request):
    """
    首页
    显示欢迎信息和医生列表
    """
    # 获取所有医生
    doctors = Doctor.objects.all()

    context = {
        'doctors': doctors,
    }
    return render(request, 'home.html', context)


def doctor_list(request):
    """
    医生列表页
    显示所有医生
    """
    doctors = Doctor.objects.all()
    return render(request, 'doctor_list.html', {'doctors': doctors})


def doctor_detail(request, doctor_id):
    """
    医生详情页
    显示医生信息和可预约时间段
    """
    # 根据ID获取医生，如果不存在返回404
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # 获取今天及以后的可预约时间段
    today = timezone.now().date()
    available_slots = TimeSlot.objects.filter(
        doctor=doctor,
        date__gte=today,  # 今天或以后
        is_available=True  # 可预约的
    ).order_by('date', 'start_time')

    context = {
        'doctor': doctor,
        'available_slots': available_slots,
    }
    return render(request, 'doctor_detail.html', context)


@login_required
def book_appointment(request, slot_id):
    """
    预约功能
    患者预约某个时间段
    需要登录才能访问
    """
    # 获取时间段
    slot = get_object_or_404(TimeSlot, id=slot_id)

    # 检查时间段是否可用
    if not slot.is_available:
        messages.error(request, '该时间段已被预约')
        return redirect('doctor_detail', doctor_id=slot.doctor.id)

    # 检查是否已经被预约
    if Appointment.objects.filter(time_slot=slot).exists():
        messages.error(request, '该时间段已被预约')
        return redirect('doctor_detail', doctor_id=slot.doctor.id)

    # 获取或创建当前用户的Patient资料
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # 创建预约
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.time_slot = slot
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
    return render(request, 'book_appointment.html', context)


@login_required
def my_appointments(request):
    """
    我的预约
    显示当前患者的所有预约
    """
    # 获取或创建患者资料
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    # 获取该患者的所有预约
    appointments = Appointment.objects.filter(
        patient=patient
    ).order_by('-time_slot__date', '-time_slot__start_time')

    context = {
        'appointments': appointments,
    }
    return render(request, 'my_appointments.html', context)


@login_required
def edit_appointment(request, appointment_id):
    """
    患者编辑预约
    只能改备注，不能改状态
    """
    # 获取患者资料
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    # 获取该患者的预约
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=patient
    )

    # 已取消的预约不能编辑
    if appointment.status == 'Cancelled':
        messages.error(request, '已取消的预约不能编辑')
        return redirect('my_appointments')

    if request.method == 'POST':
        # 只更新备注
        appointment.notes = request.POST.get('notes', '')
        appointment.save()
        messages.success(request, '预约已更新！')
        return redirect('my_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'patient_edit_appointment.html', context)


@login_required
def cancel_appointment(request, appointment_id):
    """
    患者取消预约
    """
    # 获取患者资料
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    # 获取预约
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient=patient
    )

    if request.method == 'POST':
        # 标记为已取消
        appointment.status = 'Cancelled'
        appointment.save()

        # 释放时间段
        appointment.time_slot.is_available = True
        appointment.time_slot.save()

        messages.success(request, '预约已取消')
        return redirect('my_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'cancel_appointment.html', context)


# 医生功能

@login_required
@user_passes_test(is_doctor)
def doctor_set_slot(request):
    """
    医生设置时间段
    医生只能给自己设置
    """
    # 获取当前医生的资料
    doctor = get_object_or_404(Doctor, user=request.user)

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            # 创建时间段
            slot = form.save(commit=False)
            slot.doctor = doctor  # 强制设置当前医生
            slot.save()
            messages.success(request, '时间段已创建！')
            return redirect('doctor_set_slot')
    else:
        form = TimeSlotForm()
        # 只显示当前医生选项
        form.fields['doctor'].queryset = Doctor.objects.filter(user=request.user)
        form.fields['doctor'].initial = doctor

    # 获取当前医生的所有时间段
    slots = TimeSlot.objects.filter(
        doctor=doctor
    ).order_by('-date', '-start_time')

    context = {
        'form': form,
        'slots': slots,
    }
    return render(request, 'set_slot.html', context)


@login_required
@user_passes_test(is_doctor)
def doctor_appointments(request):
    """
    医生查看自己的预约
    """
    # 获取当前医生资料
    doctor = get_object_or_404(Doctor, user=request.user)

    # 获取该医生的所有预约
    appointments = Appointment.objects.filter(
        time_slot__doctor=doctor
    ).order_by('-time_slot__date', '-time_slot__start_time')

    context = {
        'appointments': appointments,
    }
    return render(request, 'doctor_appointments.html', context)


@login_required
@user_passes_test(is_doctor)
def delete_slot(request, slot_id):
    """
    医生删除自己的时间段
    """
    doctor = get_object_or_404(Doctor, user=request.user)
    slot = get_object_or_404(TimeSlot, id=slot_id, doctor=doctor)

    if request.method == 'POST':
        slot.delete()
        messages.success(request, '时间段已删除')
        return redirect('doctor_set_slot')

    context = {
        'slot': slot,
    }
    return render(request, 'delete_slot.html', context)


# 用户认证

def register(request):
    """
    患者注册
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            # 创建用户
            user = form.save()

            # 添加到 patient 组
            group, created = Group.objects.get_or_create(name='patient')
            user.groups.add(group)

            # 创建 Patient资料
            Patient.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', '')
            )

            # 自动登录
            login(request, user)

            messages.success(request, '注册成功！')
            return redirect('home')
    else:
        form = PatientRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    """
    用户登录
    根据角色跳转到不同页面
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 验证用户
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{username}！')

            # 根据角色跳转
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.is_staff:
                return redirect('doctor_set_slot')
            else:
                return redirect('home')
        else:
            messages.error(request, '用户名或密码错误')

    return render(request, 'login.html')


def user_logout(request):
    """
    用户登出
    """
    logout(request)
    messages.success(request, '已成功登出')
    return redirect('home')


# 管理员功能

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    管理员仪表盘
    显示统计信息
    """
    # 统计
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='Booked').count()

    # 最近预约
    recent_appointments = Appointment.objects.all().order_by('-created_at')[:5]

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'dashboard.html', context)


# ===== 医生管理 =====

@login_required
@user_passes_test(is_admin)
def manage_doctors(request):
    """
    管理医生列表
    """
    doctors = Doctor.objects.all()
    return render(request, 'manage_doctors.html', {'doctors': doctors})


@login_required
@user_passes_test(is_admin)
def add_doctor(request):
    """
    添加医生
    同时创建User和Doctor
    """
    if request.method == 'POST':
        form = DoctorCreationForm(request.POST)
        if form.is_valid():
            doctor = form.save()

            # 添加到 doctor 组
            group, created = Group.objects.get_or_create(name='doctor')
            doctor.user.groups.add(group)

            messages.success(request, '医生添加成功！')
            return redirect('manage_doctors')
    else:
        form = DoctorCreationForm()

    return render(request, 'add_doctor.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def delete_doctor(request, doctor_id):
    """
    删除医生
    """
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method == 'POST':
        user = doctor.user
        doctor.delete()
        user.delete()
        messages.success(request, '医生已删除')
        return redirect('manage_doctors')

    context = {
        'doctor': doctor,
    }
    return render(request, 'delete_doctor.html', context)


# ===== 时间段管理 =====

@login_required
@user_passes_test(is_admin)
def manage_slots(request):
    """
    管理所有时间段
    """
    slots = TimeSlot.objects.all().order_by('-date', '-start_time')
    return render(request, 'manage_slots.html', {'slots': slots})


@login_required
@user_passes_test(is_admin)
def add_slot(request):
    """
    添加时间段（管理员）
    """
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '时间段添加成功！')
            return redirect('manage_slots')
    else:
        form = TimeSlotForm()

    return render(request, 'add_slot.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_delete_slot(request, slot_id):
    """
    管理员删除时间段
    """
    slot = get_object_or_404(TimeSlot, id=slot_id)

    if request.method == 'POST':
        slot.delete()
        messages.success(request, '时间段已删除')
        return redirect('manage_slots')

    context = {
        'slot': slot,
    }
    return render(request, 'delete_slot.html', context)


# ===== 预约管理 =====

@login_required
@user_passes_test(is_admin)
def manage_appointments(request):
    """
    管理所有预约
    """
    appointments = Appointment.objects.all().order_by('-created_at')
    return render(request, 'manage_appointments.html', {
        'appointments': appointments
    })


@login_required
@user_passes_test(is_admin)
def admin_edit_appointment(request, appointment_id):
    """
    管理员编辑预约
    可以改状态和备注
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes')

        appointment.status = status
        appointment.notes = notes
        appointment.save()

        # 如果取消预约，释放时间段
        if status == 'Cancelled':
            appointment.time_slot.is_available = True
            appointment.time_slot.save()

        messages.success(request, '预约已更新！')
        return redirect('manage_appointments')

    context = {
        'appointment': appointment,
        'status_choices': Appointment.STATUS_CHOICES,
    }
    return render(request, 'admin_edit_appointment.html', context)


@login_required
@user_passes_test(is_admin)
def admin_cancel_appointment(request, appointment_id):
    """
    管理员取消预约
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        appointment.status = 'Cancelled'
        appointment.save()

        # 释放时间段
        appointment.time_slot.is_available = True
        appointment.time_slot.save()

        messages.success(request, '预约已取消')
        return redirect('manage_appointments')

    context = {
        'appointment': appointment,
    }
    return render(request, 'cancel_appointment.html', context)


# ===== 患者管理 =====

@login_required
@user_passes_test(is_admin)
def manage_patients(request):
    """
    管理患者账号
    """
    patients = Patient.objects.all().order_by('-created_at')
    return render(request, 'manage_patients.html', {'patients': patients})


@login_required
@user_passes_test(is_admin)
def toggle_patient(request, patient_id):
    """
    启用/禁用患者账号
    """
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        patient.user.is_active = not patient.user.is_active
        patient.user.save()

        status = "启用" if patient.user.is_active else "禁用"
        messages.success(request, f'患者账号已{status}')
        return redirect('manage_patients')

    context = {
        'patient': patient,
    }
    return render(request, 'toggle_patient.html', context)