from rest_framework import serializers
from .models import Group


class GroupMinimalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'name')


class GroupSerializer(serializers.ModelSerializer):

    teacher_details = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'description', 'teacher', 'teacher_details',
                  'is_active', 'student_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_teacher_details(self, obj):
        if obj.teacher:
            return {
                'id': obj.teacher.id,
                'employee_id': obj.teacher.employee_id,
                'user': {
                    'id': obj.teacher.user.id,
                    'username': obj.teacher.user.username,
                    'first_name': obj.teacher.user.first_name,
                    'last_name': obj.teacher.user.last_name,
                    'email': obj.teacher.user.email,
                }
            }
        return None


class GroupListSerializer(serializers.ModelSerializer):

    teacher_name = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'description', 'teacher', 'teacher_name',
                  'is_active', 'student_count')

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name() or obj.teacher.user.username
        return None
