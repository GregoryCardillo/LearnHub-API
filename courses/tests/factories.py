import factory
from factory.django import DjangoModelFactory
from faker import Faker
from courses.models import User, Course, Module, Lesson, Enrollment, Progress

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'student'
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if create:
            self.set_password(extracted or 'testpass123')


class InstructorFactory(UserFactory):
    """Factory for creating Instructor users."""
    role = 'instructor'


class StudentFactory(UserFactory):
    """Factory for creating Student users."""
    role = 'student'


class CourseFactory(DjangoModelFactory):
    """Factory for creating Course instances."""
    
    class Meta:
        model = Course
    
    title = factory.Faker('sentence', nb_words=4)
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(' ', '-'))
    description = factory.Faker('paragraph')
    instructor = factory.SubFactory(InstructorFactory)
    level = 'beginner'
    status = 'published'
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, max_value=999)


class ModuleFactory(DjangoModelFactory):
    """Factory for creating Module instances."""
    
    class Meta:
        model = Module
    
    course = factory.SubFactory(CourseFactory)
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph')
    order = factory.Sequence(lambda n: n)


class LessonFactory(DjangoModelFactory):
    """Factory for creating Lesson instances."""
    
    class Meta:
        model = Lesson
    
    module = factory.SubFactory(ModuleFactory)
    title = factory.Faker('sentence', nb_words=3)
    content_type = 'video'
    content = factory.Faker('paragraph')
    video_url = factory.Faker('url')
    duration_minutes = factory.Faker('random_int', min=5, max=60)
    order = factory.Sequence(lambda n: n)
    is_free = False


class EnrollmentFactory(DjangoModelFactory):
    """Factory for creating Enrollment instances."""
    
    class Meta:
        model = Enrollment
    
    student = factory.SubFactory(StudentFactory)
    course = factory.SubFactory(CourseFactory)
    is_active = True


class ProgressFactory(DjangoModelFactory):
    """Factory for creating Progress instances."""
    
    class Meta:
        model = Progress
    
    enrollment = factory.SubFactory(EnrollmentFactory)
    lesson = factory.SubFactory(LessonFactory)
    completed = False