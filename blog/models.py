# clinic/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Doctor(models.Model):
    """
    医生模型
    存储医生的信息
    """
    # 一对一关联Django内置用户表
    # 一个用户对应一个医生资料
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )

    # 医生的科室（比如：内科、外科、儿科）
    specialty = models.CharField(max_length=100)

    # 医生的联系电话
    phone = models.CharField(max_length=20)

    # 医生的个人简介
    bio = models.TextField(blank=True)

    # 医生创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # 显示医生的用户名
        return f"Dr. {self.user.username}"

    class Meta:
        # 按创建时间倒序排列（最新的在前）
        ordering = ['-created_at']


class AppointmentSlot(models.Model):
    """
    预约时间段模型
    管理员创建可预约的时间段
    一个医生可以有多个时间段
    """
    # 外键关联医生
    # 一个医生可以有多个时间段
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='slots'
    )

    # 预约日期
    date = models.DateField()

    # 预约时间
    time = models.TimeField()

    # 时间段是否可用
    # True = 可预约，False = 已被预约或不可用
    is_available = models.BooleanField(default=True)

    # 时间段创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # 显示医生、日期和时间
        return f"{self.doctor.user.username} - {self.date} {self.time}"

    class Meta:
        # 同一个医生、同一天、同一时间只能有一个时间段
        unique_together = ['doctor', 'date', 'time']
        # 按日期和时间排序
        ordering = ['date', 'time']


class Appointment(models.Model):
    """
    预约模型
    患者预约医生
    """
    # 预约状态选项
    STATUS_CHOICES = [
        ('pending', '待确认'),  # 刚预约，等待确认
        ('confirmed', '已确认'),  # 管理员确认
        ('completed', '已完成'),  # 就诊完成
        ('cancelled', '已取消'),  # 已取消
    ]

    # 外键关联患者（用户）
    # 一个患者可以有多个预约
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    # 外键关联时间段
    # 一个时间段只能被预约一次
    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.CASCADE,
        related_name='appointment'
    )

    # 预约状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # 患者备注（比如：哪里不舒服）
    notes = models.TextField(blank=True)

    # 预约创建时间
    created_at = models.DateTimeField(auto_now_add=True)

    # 预约更新时间
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.username} - {self.slot.doctor.user.username} - {self.slot.date}"

    class Meta:
        ordering = ['-created_at']