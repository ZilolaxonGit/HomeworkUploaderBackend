from django.db import models


class Group(models.Model):

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        'users.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_groups'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'groups'
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        """Return the number of students in this group."""
        return self.students.count()
