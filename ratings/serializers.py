from rest_framework import serializers
from .models import Rating, DailyLeaderboard
from homework.models import Homework


class RatingSerializer(serializers.ModelSerializer):

    teacher_name = serializers.SerializerMethodField(read_only=True)
    student_name = serializers.SerializerMethodField(read_only=True)
    homework_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Rating
        fields = ('id', 'homework', 'homework_details', 'teacher', 'teacher_name',
                  'student', 'student_name', 'score', 'comment', 'rating_date',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'teacher', 'student', 'rating_date', 'created_at', 'updated_at')

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name() or obj.teacher.user.username
        return None

    def get_student_name(self, obj):
        if obj.student and obj.student.user:
            return obj.student.user.get_full_name() or obj.student.user.username
        return None

    def get_homework_details(self, obj):
        return {
            'id': obj.homework.id,
            'lesson_title': obj.homework.lesson.title,
            'student_id': obj.homework.student.student_id
        }

    def create(self, validated_data):
        homework = validated_data.get('homework')
        validated_data['student'] = homework.student

        rating = super().create(validated_data)

        homework.status = Homework.STATUS_RATED
        homework.save()

        return rating


class DailyLeaderboardSerializer(serializers.ModelSerializer):

    student_id = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.SerializerMethodField(read_only=True)
    student_details = serializers.SerializerMethodField(read_only=True)
    group_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DailyLeaderboard
        fields = ('id', 'student', 'student_id', 'student_name', 'student_details',
                  'group', 'group_details', 'date', 'average_score', 'rank',
                  'total_ratings', 'is_top_three')
        read_only_fields = ('id', 'is_top_three')

    def get_student_name(self, obj):
        if obj.student and obj.student.user:
            return obj.student.user.get_full_name() or obj.student.user.username
        return None

    def get_student_details(self, obj):
        if obj.student and obj.student.user:
            return {
                'username': obj.student.user.username,
                'first_name': obj.student.user.first_name,
                'last_name': obj.student.user.last_name,
            }
        return None

    def get_group_details(self, obj):
        if obj.group:
            return {
                'id': obj.group.id,
                'name': obj.group.name,
            }
        return None
