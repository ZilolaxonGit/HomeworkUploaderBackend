from rest_framework import serializers
from .models import Lesson
from users.serializers import TeacherSerializer
from groups.serializers import GroupMinimalSerializer


class LessonSerializer(serializers.ModelSerializer):

    teacher_details = TeacherSerializer(source='teacher', read_only=True)
    group_details = GroupMinimalSerializer(source='group', read_only=True)
    is_deadline_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'description', 'teacher', 'teacher_details',
                  'group', 'group_details', 'start_date', 'end_date', 'deadline',
                  'is_deadline_passed', 'is_active',
                  'homework_task', 'homework_image', 'allow_file_upload', 'allow_url_submission',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_deadline_passed')


class LessonListSerializer(serializers.ModelSerializer):

    teacher_details = TeacherSerializer(source='teacher', read_only=True)
    group_details = GroupMinimalSerializer(source='group', read_only=True)
    is_deadline_passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'description', 'teacher', 'teacher_details',
                  'group', 'group_details', 'start_date', 'end_date', 'deadline',
                  'is_deadline_passed', 'is_active',
                  'homework_task', 'homework_image', 'allow_file_upload', 'allow_url_submission')
