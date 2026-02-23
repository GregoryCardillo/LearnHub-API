import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .factories import (
    UserFactory,
    StudentFactory,
    InstructorFactory,
    CourseFactory,
    ModuleFactory,
    LessonFactory,
    EnrollmentFactory,
)


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def student():
    """Fixture for a student user."""
    return StudentFactory()


@pytest.fixture
def instructor():
    """Fixture for an instructor user."""
    return InstructorFactory()


@pytest.fixture
def authenticated_client(api_client, student):
    """Fixture for authenticated API client with student."""
    refresh = RefreshToken.for_user(student)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def instructor_client(api_client, instructor):
    """Fixture for authenticated API client with instructor."""
    refresh = RefreshToken.for_user(instructor)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def course():
    """Fixture for a course with modules and lessons."""
    course = CourseFactory()
    module1 = ModuleFactory(course=course, order=1)
    module2 = ModuleFactory(course=course, order=2)
    
    LessonFactory(module=module1, order=1, duration_minutes=10)
    LessonFactory(module=module1, order=2, duration_minutes=15)
    LessonFactory(module=module2, order=1, duration_minutes=20)
    
    return course


@pytest.fixture
def enrollment_with_progress(student, course):
    """Fixture for enrollment with progress records."""
    enrollment = EnrollmentFactory(student=student, course=course)
    return enrollment