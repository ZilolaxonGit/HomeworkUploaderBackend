from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RatingViewSet, DailyLeaderboardViewSet, calculate_daily_leaderboard

router = DefaultRouter()
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'leaderboard', DailyLeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    path('leaderboard/calculate/', calculate_daily_leaderboard, name='calculate-leaderboard'),
    path('', include(router.urls)),
]
