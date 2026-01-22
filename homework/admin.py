from django.contrib import admin
from .models import Homework


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):

    list_display = ('student', 'lesson', 'status', 'has_submission', 'submitted_at', 'created_at')
    list_filter = ('status', 'submitted_at', 'created_at')
    search_fields = ('student__student_id', 'lesson__title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def has_submission(self, obj):
        return obj.has_submission
    has_submission.boolean = True
    has_submission.short_description = 'Has Submission'
