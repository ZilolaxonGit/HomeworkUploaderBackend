from django.db import models
from django.utils import timezone
from users.models import Teacher


class Lesson(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='lessons')
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lessons'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True, help_text='Deadline for homework submission')
    is_active = models.BooleanField(default=True)

    @property
    def is_deadline_passed(self):
        if self.deadline:
            return timezone.now() > self.deadline
        return False

    homework_task = models.TextField(blank=True, help_text='Description of what students should do')
    homework_image = models.ImageField(upload_to='homework_tasks/', blank=True, null=True, help_text='Optional image for the homework task')
    allow_file_upload = models.BooleanField(default=True, help_text='Whether students can upload files')
    allow_url_submission = models.BooleanField(default=True, help_text='Whether students can submit URLs')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lessons'
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
