import pytest
from rest_framework.test import APIRequestFactory
from courses.permissions import (
    IsInstructor,
    IsStudent,
    IsOwnerOrReadOnly,
    IsCourseInstructor,
)
from .factories import StudentFactory, InstructorFactory, CourseFactory


@pytest.mark.django_db
class TestIsInstructor:
    """Tests for IsInstructor permission."""
    
    def setup_method(self):
        self.permission = IsInstructor()
        self.factory = APIRequestFactory()
    
    def test_instructor_has_permission(self, instructor):
        """Test that instructor users have permission."""
        request = self.factory.get('/')
        request.user = instructor
        
        assert self.permission.has_permission(request, None) is True
    
    def test_student_no_permission(self, student):
        """Test that student users don't have permission."""
        request = self.factory.get('/')
        request.user = student
        
        assert self.permission.has_permission(request, None) is False
    
    def test_unauthenticated_no_permission(self):
        """Test that unauthenticated users don't have permission."""
        from django.contrib.auth.models import AnonymousUser
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsStudent:
    """Tests for IsStudent permission."""
    
    def setup_method(self):
        self.permission = IsStudent()
        self.factory = APIRequestFactory()
    
    def test_student_has_permission(self, student):
        """Test that student users have permission."""
        request = self.factory.get('/')
        request.user = student
        
        assert self.permission.has_permission(request, None) is True
    
    def test_instructor_no_permission(self, instructor):
        """Test that instructor users don't have permission."""
        request = self.factory.get('/')
        request.user = instructor
        
        assert self.permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsOwnerOrReadOnly:
    """Tests for IsOwnerOrReadOnly permission."""
    
    def setup_method(self):
        self.permission = IsOwnerOrReadOnly()
        self.factory = APIRequestFactory()
    
    def test_read_permission_for_all(self, student):
        """Test that read permissions are allowed for everyone."""
        request = self.factory.get('/')
        request.user = student
        course = CourseFactory()
        
        assert self.permission.has_object_permission(request, None, course) is True
    
    def test_write_permission_for_owner(self, instructor):
        """Test that write permissions are only for owner."""
        course = CourseFactory(instructor=instructor)
        
        request = self.factory.put('/')
        request.user = instructor
        
        assert self.permission.has_object_permission(request, None, course) is True
    
    def test_write_permission_denied_for_non_owner(self, instructor):
        """Test that write permissions are denied for non-owners."""
        other_instructor = InstructorFactory()
        course = CourseFactory(instructor=other_instructor)
        
        request = self.factory.put('/')
        request.user = instructor
        
        assert self.permission.has_object_permission(request, None, course) is False


@pytest.mark.django_db
class TestIsCourseInstructor:
    """Tests for IsCourseInstructor permission."""
    
    def setup_method(self):
        self.permission = IsCourseInstructor()
        self.factory = APIRequestFactory()
    
    def test_course_instructor_has_permission(self, instructor):
        """Test that course instructor has permission."""
        course = CourseFactory(instructor=instructor)
        
        request = self.factory.get('/')
        request.user = instructor
        
        assert self.permission.has_object_permission(request, None, course) is True
    
    def test_other_instructor_no_permission(self, instructor):
        """Test that other instructors don't have permission."""
        other_instructor = InstructorFactory()
        course = CourseFactory(instructor=other_instructor)
        
        request = self.factory.get('/')
        request.user = instructor
        
        assert self.permission.has_object_permission(request, None, course) is False