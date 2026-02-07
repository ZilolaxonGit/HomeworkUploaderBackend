from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Teacher, Student
from homework.models import Homework


class Rating(models.Model):

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='ratings')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='ratings_given')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ratings_received')
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Rating from 1 to 10'
    )
    comment = models.TextField(blank=True)
    rating_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ratings'
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        ordering = ['-created_at']
        unique_together = ['homework', 'teacher']

    def __str__(self):
        return f"{self.student.user.username} - {self.score}/10 by {self.teacher.user.username}"


class DailyLeaderboard(models.Model):

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leaderboard_entries')
    group = models.ForeignKey(
        'groups.Group',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries'
    )
    date = models.DateField()
    average_score = models.DecimalField(max_digits=4, decimal_places=2)
    rank = models.IntegerField()
    total_ratings = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_leaderboard'
        verbose_name = 'Daily Leaderboard'
        verbose_name_plural = 'Daily Leaderboards'
        ordering = ['date', 'rank']
        unique_together = ['student', 'date', 'group']

    def __str__(self):
        return f"{self.date} - Rank {self.rank}: {self.student.user.username} ({self.average_score})"

    @property
    def is_top_three(self):
        return self.rank <= 3
