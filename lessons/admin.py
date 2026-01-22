from django.contrib import admin
from .models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):

    list_display = ('title', 'teacher', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'start_date', 'created_at')
    search_fields = ('title', 'description', 'teacher__user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'start_date'
