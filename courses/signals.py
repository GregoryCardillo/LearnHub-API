from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Enrollment, Progress, Lesson

@receiver(post_save, sender=Enrollment)
def create_progress_records(sender, instance, created, **kwargs):
    """
    Automatically create Progress records for all lessons in the course when a student enrolls.
    """
    if created: # Only when a new enrollment is created get all lessons in the course
        course = instance.course
        lessons = Lesson.objects.filter(module__course=course)

        # Create a Progress record for each lesson
        progress_records = [
            Progress(enrollment=instance, lesson=lesson)
            for lesson in lessons
        ]

        #Bulk create for efficiency
        Progress.objects.bulk_create(progress_records)

        print(f"Created {len(progress_records)} progress records for {instance.student.email}")