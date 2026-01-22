from rest_framework import serializers
from .models import Homework
from users.serializers import StudentSerializer
from lessons.serializers import LessonListSerializer


class HomeworkSerializer(serializers.ModelSerializer):

    student_details = StudentSerializer(source='student', read_only=True)
    lesson_details = LessonListSerializer(source='lesson', read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Homework
        fields = ('id', 'student', 'student_details', 'lesson', 'lesson_details',
                  'submission_url', 'submission_file', 'description', 'status',
                  'submitted_at', 'created_at', 'updated_at', 'rating')
        read_only_fields = ('id', 'student', 'status', 'submitted_at', 'created_at', 'updated_at')

    def get_rating(self, obj):
        """Get the rating for this homework if it exists."""
        rating = obj.ratings.first() if hasattr(obj, 'ratings') else None
        if rating:
            return {
                'id': rating.id,
                'score': rating.score,
                'comment': rating.comment,
                'rating_date': rating.rating_date,
            }
        return None

    def create(self, validated_data):
        """Create homework and set status to SUBMITTED if submission provided."""
        if validated_data.get('submission_url') or validated_data.get('submission_file'):
            validated_data['status'] = Homework.STATUS_SUBMITTED
            from django.utils import timezone
            validated_data['submitted_at'] = timezone.now()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'submission_url' in validated_data or 'submission_file' in validated_data:
            if validated_data.get('submission_url') or validated_data.get('submission_file'):
                instance.status = Homework.STATUS_SUBMITTED
                from django.utils import timezone
                instance.submitted_at = timezone.now()

        return super().update(instance, validated_data)


class HomeworkListSerializer(serializers.ModelSerializer):

    student_details = StudentSerializer(source='student', read_only=True)
    lesson_details = LessonListSerializer(source='lesson', read_only=True)
    student_name = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Homework
        fields = ('id', 'student_details', 'lesson_details', 'student_name', 'lesson_title',
                  'submission_url', 'submission_file', 'description', 'status',
                  'submitted_at', 'created_at', 'rating')

    def get_student_name(self, obj):
        if obj.student and obj.student.user:
            return obj.student.user.get_full_name() or obj.student.user.username
        return None

    def get_rating(self, obj):
        rating = obj.ratings.first() if hasattr(obj, 'ratings') else None
        if rating:
            return {
                'id': rating.id,
                'score': rating.score,
                'comment': rating.comment,
                'rating_date': rating.rating_date,
            }
        return None
