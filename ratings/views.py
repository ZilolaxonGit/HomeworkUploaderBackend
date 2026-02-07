from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import date, timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Rating, DailyLeaderboard
from .serializers import RatingSerializer, DailyLeaderboardSerializer
from users.permissions import IsAdmin, IsTeacher, IsAdminOrTeacher
from users.models import Student
from groups.models import Group


@extend_schema_view(
    list=extend_schema(tags=['Ratings'], summary='List Ratings', description='Get a list of ratings. Filtered by user role.'),
    retrieve=extend_schema(tags=['Ratings'], summary='Get Rating', description='Get a specific rating by ID.'),
    create=extend_schema(tags=['Ratings'], summary='Create Rating', description='Create a new rating for homework. Teachers only.'),
    update=extend_schema(tags=['Ratings'], summary='Update Rating', description='Update a rating. Teachers only.'),
    partial_update=extend_schema(tags=['Ratings'], summary='Partial Update Rating', description='Partially update a rating. Teachers only.'),
    destroy=extend_schema(tags=['Ratings'], summary='Delete Rating', description='Delete a rating. Admin only.'),
)
class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ratings."""

    queryset = Rating.objects.select_related(
        'homework', 'homework__lesson', 'homework__lesson__group',
        'teacher', 'teacher__user', 'student', 'student__user', 'student__group'
    ).all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsTeacher]
        elif self.action in ['destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter ratings based on user role."""
        user = self.request.user

        if user.is_admin:
            return self.queryset

        if user.is_teacher and hasattr(user, 'teacher_profile'):
            # Teachers see ratings from their assigned groups
            return self.queryset.filter(homework__lesson__group__teacher=user.teacher_profile)

        if user.is_student and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)

        return Rating.objects.none()

    def perform_create(self, serializer):
        """Set teacher automatically when creating rating and validate group access."""
        if not hasattr(self.request.user, 'teacher_profile'):
            raise ValidationError({'detail': 'Teacher profile not found for this user.'})

        teacher = self.request.user.teacher_profile
        homework = serializer.validated_data.get('homework')

        # Validate teacher is assigned to the homework's group
        if homework.lesson.group and homework.lesson.group.teacher != teacher:
            raise ValidationError({
                'homework': 'You can only rate homework from your assigned groups.'
            })

        serializer.save(teacher=teacher)


