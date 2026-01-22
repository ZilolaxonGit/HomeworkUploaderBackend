from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Group
from .serializers import GroupSerializer, GroupListSerializer
from users.permissions import IsAdmin, IsAdminOrTeacher
from users.models import Student, Teacher


@extend_schema_view(
    list=extend_schema(tags=['Groups'], summary='List Groups', description='Get a list of all groups.'),
    retrieve=extend_schema(tags=['Groups'], summary='Get Group', description='Get a specific group by ID.'),
    create=extend_schema(tags=['Groups'], summary='Create Group', description='Create a new group. Admin only.'),
    update=extend_schema(tags=['Groups'], summary='Update Group', description='Update a group. Admin only.'),
    partial_update=extend_schema(tags=['Groups'], summary='Partial Update Group', description='Partially update a group. Admin only.'),
    destroy=extend_schema(tags=['Groups'], summary='Delete Group', description='Delete a group. Admin only.'),
)
class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.select_related('teacher', 'teacher__user').annotate(
        student_total=Count('students')
    ).all()
    serializer_class = GroupSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy',
                           'assign_student', 'remove_student', 'assign_teacher']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use lightweight serializer for list action."""
        if self.action == 'list':
            return GroupListSerializer
        return GroupSerializer

    def get_queryset(self):
        """Filter groups based on user role."""
        user = self.request.user
        queryset = self.queryset

        if user.is_admin:
            return queryset

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            return queryset.filter(teacher=user.teacher_profile)

        if user.is_student and hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return queryset.filter(id=student.group.id)
            return Group.objects.none()

        return Group.objects.none()

    @extend_schema(
        tags=['Groups'],
        summary='Assign Student to Group',
        description='Assign a student to this group. Admin only.',
        request={'application/json': {'type': 'object', 'properties': {'student_id': {'type': 'integer'}}}},
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_student(self, request, pk=None):
        """Assign a student to this group."""
        group = self.get_object()
        student_id = request.data.get('student_id')

        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        student.group = group
        student.save()

        return Response({
            'message': f'Student {student.student_id} assigned to group {group.name}',
            'student_id': student.id,
            'group_id': group.id
        })

    @extend_schema(
        tags=['Groups'],
        summary='Remove Student from Group',
        description='Remove a student from this group. Admin only.',
        request={'application/json': {'type': 'object', 'properties': {'student_id': {'type': 'integer'}}}},
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def remove_student(self, request, pk=None):
        """Remove a student from this group."""
        group = self.get_object()
        student_id = request.data.get('student_id')

        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student = Student.objects.get(id=student_id, group=group)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found in this group'},
                status=status.HTTP_404_NOT_FOUND
            )

        student.group = None
        student.save()

        return Response({
            'message': f'Student {student.student_id} removed from group {group.name}',
            'student_id': student.id
        })

    @extend_schema(
        tags=['Groups'],
        summary='Assign Teacher to Group',
        description='Assign a teacher to this group. Admin only.',
        request={'application/json': {'type': 'object', 'properties': {'teacher_id': {'type': 'integer'}}}},
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def assign_teacher(self, request, pk=None):
        """Assign a teacher to this group."""
        group = self.get_object()
        teacher_id = request.data.get('teacher_id')

        if teacher_id is None:
            group.teacher = None
            group.save()
            return Response({
                'message': f'Teacher removed from group {group.name}',
                'group_id': group.id
            })

        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'Teacher not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        group.teacher = teacher
        group.save()

        return Response({
            'message': f'Teacher {teacher.employee_id} assigned to group {group.name}',
            'teacher_id': teacher.id,
            'group_id': group.id
        })

    @extend_schema(
        tags=['Groups'],
        summary='Get Students in Group',
        description='Get all students in this group.',
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in this group."""
        group = self.get_object()
        students = group.students.select_related('user').all()

        student_data = []
        for student in students:
            student_data.append({
                'id': student.id,
                'student_id': student.student_id,
                'username': student.user.username,
                'first_name': student.user.first_name,
                'last_name': student.user.last_name,
                'full_name': student.user.get_full_name(),
            })

        return Response({
            'group_id': group.id,
            'group_name': group.name,
            'students': student_data,
            'count': len(student_data)
        })
