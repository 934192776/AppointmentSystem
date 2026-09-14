# clinic/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Doctor, AppointmentSlot, Appointment


class PatientRegistrationForm(UserCreationForm):
    """
    患者注册表单
    继承Django的UserCreationForm，自动处理密码验证
    """
    # 邮箱字段（必填）
    email = forms.EmailField(required=True)

    # 手机号字段（选填）
    phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        # 表单显示的字段
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给所有字段添加CSS类
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class DoctorForm(forms.ModelForm):
    """
    医生表单
    管理员用来添加/编辑医生
    """

    class Meta:
        model = Doctor
        fields = ['user', 'specialty', 'phone', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AppointmentSlotForm(forms.ModelForm):
    """
    预约时间段表单
    管理员用来创建时间段
    """

    class Meta:
        model = AppointmentSlot
        fields = ['doctor', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AppointmentForm(forms.ModelForm):
    """
    预约表单
    患者用来预约
    """

    class Meta:
        model = Appointment
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '请描述您的症状（选填）'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})