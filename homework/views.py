from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from .models import Homework
from .serializers import HomeworkSerializer, HomeworkListSerializer
from users.permissions import IsAdmin, IsStudent, IsAdminOrTeacher
from lessons.models import Lesson


@extend_schema_view(
    list=extend_schema(tags=['Homework'], summary='List Homework', description='Get a list of homework submissions. Filtered by user role.'),
    retrieve=extend_schema(tags=['Homework'], summary='Get Homework', description='Get a specific homework submission by ID.'),
    create=extend_schema(tags=['Homework'], summary='Submit Homework', description='Submit a new homework. Students only. One submission per lesson.'),
    update=extend_schema(tags=['Homework'], summary='Update Homework', description='Update a homework submission. Cannot update if already rated.'),
    partial_update=extend_schema(tags=['Homework'], summary='Partial Update Homework', description='Partially update a homework submission. Cannot update if already rated.'),
    destroy=extend_schema(tags=['Homework'], summary='Delete Homework', description='Delete a homework submission. Admin only.'),
)
class HomeworkViewSet(viewsets.ModelViewSet):

    queryset = Homework.objects.select_related(
        'student', 'student__user', 'student__group',
        'lesson', 'lesson__teacher', 'lesson__teacher__user', 'lesson__group'
    ).prefetch_related('ratings').all()
    serializer_class = HomeworkSerializer

    def get_permissions(self):
        if self.action in ['create', 'submit_for_lesson']:
            permission_classes = [IsStudent]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsStudent | IsAdminOrTeacher]
        elif self.action in ['destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if user.is_admin:
            return self.queryset

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            # Teachers see homework from their assigned groups
            return self.queryset.filter(lesson__group__teacher=user.teacher_profile)

        if user.is_student and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)

        return Homework.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return HomeworkListSerializer
        return HomeworkSerializer

    def perform_create(self, serializer):
        student = self.request.user.student_profile
        lesson = serializer.validated_data.get('lesson')

        # Validate that student's group matches lesson's group
        if lesson.group and student.group != lesson.group:
            raise ValidationError({
                'lesson': 'You can only submit homework for lessons in your group.'
            })

        if lesson.group and not student.group:
            raise ValidationError({
                'lesson': 'You must be assigned to a group to submit homework for this lesson.'
            })

        existing_homework = Homework.objects.filter(student=student, lesson=lesson).first()
        if existing_homework:
            raise ValidationError({
                'lesson': 'You have already submitted homework for this lesson. Please edit your existing submission instead.'
            })

        serializer.save(student=student, status=Homework.STATUS_SUBMITTED, submitted_at=timezone.now())

    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user

        # Students can only update their own homework that hasn't been rated
        if user.is_student:
            if instance.status == Homework.STATUS_RATED:
                raise PermissionDenied('Cannot edit homework that has already been rated.')
            if instance.student != user.student_profile:
                raise PermissionDenied('You can only edit your own homework.')

        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def my_homeworks(self, request):
        homeworks = self.get_queryset()
        serializer = self.get_serializer(homeworks, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Homework'],
        summary='Get My Lessons with Homework Status',
        description='Get all lessons for the student\'s group with their homework submission status.',
    )
    @action(detail=False, methods=['get'], permission_classes=[IsStudent])
    def my_lessons(self, request):
        student = request.user.student_profile

        if not student.group:
            return Response({
                'error': 'You are not assigned to any group.',
                'lessons': []
            })

        lessons = Lesson.objects.filter(
            group=student.group,
            is_active=True
        ).select_related('teacher', 'teacher__user', 'group').order_by('-created_at')

        student_homeworks = {
            hw.lesson_id: hw for hw in Homework.objects.filter(student=student).prefetch_related('ratings')
        }

        lessons_data = []
        for lesson in lessons:
            homework = student_homeworks.get(lesson.id)
            lesson_data = {
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'teacher_name': lesson.teacher.user.get_full_name() if lesson.teacher else None,
                'start_date': lesson.start_date,
                'end_date': lesson.end_date,
                'deadline': lesson.deadline,
                'is_deadline_passed': lesson.is_deadline_passed,
                'homework_task': lesson.homework_task,
                'homework_image': request.build_absolute_uri(lesson.homework_image.url) if lesson.homework_image else None,
                'allow_file_upload': lesson.allow_file_upload,
                'allow_url_submission': lesson.allow_url_submission,
                'homework_status': None,
                'homework_id': None,
                'can_submit': True,
                'can_edit': False,
                'submission_url': None,
                'submission_file': None,
                'rating_score': None,
                'rating_comment': None,
            }

            if homework:
                lesson_data['homework_status'] = homework.status
                lesson_data['homework_id'] = homework.id
                lesson_data['can_submit'] = False
                lesson_data['can_edit'] = homework.status != Homework.STATUS_RATED
                lesson_data['submission_url'] = homework.submission_url
                lesson_data['submission_file'] = request.build_absolute_uri(homework.submission_file.url) if homework.submission_file else None

                rating = homework.ratings.first()
                if rating:
                    lesson_data['rating_score'] = rating.score
                    lesson_data['rating_comment'] = rating.comment

            lessons_data.append(lesson_data)

        return Response({'lessons': lessons_data})

    @extend_schema(
        tags=['Homework'],
        summary='Submit or Update Homework for Lesson',
        description='Submit new homework or update existing for a specific lesson.',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'submission_url': {'type': 'string', 'format': 'uri'},
                'submission_file': {'type': 'string', 'format': 'binary'},
                'description': {'type': 'string'},
            }
        }},
    )
    @action(detail=False, methods=['post'], url_path='submit/(?P<lesson_id>[^/.]+)', permission_classes=[IsStudent])
    def submit_for_lesson(self, request, lesson_id=None):
        student = request.user.student_profile

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            raise ValidationError({'lesson': 'Lesson not found.'})

        if lesson.group and student.group != lesson.group:
            raise ValidationError({'lesson': 'You can only submit homework for lessons in your group.'})

        if lesson.group and not student.group:
            raise ValidationError({'lesson': 'You must be assigned to a group to submit homework.'})

        existing_homework = Homework.objects.filter(student=student, lesson=lesson).first()

        if existing_homework:
            if existing_homework.status == Homework.STATUS_RATED:
                raise PermissionDenied('Cannot edit homework that has already been rated.')

            if 'submission_url' in request.data:
                existing_homework.submission_url = request.data.get('submission_url')
            if 'submission_file' in request.FILES:
                existing_homework.submission_file = request.FILES.get('submission_file')
            if 'description' in request.data:
                existing_homework.description = request.data.get('description')

            existing_homework.status = Homework.STATUS_SUBMITTED
            existing_homework.submitted_at = timezone.now()
            existing_homework.save()

            serializer = HomeworkSerializer(existing_homework)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            homework = Homework.objects.create(
                student=student,
                lesson=lesson,
                submission_url=request.data.get('submission_url', ''),
                submission_file=request.FILES.get('submission_file'),
                description=request.data.get('description', ''),
                status=Homework.STATUS_SUBMITTED,
                submitted_at=timezone.now()
            )

            serializer = HomeworkSerializer(homework)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Homework'],
        summary='Get Homework for Lesson',
        description='Get homework submission for a specific lesson.',
    )
    @action(detail=False, methods=['get'], url_path='for-lesson/(?P<lesson_id>[^/.]+)', permission_classes=[IsStudent])
    def for_lesson(self, request, lesson_id=None):
        """Get homework for a specific lesson."""
        student = request.user.student_profile

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        lesson_data = {
            'id': lesson.id,
            'title': lesson.title,
            'description': lesson.description,
            'homework_task': lesson.homework_task,
            'homework_image': request.build_absolute_uri(lesson.homework_image.url) if lesson.homework_image else None,
            'allow_file_upload': lesson.allow_file_upload,
            'allow_url_submission': lesson.allow_url_submission,
            'start_date': lesson.start_date,
            'end_date': lesson.end_date,
            'deadline': lesson.deadline,
            'is_deadline_passed': lesson.is_deadline_passed,
        }

        homework = Homework.objects.filter(student=student, lesson=lesson).first()

        if homework:
            serializer = HomeworkSerializer(homework)
            data = serializer.data
            data['lesson_details'] = lesson_data
            return Response(data)
        else:
            return Response({
                'homework': None,
                'lesson': lesson_data
            })
