import pytest
from django.utils import timezone
from courses.models import User, Course, Enrollment, Progress
from .factories import (
    StudentFactory,
    InstructorFactory,
    CourseFactory,
    ModuleFactory,
    LessonFactory,
    EnrollmentFactory,
)


@pytest.mark.django_db
class TestUserModel:
    """Tests for User model."""
    
    def test_create_student(self):
        """Test creating a student user."""
        student = StudentFactory()
        assert student.is_student is True
        assert student.is_instructor is False
        assert student.role == 'student'
    
    def test_create_instructor(self):
        """Test creating an instructor user."""
        instructor = InstructorFactory()
        assert instructor.is_instructor is True
        assert instructor.is_student is False
        assert instructor.role == 'instructor'
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = StudentFactory(first_name='John', last_name='Doe')
        assert user.get_full_name() == 'John Doe'
    
    def test_user_string_representation(self):
        """Test __str__ method."""
        user = StudentFactory(email='test@example.com')
        assert str(user) == 'test@example.com'


@pytest.mark.django_db
class TestCourseModel:
    """Tests for Course model."""
    
    def test_create_course(self):
        """Test creating a course."""
        course = CourseFactory(title='Python for Beginners')
        assert course.title == 'Python for Beginners'
        assert course.status == 'published'
    
    def test_total_modules(self, course):
        """Test total_modules property."""
        assert course.total_modules == 2
    
    def test_total_lessons(self, course):
        """Test total_lessons property."""
        assert course.total_lessons == 3
    
    def test_total_duration(self, course):
        """Test total_duration property."""
        # 10 + 15 + 20 = 45 minutes
        assert course.total_duration == 45
    
    def test_course_string_representation(self):
        """Test __str__ method."""
        course = CourseFactory(title='Django Course')
        assert str(course) == 'Django Course'


@pytest.mark.django_db
class TestEnrollmentModel:
    """Tests for Enrollment model."""
    
    def test_create_enrollment(self, student, course):
        """Test creating an enrollment."""
        enrollment = EnrollmentFactory(student=student, course=course)
        assert enrollment.student == student
        assert enrollment.course == course
        assert enrollment.is_active is True
    
    def test_progress_percentage_zero(self, enrollment_with_progress):
        """Test progress percentage when nothing completed."""
        assert enrollment_with_progress.progress_percentage == 0.0
    
    def test_progress_percentage_partial(self, enrollment_with_progress):
        """Test progress percentage with some lessons completed."""
        # Complete 1 out of 3 lessons
        progress = enrollment_with_progress.progress_records.first()
        progress.mark_complete()
        
        enrollment_with_progress.refresh_from_db()
        expected = round((1 / 3) * 100, 2)
        assert enrollment_with_progress.progress_percentage == expected
    
    def test_is_completed(self, enrollment_with_progress):
        """Test is_completed property."""
        # Complete all lessons
        for progress in enrollment_with_progress.progress_records.all():
            progress.mark_complete()
        
        enrollment_with_progress.refresh_from_db()
        assert enrollment_with_progress.is_completed is True
    
    def test_get_next_lesson(self, enrollment_with_progress):
        """Test get_next_lesson method."""
        next_lesson = enrollment_with_progress.get_next_lesson()
        assert next_lesson is not None
        assert next_lesson.order == 1
    
    def test_enrollment_string_representation(self, enrollment_with_progress):
        """Test __str__ method."""
        expected = f"{enrollment_with_progress.student.email} enrolled in {enrollment_with_progress.course.title}"
        assert str(enrollment_with_progress) == expected


@pytest.mark.django_db
class TestProgressModel:
    """Tests for Progress model."""
    
    def test_mark_complete(self, enrollment_with_progress):
        """Test mark_complete method."""
        progress = enrollment_with_progress.progress_records.first()
        
        assert progress.completed is False
        assert progress.completed_at is None
        
        progress.mark_complete()
        
        assert progress.completed is True
        assert progress.completed_at is not None
    
    def test_mark_complete_updates_enrollment(self, enrollment_with_progress):
        """Test that completing all lessons updates enrollment completion."""
        # Complete all lessons
        for progress in enrollment_with_progress.progress_records.all():
            progress.mark_complete()
        
        enrollment_with_progress.refresh_from_db()
        assert enrollment_with_progress.completed_at is not None