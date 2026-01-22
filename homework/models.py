from django.db import models
from users.models import Student
from lessons.models import Lesson


class Homework(models.Model):

    STATUS_PENDING = 'PENDING'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_RATED = 'RATED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_RATED, 'Rated'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homeworks')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='homeworks')
    submission_url = models.URLField(blank=True, null=True)
    submission_file = models.FileField(upload_to='homework_files/', blank=True, null=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homeworks'
        verbose_name = 'Homework'
        verbose_name_plural = 'Homeworks'
        ordering = ['-created_at']
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student.student_id} - {self.lesson.title}"

    @property
    def has_submission(self):
        """Check if homework has either URL or file submission."""
        return bool(self.submission_url or self.submission_file)