@extend_schema_view(
    list=extend_schema(
        tags=['Leaderboard'],
        summary='List Leaderboard',
        description='Get the leaderboard. Optionally filter by date and group.',
        parameters=[
            OpenApiParameter(name='date', type=OpenApiTypes.DATE, description='Filter by date (YYYY-MM-DD). Defaults to today.'),
            OpenApiParameter(name='group', type=OpenApiTypes.INT, description='Filter by group ID.'),
        ],
    ),
    retrieve=extend_schema(tags=['Leaderboard'], summary='Get Leaderboard Entry', description='Get a specific leaderboard entry by ID.'),
)
class DailyLeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing daily leaderboards."""

    queryset = DailyLeaderboard.objects.select_related('student', 'student__user', 'group').all()
    serializer_class = DailyLeaderboardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter leaderboard by date and group based on user role."""
        user = self.request.user
        queryset = self.queryset

        # Filter by date
        date_param = self.request.query_params.get('date', None)
        if date_param:
            queryset = queryset.filter(date=date_param)
        else:
            today = date.today()
            queryset = queryset.filter(date=today)

        # Filter by group from query params
        group_param = self.request.query_params.get('group', None)
        if group_param:
            queryset = queryset.filter(group_id=group_param)

        # Apply role-based filtering
        if user.is_admin:
            pass  # Admin sees all
        elif user.is_teacher and hasattr(user, 'teacher_profile'):
            # Teachers see leaderboards from their assigned groups
            queryset = queryset.filter(group__teacher=user.teacher_profile)
        elif user.is_student and hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                queryset = queryset.filter(group=student.group)
            else:
                queryset = DailyLeaderboard.objects.none()
        else:
            queryset = DailyLeaderboard.objects.none()

        return queryset.order_by('rank')

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's leaderboard."""
        leaderboard = self.get_queryset()
        serializer = self.get_serializer(leaderboard, many=True)
        return Response(serializer.data)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @action(detail=False, methods=['get'])
    def top_three(self, request):
        """Get top 3 students from today's leaderboard."""
        top_three = self.get_queryset().filter(rank__lte=3).order_by('rank')
        serializer = self.get_serializer(top_three, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Leaderboard'],
        summary='Get Monthly Leaderboard',
        description='Get leaderboard for a specific month based on lessons created in that month.',
        parameters=[
            OpenApiParameter(name='year', type=OpenApiTypes.INT, description='Year (e.g., 2026)'),
            OpenApiParameter(name='month', type=OpenApiTypes.INT, description='Month (1-12)'),
        ],
    )
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly leaderboard based on lessons created in that month.

        Average score calculation:
        - Includes all lessons where deadline has passed or homework has been rated
        - Students who missed homework (deadline passed, no submission) get 0 for that lesson
        - Average = total score / number of lessons with passed deadlines
        """
        user = self.request.user
        group_param = self.request.query_params.get('group', None)

        # Get year and month from query params, default to current month
        today = date.today()
        try:
            year = int(request.query_params.get('year', today.year))
            month = int(request.query_params.get('month', today.month))
        except (ValueError, TypeError):
            year = today.year
            month = today.month

        # Calculate the date range for the month
        from calendar import monthrange
        from lessons.models import Lesson
        from homework.models import Homework

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # Get lessons created in this month
        lessons_query = Lesson.objects.filter(
            created_at__date__gte=first_day,
            created_at__date__lte=last_day,
            is_active=True
        )

        # Apply group filter based on user role
        target_group = None
        if group_param:
            lessons_query = lessons_query.filter(group_id=group_param)
            target_group = Group.objects.filter(id=group_param).first()
        elif user.is_teacher and hasattr(user, 'teacher_profile'):
            lessons_query = lessons_query.filter(group__teacher=user.teacher_profile)
        elif user.is_student and hasattr(user, 'student_profile'):
            if user.student_profile.group:
                lessons_query = lessons_query.filter(group=user.student_profile.group)
                target_group = user.student_profile.group
            else:
                return Response({'leaderboard': [], 'month': month, 'year': year, 'total_lessons': 0})

        total_lessons = lessons_query.count()

        # Get lessons where deadline has passed or has any rated homework
        now = timezone.now()
        countable_lesson_ids = []
        for lesson in lessons_query:
            # Lesson is countable if deadline passed or any homework is rated
            if lesson.deadline and lesson.deadline < now:
                countable_lesson_ids.append(lesson.id)
            elif Homework.objects.filter(lesson=lesson, status='RATED').exists():
                countable_lesson_ids.append(lesson.id)

        total_countable_lessons = len(countable_lesson_ids)

        if total_countable_lessons == 0:
            return Response({'leaderboard': [], 'month': month, 'year': year, 'total_lessons': total_lessons})

        # Get all students in the relevant group(s)
        students_query = Student.objects.filter(user__is_active=True)
        if target_group:
            students_query = students_query.filter(group=target_group)
        elif group_param:
            students_query = students_query.filter(group_id=group_param)
        elif user.is_teacher and hasattr(user, 'teacher_profile'):
            students_query = students_query.filter(group__teacher=user.teacher_profile)
        elif user.is_student and hasattr(user, 'student_profile') and user.student_profile.group:
            students_query = students_query.filter(group=user.student_profile.group)

        students = students_query.select_related('user', 'group')

        # Calculate scores for each student using optimized query
        # Get all ratings for countable lessons in ONE query with aggregation
        ratings_for_month = Rating.objects.filter(
            homework__lesson_id__in=countable_lesson_ids
        ).values('student_id').annotate(
            total_score=Sum('score'),
            rated_count=Count('id')
        )

        # Create a dictionary for O(1) lookup
        ratings_dict = {r['student_id']: r for r in ratings_for_month}

        # Build student scores efficiently
        student_scores = []
        for student in students:
            rating_data = ratings_dict.get(student.id, {'total_score': 0, 'rated_count': 0})

            total_score = rating_data['total_score'] or 0
            rated_count = rating_data['rated_count'] or 0

            # Calculate average: total score / number of countable lessons
            avg_score = total_score / total_countable_lessons if total_countable_lessons > 0 else 0

            student_scores.append({
                'student': student,
                'avg_score': round(avg_score, 1),
                'total_score': total_score,
                'rated_count': rated_count,
                'total_lessons': total_countable_lessons
            })

        # Sort by average score (descending), then by total_score as tiebreaker
        student_scores.sort(key=lambda x: (x['avg_score'], x['total_score']), reverse=True)

        # Build leaderboard data with ranks
        leaderboard_data = []
        for rank, entry in enumerate(student_scores, start=1):
            student = entry['student']
            leaderboard_data.append({
                'id': f"monthly_{year}_{month}_{student.id}",
                'rank': rank,
                'student_id': student.student_id,
                'student_name': student.user.get_full_name() or student.user.username,
                'student_details': {
                    'username': student.user.username,
                    'first_name': student.user.first_name,
                    'last_name': student.user.last_name,
                },
                'group_details': {
                    'id': student.group.id,
                    'name': student.group.name,
                } if student.group else None,
                'average_score': entry['avg_score'],
                'total_ratings': entry['rated_count'],
                'is_top_three': rank <= 3,
            })

        return Response({
            'leaderboard': leaderboard_data,
            'month': month,
            'year': year,
            'total_lessons': total_lessons
        })


@extend_schema(
    tags=['Leaderboard'],
    summary='Calculate Daily Leaderboard',
    description='Calculate and save the daily leaderboard based on ratings per group. Admin only.',
    request={'application/json': {'type': 'object', 'properties': {
        'date': {'type': 'string', 'format': 'date', 'description': 'Date to calculate leaderboard for (YYYY-MM-DD). Defaults to today.'},
        'group': {'type': 'integer', 'description': 'Optional group ID to calculate leaderboard for a specific group.'},
    }}},
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
)
@api_view(['POST'])
@permission_classes([IsAdmin])
def calculate_daily_leaderboard(request):
    """Calculate and save daily leaderboard per group (Admin only)."""
    target_date = request.data.get('date')
    group_id = request.data.get('group')

    if target_date:
        try:
            target_date = date.fromisoformat(target_date)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        target_date = date.today()

    # Get groups to calculate for
    if group_id:
        groups = Group.objects.filter(id=group_id)
        if not groups.exists():
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Get all active groups
        groups = Group.objects.filter(is_active=True)

    # Delete existing leaderboard entries for the target date and groups
    if group_id:
        DailyLeaderboard.objects.filter(date=target_date, group_id=group_id).delete()
    else:
        DailyLeaderboard.objects.filter(date=target_date).delete()

    all_leaderboard_entries = []
    groups_processed = 0
    total_entries = 0

    for group in groups:
        # Get ratings for students in this group on the target date
        ratings = Rating.objects.filter(
            rating_date=target_date,
            student__group=group
        )

        if not ratings.exists():
            continue

        groups_processed += 1

        student_scores = ratings.values('student').annotate(
            avg_score=Avg('score'),
            total_ratings=Count('id')
        ).order_by('-avg_score')

        # Prefetch all students in one query to avoid N+1
        student_ids = [entry['student'] for entry in student_scores]
        students_map = {
            s.id: s for s in Student.objects.filter(
                id__in=student_ids
            ).select_related('user', 'group')
        }

        for rank, entry in enumerate(student_scores, start=1):
            student = students_map[entry['student']]
            leaderboard_entry = DailyLeaderboard(
                student=student,
                group=group,
                date=target_date,
                average_score=round(entry['avg_score'], 1),
                rank=rank,
                total_ratings=entry['total_ratings']
            )
            all_leaderboard_entries.append(leaderboard_entry)
            total_entries += 1

    if total_entries == 0:
        return Response(
            {'message': f'No ratings found for {target_date}'},
            status=status.HTTP_404_NOT_FOUND
        )

    DailyLeaderboard.objects.bulk_create(all_leaderboard_entries)

    serializer = DailyLeaderboardSerializer(all_leaderboard_entries, many=True)

    return Response({
        'message': f'Daily leaderboard calculated for {target_date}',
        'groups_processed': groups_processed,
        'count': total_entries,
        'leaderboard': serializer.data
    }, status=status.HTTP_201_CREATED)
