from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as the unique identifier.
    Supports two roles: STUDENT and INSTRUCTOR.
    """

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    )

    email = models.EmailField(unique=True, verbose_name='Email Address')
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email is already required by default

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Rturns the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name
    
    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == 'student'
    
    @property
    def is_instructor(self):
        """Check if user is an instructor."""
        return self.role == 'instructor'
    
class Course(models.Model):
    """
    Represents a course that can be created by instructors 
    """

    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses_created',
        limit_choices_to={'role': 'instructor'}
    )
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title
    
    @property 
    def total_modules(self):
        """Return the total number of modules in this course."""
        return self.modules.count()
    
    @property
    def total_lessons(self):
        """Return the total number of lessons across all modules."""
        return sum(module.lessons.count() for module in self.modules.all())
    
    @property
    def total_duration(self):
        """Returns the total duration of all lessons in minutes."""
        total = sum(lesson.duration_minutes for module in self.modules.all() for lesson in module.lessons.all() if lesson.duration_minutes)
        return total
    

class Module(models.Model):
    """
    Represents a module/section within a course.
    """

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: 
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def total_lessons(self):
        """Returns the number of lessons in this module."""
        return self.lessons.count()
    

class Lesson(models.Model):
    """
    Represents a single lesson within a module.
    """

    CONTENT_TYPE_CHOICES = (
        ('video', 'Video'),
        ('article', 'Article'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    )

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons'
    )

    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='video')
    content = models.TextField(help_text="Text content or video embed code")
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or Vimeo URL")
    attachments = models.FileField(upload_to='lessons/attachments/', blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0, help_text="Lesson duration in minutes")
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False, help_text="Free preview lesson")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['order']
        unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"