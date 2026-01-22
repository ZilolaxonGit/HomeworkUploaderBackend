from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User, Student, Teacher


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )


class StudentCreationForm(forms.ModelForm):

    username = forms.CharField(label='Username', max_length=150, help_text='Required. Username for login.')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, help_text='Required. Minimum 8 characters.')
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, help_text='Enter the same password again.')
    first_name = forms.CharField(label='First Name', max_length=150, required=False)
    last_name = forms.CharField(label='Last Name', max_length=150, required=False)
    email = forms.EmailField(label='Email', required=False)

    class Meta:
        model = Student
        fields = ('student_id', 'phone', 'date_of_birth', 'address')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            email=self.cleaned_data.get('email', ''),
            role=User.STUDENT
        )

        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student


class StudentChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text='Raw passwords are not stored. You can change the password using <a href="../password/">this form</a>.'
    )

    class Meta:
        model = Student
        fields = ('user', 'student_id', 'phone', 'date_of_birth', 'address')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    form = StudentChangeForm
    add_form = StudentCreationForm

    list_display = ('student_id', 'get_username', 'get_full_name', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'student_id', 'phone', 'date_of_birth', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('User Account', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email'),
        }),
        ('Student Information', {
            'classes': ('wide',),
            'fields': ('student_id', 'phone', 'date_of_birth', 'address'),
        }),
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

    def get_form(self, request, obj=None, **kwargs):
        """Use special form during student creation."""
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)


class TeacherCreationForm(forms.ModelForm):

    username = forms.CharField(label='Username', max_length=150, help_text='Required. Username for login.')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, help_text='Required. Minimum 8 characters.')
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, help_text='Enter the same password again.')
    first_name = forms.CharField(label='First Name', max_length=150, required=False)
    last_name = forms.CharField(label='Last Name', max_length=150, required=False)
    email = forms.EmailField(label='Email', required=False)

    class Meta:
        model = Teacher
        fields = ('employee_id', 'phone', 'specialization', 'bio')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            email=self.cleaned_data.get('email', ''),
            role=User.TEACHER
        )

        teacher = super().save(commit=False)
        teacher.user = user
        if commit:
            teacher.save()
        return teacher


class TeacherChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text='Raw passwords are not stored. You can change the password using <a href="../password/">this form</a>.'
    )

    class Meta:
        model = Teacher
        fields = ('user', 'employee_id', 'phone', 'specialization', 'bio')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):

    form = TeacherChangeForm
    add_form = TeacherCreationForm

    list_display = ('employee_id', 'get_username', 'get_full_name', 'phone', 'specialization', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'specialization')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Teacher Information', {
            'fields': ('user', 'employee_id', 'phone', 'specialization', 'bio')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('User Account', {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email'),
        }),
        ('Teacher Information', {
            'classes': ('wide',),
            'fields': ('employee_id', 'phone', 'specialization', 'bio'),
        }),
    )

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
