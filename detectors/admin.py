from django.contrib import admin
from .models import TrainedModel, CodeSmellType, AnalysisJob, SmellDetectionResult, Dataset, MetricHistory

@admin.register(TrainedModel)
class TrainedModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'accuracy', 'is_active', 'created_at']
    list_filter = ['model_type', 'is_active', 'created_at']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CodeSmellType)
class CodeSmellTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'created_at']
    list_filter = ['severity']
    search_fields = ['name', 'description']

@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'analysis_type', 'status', 'file_count', 'total_smells_found', 'created_at']
    list_filter = ['analysis_type', 'status', 'created_at']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'completed_at']

@admin.register(SmellDetectionResult)
class SmellDetectionResultAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'smell_type', 'confidence', 'created_at']
    list_filter = ['smell_type', 'created_at']
    search_fields = ['file_name', 'analysis_job__name']

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'row_count', 'is_public', 'uploaded_by', 'created_at']
    list_filter = ['language', 'is_public', 'created_at']
    search_fields = ['name', 'uploaded_by__username']

@admin.register(MetricHistory)
class MetricHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'loc', 'wmc', 'complexity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']