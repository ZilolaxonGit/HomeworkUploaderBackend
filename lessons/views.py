from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.utils import timezone
from .models import Lesson
from .serializers import LessonSerializer, LessonListSerializer
from users.permissions import IsAdmin, IsAdminOrTeacher
from users.models import Student
from groups.models import Group
from homework.models import Homework
from ratings.models import Rating


@extend_schema_view(
    list=extend_schema(tags=['Lessons'], summary='List Lessons', description='Get a list of all lessons.'),
    retrieve=extend_schema(tags=['Lessons'], summary='Get Lesson', description='Get a specific lesson by ID.'),
    create=extend_schema(tags=['Lessons'], summary='Create Lesson', description='Create a new lesson. Admin or Teacher for their groups.'),
    update=extend_schema(tags=['Lessons'], summary='Update Lesson', description='Update a lesson. Admin or Teacher for their groups.'),
    partial_update=extend_schema(tags=['Lessons'], summary='Partial Update Lesson', description='Partially update a lesson. Admin or Teacher for their groups.'),
    destroy=extend_schema(tags=['Lessons'], summary='Delete Lesson', description='Delete a lesson. Admin only.'),
)
class LessonViewSet(viewsets.ModelViewSet):

    queryset = Lesson.objects.select_related('teacher', 'teacher__user', 'group').all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ['destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAdminOrTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'list':
            return LessonListSerializer
        return LessonSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        if user.is_admin:
            return queryset

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            return queryset.filter(group__teacher=user.teacher_profile)

        if user.is_student and hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return queryset.filter(group=student.group)
            return Lesson.objects.none()

        return Lesson.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        group = serializer.validated_data.get('group')

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            if group and group.teacher != user.teacher_profile:
                raise PermissionDenied('You can only create lessons for your assigned groups.')
            serializer.save(teacher=user.teacher_profile)
        else:
            # Admin can set any teacher
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        group = serializer.validated_data.get('group', instance.group)

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            if instance.group and instance.group.teacher != user.teacher_profile:
                raise PermissionDenied('You can only edit lessons for your assigned groups.')
            if group and group.teacher != user.teacher_profile:
                raise PermissionDenied('You can only move lessons to your assigned groups.')

        serializer.save()

    @extend_schema(
        tags=['Lessons'],
        summary='Get Lesson Submission Stats',
        description='Get submission statistics for a lesson including who submitted and who did not, ordered by rating.',
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def submission_stats(self, request, pk=None):
        lesson = self.get_object()
        user = request.user

        # Check access
        if user.is_student and hasattr(user, 'student_profile'):
            if user.student_profile.group != lesson.group:
                raise PermissionDenied('You can only view stats for lessons in your group.')

        if not lesson.group:
            return Response({'error': 'This lesson has no group assigned.'}, status=400)

        all_students = Student.objects.filter(group=lesson.group).select_related('user')

        homework_submissions = Homework.objects.filter(lesson=lesson).select_related(
            'student', 'student__user'
        ).prefetch_related('ratings')

        submissions_dict = {hw.student_id: hw for hw in homework_submissions}

        submitted_students = []
        not_submitted_students = []

        for student in all_students:
            homework = submissions_dict.get(student.id)
            student_data = {
                'id': student.id,
                'student_id': student.student_id,
                'username': student.user.username,
                'full_name': student.user.get_full_name() or student.user.username,
                'first_name': student.user.first_name,
                'last_name': student.user.last_name,
            }

            if homework:
                rating = homework.ratings.first()
                student_data['homework_id'] = homework.id
                student_data['submission_url'] = homework.submission_url
                student_data['submission_file'] = request.build_absolute_uri(homework.submission_file.url) if homework.submission_file else None
                student_data['submitted_at'] = homework.submitted_at
                student_data['status'] = homework.status
                student_data['rating'] = {
                    'id': rating.id,
                    'score': rating.score,
                    'comment': rating.comment,
                } if rating else None
                student_data['score'] = rating.score if rating else None
                submitted_students.append(student_data)
            else:
                # If deadline has passed, treat as 0 score and include in submitted list for ranking
                if lesson.is_deadline_passed:
                    student_data['score'] = 0
                    student_data['homework_id'] = None
                    student_data['submission_url'] = None
                    student_data['submission_file'] = None
                    student_data['submitted_at'] = None
                    student_data['status'] = 'MISSED'
                    student_data['rating'] = {
                        'id': None,
                        'score': 0,
                        'comment': 'Missed deadline - automatic 0 score',
                    }
                    submitted_students.append(student_data)  # Add to submitted list for ranking
                else:
                    student_data['score'] = None
                    not_submitted_students.append(student_data)

        # Sort submitted students by score (highest first), None scores at the end
        submitted_students.sort(key=lambda x: (x['score'] is None, -(x['score'] or 0)))

        # Separate actual submissions from missed deadlines for display purposes
        actual_submissions = [s for s in submitted_students if s.get('status') != 'MISSED']
        missed_submissions = [s for s in submitted_students if s.get('status') == 'MISSED']

        return Response({
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'deadline': lesson.deadline,
                'is_deadline_passed': lesson.is_deadline_passed,
            },
            'total_students': all_students.count(),
            'submitted_count': len(actual_submissions),
            'missed_count': len(missed_submissions),
            'not_submitted_count': len(not_submitted_students),
            'submitted_students': submitted_students,  # Includes both actual and missed for ranking
            'not_submitted_students': not_submitted_students,
        })

    @extend_schema(
        tags=['Lessons'],
        summary='Auto-rate Missing Submissions',
        description='Automatically rate students who did not submit homework with 0 after deadline. Teacher/Admin only.',
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrTeacher])
    def auto_rate_missing(self, request, pk=None):
        """Auto-rate students who didn't submit homework after deadline with 0."""
        lesson = self.get_object()
        user = request.user

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            if lesson.group and lesson.group.teacher != user.teacher_profile:
                raise PermissionDenied('You can only rate lessons for your assigned groups.')

        if not lesson.is_deadline_passed:
            return Response({'error': 'Deadline has not passed yet.'}, status=400)

        if not lesson.group:
            return Response({'error': 'This lesson has no group assigned.'}, status=400)

        all_students = Student.objects.filter(group=lesson.group)

        submitted_student_ids = Homework.objects.filter(lesson=lesson).values_list('student_id', flat=True)

        missing_students = all_students.exclude(id__in=submitted_student_ids)

        teacher = lesson.teacher
        if not teacher and user.is_teacher:
            teacher = user.teacher_profile

        if not teacher:
            return Response({'error': 'No teacher found to create ratings.'}, status=400)

        created_count = 0
        for student in missing_students:
            homework, hw_created = Homework.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={
                    'status': Homework.STATUS_RATED,
                    'description': 'Auto-created: Missed deadline',
                }
            )

            if not Rating.objects.filter(homework=homework).exists():
                Rating.objects.create(
                    homework=homework,
                    teacher=teacher,
                    student=student,
                    score=0,
                    comment='Homework not submitted before deadline.'
                )
                if hw_created:
                    created_count += 1

        return Response({
            'message': f'Auto-rated {created_count} students with 0 for missed deadline.',
            'rated_count': created_count,
        })
