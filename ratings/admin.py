from django.contrib import admin
from .models import Rating, DailyLeaderboard


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):

    list_display = ('student', 'homework', 'teacher', 'score', 'rating_date', 'created_at')
    list_filter = ('score', 'rating_date', 'created_at')
    search_fields = ('student__student_id', 'teacher__employee_id', 'homework__lesson__title')
    ordering = ('-created_at',)
    readonly_fields = ('rating_date', 'created_at', 'updated_at')


@admin.register(DailyLeaderboard)
class DailyLeaderboardAdmin(admin.ModelAdmin):

    list_display = ('date', 'rank', 'student', 'average_score', 'total_ratings', 'is_top_three')
    list_filter = ('date', 'rank')
    search_fields = ('student__student_id', 'student__user__username')
    ordering = ('date', 'rank')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)

    def is_top_three(self, obj):
        return obj.is_top_three
    is_top_three.boolean = True
    is_top_three.short_description = 'Top 3'
