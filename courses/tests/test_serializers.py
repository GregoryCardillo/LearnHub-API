import pytest
from courses.serializers import (
    UserProfileSerializer,
    CourseListSerializer,
    CourseWriteSerializer,
    EnrollmentSerializer,
    RegisterSerializer,
    LoginSerializer,
)
from courses.models import Course
from .factories import (
    StudentFactory,
    InstructorFactory,
    CourseFactory,
    EnrollmentFactory,
)


@pytest.mark.django_db
class TestUserProfileSerializer:
    """Tests for UserProfileSerializer."""
    
    def test_serialize_student(self):
        """Test serializing a student user."""
        student = StudentFactory(first_name='John', last_name='Doe')
        serializer = UserProfileSerializer(student)
        data = serializer.data
        
        assert data['email'] == student.email
        assert data['first_name'] == 'John'
        assert data['last_name'] == 'Doe'
        assert data['full_name'] == 'John Doe'
        assert data['role'] == 'student'
        assert 'total_enrollments' in data
    
    def test_serialize_instructor(self):
        """Test serializing an instructor user."""
        instructor = InstructorFactory()
        serializer = UserProfileSerializer(instructor)
        data = serializer.data
        
        assert data['role'] == 'instructor'
        assert 'total_courses_created' in data


@pytest.mark.django_db
class TestCourseSerializers:
    """Tests for Course serializers."""
    
    def test_course_list_serializer(self, course):
        """Test CourseListSerializer."""
        serializer = CourseListSerializer(course)
        data = serializer.data
        
        assert data['title'] == course.title
        assert data['slug'] == course.slug
        assert 'instructor' in data
        assert data['total_modules'] == 2
        assert data['total_lessons'] == 3
    
    def test_course_write_serializer_valid(self, instructor):
        """Test CourseWriteSerializer with valid data."""
        data = {
            'title': 'New Python Course',
            'slug': 'new-python-course',
            'description': 'Learn Python from scratch',
            'level': 'beginner',
            'status': 'draft',
            'price': '99.99'
        }
        
        # Mock request context
        class MockRequest:
            user = instructor
        
        serializer = CourseWriteSerializer(data=data, context={'request': MockRequest()})
        assert serializer.is_valid()
        
        course = serializer.save()
        assert course.instructor == instructor
        assert course.title == 'New Python Course'
    
    def test_course_write_serializer_invalid_price(self):
        """Test CourseWriteSerializer with negative price."""
        data = {
            'title': 'Test Course',
            'slug': 'test-course',
            'description': 'Description',
            'level': 'beginner',
            'status': 'draft',
            'price': '-10.00'
        }
        
        serializer = CourseWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'price' in serializer.errors
    
    def test_course_write_serializer_short_title(self):
        """Test CourseWriteSerializer with too short title."""
        data = {
            'title': 'ABC',  # Too short
            'slug': 'abc',
            'description': 'Description',
            'level': 'beginner',
            'status': 'draft',
            'price': '50.00'
        }
        
        serializer = CourseWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors


@pytest.mark.django_db
class TestEnrollmentSerializer:
    """Tests for EnrollmentSerializer."""
    
    def test_serialize_enrollment(self, enrollment_with_progress):
        """Test serializing an enrollment."""
        serializer = EnrollmentSerializer(enrollment_with_progress)
        data = serializer.data
        
        assert 'course' in data
        assert 'progress_percentage' in data
        assert 'is_completed' in data
        assert 'next_lesson' in data
        assert 'completed_lessons_count' in data
        assert data['progress_percentage'] == 0.0


@pytest.mark.django_db
class TestAuthSerializers:
    """Tests for authentication serializers."""
    
    def test_register_serializer_valid(self):
        """Test RegisterSerializer with valid data."""
        data = {
            'email': 'newuser@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student'
        }
        
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.email == 'newuser@test.com'
        assert user.check_password('securepass123')
    
    def test_register_serializer_password_mismatch(self):
        """Test RegisterSerializer with password mismatch."""
        data = {
            'email': 'test@test.com',
            'password': 'password123',
            'password_confirm': 'different123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student'
        }
        
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors
    
    def test_register_serializer_duplicate_email(self):
        """Test RegisterSerializer with existing email."""
        StudentFactory(email='existing@test.com')
        
        data = {
            'email': 'existing@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'student'
        }
        
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
    
    def test_login_serializer_valid(self):
        """Test LoginSerializer with valid credentials."""
        user = StudentFactory(email='test@test.com')
        user.set_password('testpass123')
        user.save()
        
        data = {
            'email': 'test@test.com',
            'password': 'testpass123'
        }
        
        serializer = LoginSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['user'] == user
    
    def test_login_serializer_invalid_credentials(self):
        """Test LoginSerializer with invalid credentials."""
        data = {
            'email': 'notexist@test.com',
            'password': 'wrongpass'
        }
        
        serializer = LoginSerializer(data=data)
        assert not serializer.is_valid()