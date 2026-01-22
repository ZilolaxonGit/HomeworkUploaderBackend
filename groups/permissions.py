from rest_framework import permissions


class IsGroupTeacher(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if request.user.is_teacher and hasattr(request.user, 'teacher_profile'):
            return obj.teacher == request.user.teacher_profile
        return False
