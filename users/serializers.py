from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Student, Teacher
from groups.serializers import GroupMinimalSerializer


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class StudentSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    group_details = GroupMinimalSerializer(source='group', read_only=True)

    class Meta:
        model = Student
        fields = ('id', 'user', 'student_id', 'group', 'group_details', 'phone', 'date_of_birth', 'address',
                  'username', 'password', 'first_name', 'last_name', 'email',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        email = validated_data.pop('email', '')

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=User.STUDENT
        )

        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        email = validated_data.pop('email', None)

        if username:
            instance.user.username = username
        if password:
            instance.user.set_password(password)
        if first_name is not None:
            instance.user.first_name = first_name
        if last_name is not None:
            instance.user.last_name = last_name
        if email is not None:
            instance.user.email = email

        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class TeacherSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ('id', 'user', 'employee_id', 'phone', 'specialization', 'bio',
                  'username', 'password', 'first_name', 'last_name', 'email',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        email = validated_data.pop('email', '')

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=User.TEACHER
        )

        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher

    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        email = validated_data.pop('email', None)

        if username:
            instance.user.username = username
        if password:
            instance.user.set_password(password)
        if first_name is not None:
            instance.user.first_name = first_name
        if last_name is not None:
            instance.user.last_name = last_name
        if email is not None:
            instance.user.email = email

        instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
