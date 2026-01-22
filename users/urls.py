from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, TeacherViewSet, login_view, current_user_view

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teachers', TeacherViewSet, basename='teacher')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('me/', current_user_view, name='current-user'),
    path('', include(router.urls)),
]
