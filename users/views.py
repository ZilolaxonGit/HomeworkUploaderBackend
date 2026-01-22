from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User, Student, Teacher
from .serializers import (
    UserSerializer, StudentSerializer, TeacherSerializer, LoginSerializer
)
from .permissions import IsAdmin, IsStudent, IsOwnerOrAdmin


@extend_schema(
    tags=['Authentication'],
    summary='Login',
    description='Authenticate a user and receive JWT tokens. Works for Admin, Teacher, and Student roles.',
    request=LoginSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
        403: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Successful Login',
            value={
                'user': {'id': 1, 'username': 'admin', 'role': 'admin'},
                'tokens': {'refresh': 'token...', 'access': 'token...'}
            },
            response_only=True,
        ),
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login endpoint for all users (Admin, Teacher, Student)."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    try:
        user_exists = User.objects.get(username=username)
        print(f"DEBUG: User found: {user_exists.username}, role: {user_exists.role}, is_active: {user_exists.is_active}")
        print(f"DEBUG: Has usable password: {user_exists.has_usable_password()}")
    except User.DoesNotExist:
        print(f"DEBUG: User '{username}' not found in database")
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    user = authenticate(username=username, password=password)
    print(f"DEBUG: authenticate() result: {user}")

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)

    user_data = UserSerializer(user).data

    if user.is_student and hasattr(user, 'student_profile'):
        user_data['student_profile'] = {
            'id': user.student_profile.id,
            'student_id': user.student_profile.student_id
        }
    elif user.is_teacher and hasattr(user, 'teacher_profile'):
        user_data['teacher_profile'] = {
            'id': user.teacher_profile.id,
            'employee_id': user.teacher_profile.employee_id
        }

    return Response({
        'user': user_data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@extend_schema(
    tags=['Authentication'],
    summary='Current User',
    description='Get the currently authenticated user information including their profile.',
    responses={200: UserSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get current logged-in user information."""
    user = request.user
    user_data = UserSerializer(user).data

    if user.is_student and hasattr(user, 'student_profile'):
        user_data['student_profile'] = StudentSerializer(user.student_profile).data
    elif user.is_teacher and hasattr(user, 'teacher_profile'):
        user_data['teacher_profile'] = TeacherSerializer(user.teacher_profile).data

    return Response(user_data)


@extend_schema_view(
    list=extend_schema(tags=['Students'], summary='List Students', description='Get a list of all students.'),
    retrieve=extend_schema(tags=['Students'], summary='Get Student', description='Get a specific student by ID.'),
    create=extend_schema(tags=['Students'], summary='Create Student', description='Create a new student. Admin only.'),
    update=extend_schema(tags=['Students'], summary='Update Student', description='Update a student. Admin only.'),
    partial_update=extend_schema(tags=['Students'], summary='Partial Update Student', description='Partially update a student. Admin only.'),
    destroy=extend_schema(tags=['Students'], summary='Delete Student', description='Delete a student. Admin only.'),
)
class StudentViewSet(viewsets.ModelViewSet):

    queryset = Student.objects.select_related('user').all()
    serializer_class = StudentSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['retrieve', 'me']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def me(self, request):
        """Get current student's profile."""
        try:
            student = request.user.student_profile
            serializer = self.get_serializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    list=extend_schema(tags=['Teachers'], summary='List Teachers', description='Get a list of all teachers.'),
    retrieve=extend_schema(tags=['Teachers'], summary='Get Teacher', description='Get a specific teacher by ID.'),
    create=extend_schema(tags=['Teachers'], summary='Create Teacher', description='Create a new teacher. Admin only.'),
    update=extend_schema(tags=['Teachers'], summary='Update Teacher', description='Update a teacher. Admin only.'),
    partial_update=extend_schema(tags=['Teachers'], summary='Partial Update Teacher', description='Partially update a teacher. Admin only.'),
    destroy=extend_schema(tags=['Teachers'], summary='Delete Teacher', description='Delete a teacher. Admin only.'),
)
class TeacherViewSet(viewsets.ModelViewSet):

    queryset = Teacher.objects.select_related('user').all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
