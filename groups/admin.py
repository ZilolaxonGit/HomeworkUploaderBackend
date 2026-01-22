from django.contrib import admin
from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'is_active', 'student_count', 'created_at')
    list_filter = ('is_active', 'teacher')
    search_fields = ('name', 'description')
    ordering = ('name',)

    def student_count(self, obj):
        return obj.student_count
    student_count.short_description = 'Students'
