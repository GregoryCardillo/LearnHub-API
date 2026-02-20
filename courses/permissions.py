from rest_framework import permissions


class IsInstructor(permissions.BasePermission):
    """
    Permission to only allow instructors to perform the action.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is an instructor."""
        return request.user and request.user.is_authenticated and request.user.is_instructor
    
    message = "Only instructors can perform this action."


class IsStudent(permissions.BasePermission):
    """
    Permission to only allow students to perform the action.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a student."""
        return request.user and request.user.is_authenticated and request.user.is_student
    
    message = "Only students can perform this action."


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit/delete it.
    Read permissions are allowed to any request.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Read permissions (GET, HEAD, OPTIONS) are allowed for any request.
        Write permissions (PUT, PATCH, DELETE) only for the owner.
        """
        # Read permissions allowed for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        # Check if object has 'instructor' attribute (for courses)
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        
        # Check if object has 'student' attribute (for enrollments)
        if hasattr(obj, 'student'):
            return obj.student == request.user
        
        # Check if object is the user themselves
        if hasattr(obj, 'id') and obj == request.user:
            return True
        
        return False
    
    message = "You do not have permission to modify this object."


class IsCourseInstructor(permissions.BasePermission):
    """
    Permission to only allow the course instructor to perform actions.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if the user is the instructor of the course."""
        # For Course objects
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        
        # For Module objects (check parent course)
        if hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        
        # For Lesson objects (check parent module's course)
        if hasattr(obj, 'module'):
            return obj.module.course.instructor == request.user
        
        return False
    
    message = "Only the course instructor can perform this action."


class IsEnrolled(permissions.BasePermission):
    """
    Permission to check if user is enrolled in a course.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is enrolled in the course."""
        from .models import Enrollment
        
        # For Course objects
        if hasattr(obj, 'enrollments'):
            return Enrollment.objects.filter(
                student=request.user,
                course=obj,
                is_active=True
            ).exists()
        
        # For Module objects
        if hasattr(obj, 'course'):
            return Enrollment.objects.filter(
                student=request.user,
                course=obj.course,
                is_active=True
            ).exists()
        
        # For Lesson objects
        if hasattr(obj, 'module'):
            return Enrollment.objects.filter(
                student=request.user,
                course=obj.module.course,
                is_active=True
            ).exists()
        
        return False
    
    message = "You must be enrolled in this course to access this content."


class IsEnrolledOrFree(permissions.BasePermission):
    """
    Permission to allow access to free lessons OR enrolled students.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Allow access if:
        - Lesson is marked as free (is_free=True)
        - User is enrolled in the course
        """
        from .models import Enrollment
        
        # If it's a lesson, check if it's free
        if hasattr(obj, 'is_free') and obj.is_free:
            return True
        
        # Check if user is enrolled
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For Lesson objects
        if hasattr(obj, 'module'):
            return Enrollment.objects.filter(
                student=request.user,
                course=obj.module.course,
                is_active=True
            ).exists()
        
        return False
    
    message = "You must be enrolled to access this lesson, or the lesson must be free."


class IsEnrollmentOwner(permissions.BasePermission):
    """
    Permission to only allow the student who owns the enrollment.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if the user is the student of this enrollment."""
        return obj.student == request.user
    
    message = "You can only access your own enrollments."


class CanCreateCourse(permissions.BasePermission):
    """
    Permission to check if user can create courses (only instructors).
    """
    
    def has_permission(self, request, view):
        """Only instructors can create courses."""
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and request.user.is_instructor
        return True
    
    message = "Only instructors can create courses."