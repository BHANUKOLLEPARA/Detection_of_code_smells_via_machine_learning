"""
Detector App Models
"""

from django.db import models
from django.contrib.auth.models import User
import os


class TrainedModel(models.Model):
    """Trained ML Model"""
    MODEL_TYPES = [
        ('RANDOM_FOREST', 'Random Forest'),
        ('GRADIENT_BOOSTING', 'Gradient Boosting'),
        ('ADA_BOOST', 'AdaBoost'),
        ('DECISION_TREE', 'Decision Tree'),
        ('SVM', 'Support Vector Machine'),
        ('NEURAL_NETWORK', 'Neural Network'),
        ('LOGISTIC_REGRESSION', 'Logistic Regression'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES, default='RANDOM_FOREST')
    model_file = models.FileField(upload_to='models/')
    scaler_file = models.FileField(upload_to='models/', null=True, blank=True)
    encoder_file = models.FileField(upload_to='models/', null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    mcc = models.FloatField(null=True, blank=True)  # Matthews Correlation Coefficient
    dataset_used = models.CharField(max_length=255, blank=True)
    features_used = models.TextField(blank=True, help_text='Comma-separated list of features')
    training_time = models.FloatField(null=True, blank=True, help_text='Training time in seconds')
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_model_type_display()} ({self.accuracy:.2f}%)"
    
    class Meta:
        db_table = 'trained_models'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other models
            TrainedModel.objects.filter(is_active=True).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)


class CodeSmellType(models.Model):
    """Code Smell Types"""
    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='MEDIUM')
    refactoring_tip = models.TextField(blank=True)
    example_code = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'code_smell_types'


class AnalysisJob(models.Model):
    """Code Analysis Job"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    ANALYSIS_TYPES = [
        ('SINGLE_FILE', 'Single File'),
        ('FOLDER', 'Folder'),
        ('CODE_SNIPPET', 'Code Snippet'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_jobs')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    language = models.CharField(max_length=50, blank=True)
    file_count = models.IntegerField(default=0)
    total_smells_found = models.IntegerField(default=0)
    model_used = models.ForeignKey(TrainedModel, on_delete=models.SET_NULL, null=True)
    
    # Files
    uploaded_file = models.FileField(upload_to='uploads/files/', null=True, blank=True)
    uploaded_folder = models.CharField(max_length=500, blank=True)
    code_snippet = models.TextField(blank=True)
    
    # Results
    results_json = models.JSONField(default=dict, blank=True)
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Metrics
    processing_time = models.FloatField(null=True, blank=True, help_text='Processing time in seconds')
    memory_used = models.FloatField(null=True, blank=True, help_text='Memory used in MB')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name} - {self.status}"
    
    class Meta:
        db_table = 'analysis_jobs'
        ordering = ['-created_at']


class SmellDetectionResult(models.Model):
    """Individual Smell Detection Result"""
    analysis_job = models.ForeignKey(AnalysisJob, on_delete=models.CASCADE, related_name='results')
    smell_type = models.ForeignKey(CodeSmellType, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    line_start = models.IntegerField(null=True, blank=True)
    line_end = models.IntegerField(null=True, blank=True)
    code_snippet = models.TextField(blank=True)
    confidence = models.FloatField(default=0.0)
    
    # Metrics that led to this detection
    loc = models.IntegerField(default=0)
    wmc = models.IntegerField(default=0)
    cbo = models.IntegerField(default=0)
    tcc = models.FloatField(default=0.0)
    lcom = models.IntegerField(default=0)
    rfc = models.IntegerField(default=0)
    complexity = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.smell_type.name}"
    
    class Meta:
        db_table = 'smell_detection_results'


class Dataset(models.Model):
    """Training Dataset"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='datasets/')
    language = models.CharField(max_length=50, blank=True)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'datasets'
        ordering = ['-created_at']


class MetricHistory(models.Model):
    """Historical Metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    analysis_job = models.ForeignKey(AnalysisJob, on_delete=models.CASCADE, null=True)
    
    # Metrics
    loc = models.IntegerField(default=0)
    wmc = models.IntegerField(default=0)
    cbo = models.IntegerField(default=0)
    tcc = models.FloatField(default=0.0)
    lcom = models.IntegerField(default=0)
    rfc = models.IntegerField(default=0)
    complexity = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'metric_history'
        ordering = ['-created_at']


class ModelEvaluation(models.Model):
    """Model Evaluation Results"""
    model = models.ForeignKey(TrainedModel, on_delete=models.CASCADE, related_name='evaluations')
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    mcc = models.FloatField()
    
    # Cross-validation results
    cv_scores = models.JSONField(default=list)
    cv_mean = models.FloatField()
    cv_std = models.FloatField()
    
    # Confusion matrix
    confusion_matrix = models.JSONField(default=list)
    
    # Classification report
    classification_report = models.JSONField(default=dict)
    
    # Feature importance
    feature_importance = models.JSONField(default=dict)
    
    # ROC curves
    roc_auc = models.FloatField(null=True, blank=True)
    roc_curve_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'model_evaluations'
        ordering = ['-created_at']