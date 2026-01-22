from rest_framework import permissions


class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsTeacher(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_teacher


class IsStudent(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student


class IsAdminOrTeacher(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_admin or request.user.is_teacher))


class IsOwnerOrAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'student'):
            return obj.student.user == request.user
        elif hasattr(obj, 'teacher'):
            return obj.teacher.user == request.user

        return False
