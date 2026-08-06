from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AnalysisJob
from accounts.models import UserActivity

@receiver(post_save, sender=AnalysisJob)
def update_user_stats(sender, instance, created, **kwargs):
    """Update user statistics when analysis completes"""
    if instance.status == 'COMPLETED':
        user = instance.user
        profile = user.profile
        profile.total_analyses += 1
        profile.total_files_analyzed += instance.file_count
        profile.save()