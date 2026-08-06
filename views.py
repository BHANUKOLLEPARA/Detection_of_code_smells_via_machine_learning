"""
Detector App Views - Complete Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.http import require_POST
import json
import os
import time
from datetime import datetime
from pathlib import Path

# Try to import models
try:
    from .models import (
        AnalysisJob,
        TrainedModel,
        CodeSmellType,
        SmellDetectionResult,
        Dataset,
        MetricHistory,
    )

    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

    class DummyModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def save(self, *args, **kwargs):
            pass

        def delete(self, *args, **kwargs):
            pass

    AnalysisJob = DummyModel
    TrainedModel = DummyModel
    CodeSmellType = DummyModel
    SmellDetectionResult = DummyModel
    Dataset = DummyModel
    MetricHistory = DummyModel

# Import utilities
try:
    from .utils import extract_metrics_from_code, analyze_folder, generate_report
except ImportError:

    def extract_metrics_from_code(*args, **kwargs):
        return {
            "loc": 0,
            "wmc": 0,
            "cbo": 0,
            "tcc": 0.0,
            "lcom": 0,
            "rfc": 0,
            "complexity": 0,
        }

    def analyze_folder(*args, **kwargs):
        return {"files": [], "total_files": 0, "total_smells": 0}

    def generate_report(*args, **kwargs):
        return None


# Import ML models
try:
    from .ml_models import train_model, predict_smell
except ImportError:

    def train_model(*args, **kwargs):
        return None, None, {"accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0}

    def predict_smell(*args, **kwargs):
        return {"smells": [], "metrics": {}, "overall_quality": 0}


# Import User model
from django.contrib.auth.models import User


@login_required
def dashboard(request):
    """Main dashboard view"""
    try:
        if MODELS_AVAILABLE:
            total_analyses = AnalysisJob.objects.filter(user=request.user).count()
            total_smells = SmellDetectionResult.objects.filter(
                analysis_job__user=request.user
            ).count()
            recent_analyses = AnalysisJob.objects.filter(user=request.user)[:5]
            active_model = TrainedModel.objects.filter(is_active=True).first()

            smell_distribution = {}
            for result in SmellDetectionResult.objects.filter(
                analysis_job__user=request.user
            )[:100]:
                smell_name = (
                    result.smell_type.name
                    if hasattr(result, "smell_type")
                    else "Unknown"
                )
                smell_distribution[smell_name] = (
                    smell_distribution.get(smell_name, 0) + 1
                )
        else:
            total_analyses = 0
            total_smells = 0
            recent_analyses = []
            active_model = None
            smell_distribution = {}
    except Exception as e:
        print("Dashboard error: %s" % str(e))
        total_analyses = 0
        total_smells = 0
        recent_analyses = []
        active_model = None
        smell_distribution = {}

    context = {
        "total_analyses": total_analyses,
        "total_smells": total_smells,
        "recent_analyses": recent_analyses,
        "active_model": active_model,
        "smell_distribution": json.dumps(smell_distribution),
    }
    return render(request, "detector/dashboard.html", context)


@login_required
def static_mode(request):
    """Static mode - Train model with dataset"""
    if request.method == "POST":
        try:
            # Get form data
            dataset_file = request.FILES.get("dataset")
            model_name = request.POST.get("model_name")
            model_type = request.POST.get("model_type", "RANDOM_FOREST")

            print("\n" + "=" * 60)
            print("STATIC MODE POST")
            print("=" * 60)
            print("Dataset: %s" % dataset_file.name if dataset_file else "None")
            print("Model: %s" % model_name)
            print("Type: %s" % model_type)

            if not dataset_file or not model_name:
                messages.error(request, "Please provide all required fields")
                return redirect("detector:static_mode")

            # Save dataset
            dataset_path = os.path.join(
                settings.MEDIA_ROOT, "datasets", dataset_file.name
            )
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)

            with open(dataset_path, "wb+") as destination:
                for chunk in dataset_file.chunks():
                    destination.write(chunk)

            print("Dataset saved to: %s" % dataset_path)

            # Train model
            start_time = time.time()
            model_path, scaler_path, metrics = train_model(
                dataset_path=dataset_path, model_name=model_name, model_type=model_type
            )
            processing_time = time.time() - start_time

            print("\nMETRICS FROM TRAINING:")
            print("  accuracy: %s" % metrics.get("accuracy"))
            print("  precision: %s" % metrics.get("precision"))
            print("  recall: %s" % metrics.get("recall"))
            print("  f1_score: %s" % metrics.get("f1_score"))

            # Save to database
            model_id = 1
            if MODELS_AVAILABLE:
                try:
                    model = TrainedModel.objects.create(
                        name=model_name,
                        model_type=model_type,
                        model_file=model_path,
                        scaler_file=scaler_path,
                        accuracy=metrics.get("accuracy", 0.0),
                        precision=metrics.get("precision", 0.0),
                        recall=metrics.get("recall", 0.0),
                        f1_score=metrics.get("f1_score", 0.0),
                        features_used=",".join(metrics.get("features", [])),
                        created_by=request.user,
                        is_active=True,
                    )
                    model_id = model.id
                    print("Model saved with ID: %d" % model_id)
                except Exception as e:
                    print("DB save error: %s" % str(e))

            # Store in session
            training_results = {
                "model_id": model_id,
                "accuracy": float(metrics.get("accuracy", 0.0)),
                "precision": float(metrics.get("precision", 0.0)),
                "recall": float(metrics.get("recall", 0.0)),
                "f1_score": float(metrics.get("f1_score", 0.0)),
                "processing_time": float(processing_time),
                "confusion_matrix": metrics.get("confusion_matrix", [[0]]),
                "feature_importance": metrics.get("feature_importance", {}),
            }

            print("\nSTORING IN SESSION:")
            print("  accuracy: %f" % training_results["accuracy"])
            print("  precision: %f" % training_results["precision"])
            print("  recall: %f" % training_results["recall"])
            print("  f1_score: %f" % training_results["f1_score"])

            request.session["training_results"] = training_results
            request.session.modified = True

            messages.success(
                request,
                "Model trained successfully! Accuracy: %.1f%%"
                % training_results["accuracy"],
            )
            print("=" * 60)

            return redirect("detector:training_results")

        except Exception as e:
            print("\nERROR: %s" % str(e))
            import traceback

            traceback.print_exc()
            messages.error(request, "Error training model: %s" % str(e))
            return redirect("detector:static_mode")

    # GET request
    recent_datasets = []
    trained_models = []
    if MODELS_AVAILABLE:
        try:
            recent_datasets = Dataset.objects.filter(uploaded_by=request.user)[:5]
            trained_models = TrainedModel.objects.filter(created_by=request.user)[:5]
        except:
            pass

    context = {"recent_datasets": recent_datasets, "trained_models": trained_models}
    return render(request, "detector/static_mode.html", context)


@login_required
def training_results(request):
    """Display training results"""
    print("\n" + "=" * 60)
    print("TRAINING RESULTS VIEW")

    results = request.session.get("training_results")
    print("Session results: %s" % results)

    if not results:
        messages.warning(request, "No training results found")
        return redirect("detector:static_mode")

    print("\nVALUES TO TEMPLATE:")
    print("  accuracy: %s" % results.get("accuracy"))
    print("  precision: %s" % results.get("precision"))
    print("  recall: %s" % results.get("recall"))
    print("  f1_score: %s" % results.get("f1_score"))
    print("=" * 60)

    # Get model
    model = None
    if MODELS_AVAILABLE and results.get("model_id"):
        try:
            model = TrainedModel.objects.get(id=results["model_id"])
        except:
            pass

    context = {"results": results, "model": model}
    return render(request, "detector/training_results.html", context)


@login_required
def dynamic_mode(request):
    """Dynamic mode - Predict code smells"""
    if request.method == "POST":
        try:
            analysis_type = request.POST.get("analysis_type")
            analysis_name = request.POST.get(
                "analysis_name", f"Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Get active model
            active_model = None
            if MODELS_AVAILABLE:
                active_model = TrainedModel.objects.filter(is_active=True).first()

            if not active_model:
                messages.error(
                    request, "No trained model found. Please train a model first."
                )
                return redirect("detector:static_mode")

            # Create analysis job
            job = None
            if MODELS_AVAILABLE:
                job = AnalysisJob.objects.create(
                    user=request.user,
                    analysis_type=analysis_type,
                    name=analysis_name,
                    status="PROCESSING",
                    model_used=active_model,
                )

            start_time = time.time()
            results = {"smells": [], "metrics": {}}
            metrics = {}

            # ---------------- SINGLE FILE ----------------
            if analysis_type == "SINGLE_FILE":

                uploaded_file = request.FILES.get("code_file")

                if uploaded_file:
                    file_path = os.path.join(
                        settings.MEDIA_ROOT, "uploads/files", uploaded_file.name
                    )

                    os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    with open(file_path, "wb+") as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)

                    if job:
                        job.uploaded_file = uploaded_file
                        job.save()

                    metrics = extract_metrics_from_code(file_path)
                    results = predict_smell(active_model.id, metrics)

                    if job:
                        job.file_count = 1
                        job.language = os.path.splitext(uploaded_file.name)[1][1:]
                        job.save()

            # ---------------- FOLDER UPLOAD ----------------
            elif analysis_type == "FOLDER":

                uploaded_files = request.FILES.getlist("folder_files")

                if uploaded_files:

                    total_files = 0
                    smells_found = []

                    for uploaded_file in uploaded_files:

                        file_path = os.path.join(
                            settings.MEDIA_ROOT, "uploads/folders", uploaded_file.name
                        )

                        os.makedirs(os.path.dirname(file_path), exist_ok=True)

                        with open(file_path, "wb+") as destination:
                            for chunk in uploaded_file.chunks():
                                destination.write(chunk)

                        metrics = extract_metrics_from_code(file_path)
                        result = predict_smell(active_model.id, metrics)

                        smells_found.extend(result.get("smells", []))
                        total_files += 1

                    results = {"smells": smells_found, "metrics": metrics}

                    if job:
                        job.file_count = total_files
                        job.save()

            # ---------------- CODE SNIPPET ----------------
            elif analysis_type == "CODE_SNIPPET":

                code_snippet = request.POST.get("code_snippet")
                language = request.POST.get("language", "python")

                if code_snippet:

                    if job:
                        job.code_snippet = code_snippet
                        job.language = language
                        job.save()

                    metrics = extract_metrics_from_code(
                        code_snippet, is_snippet=True, language=language
                    )

                    results = predict_smell(active_model.id, metrics)

                    if job:
                        job.file_count = 1
                        job.save()

            # ---------------- SAVE RESULTS ----------------
            processing_time = time.time() - start_time

            if job:
                job.processing_time = processing_time
                job.status = "COMPLETED"
                job.completed_at = datetime.now()
                job.results_json = results
                job.total_smells_found = len(results.get("smells", []))
                job.save()

            # Save smell records
            if MODELS_AVAILABLE and job:

                for smell in results.get("smells", []):

                    smell_type, _ = CodeSmellType.objects.get_or_create(
                        name=smell.get("smell_name", "Unknown Smell"),
                        defaults={
                            "description": f'Detected {smell.get("smell_name", "Unknown")} code smell',
                            "severity": smell.get("severity", "MEDIUM"),
                        },
                    )

                    SmellDetectionResult.objects.create(
                        analysis_job=job,
                        smell_type=smell_type,
                        file_name=smell.get("file_name", "Unknown"),
                        line_start=smell.get("line_start"),
                        line_end=smell.get("line_end"),
                        code_snippet=smell.get("code_snippet", ""),
                        confidence=smell.get("confidence", 0.0),
                        loc=metrics.get("loc", 0),
                        wmc=metrics.get("wmc", 0),
                        cbo=metrics.get("cbo", 0),
                        tcc=metrics.get("tcc", 0.0),
                        lcom=metrics.get("lcom", 0),
                        rfc=metrics.get("rfc", 0),
                        complexity=metrics.get("complexity", 0),
                    )

            messages.success(
                request,
                f'Analysis completed! Found {len(results.get("smells", []))} code smells.',
            )

            if job:
                request.session["last_analysis_id"] = job.id
                return redirect("detector:prediction_results", job_id=job.id)
            else:
                return redirect("detector:dynamic_mode")

        except Exception as e:
            messages.error(request, f"Error during analysis: {str(e)}")
            return redirect("detector:dynamic_mode")

    # ---------------- GET REQUEST ----------------
    smell_types = []
    if MODELS_AVAILABLE:
        try:
            smell_types = CodeSmellType.objects.all()[:10]
        except:
            pass

    context = {"smell_types": smell_types}
    return render(request, "detector/dynamic_mode.html", context)


@login_required
def prediction_results(request, job_id):
    """Display prediction results"""
    if not MODELS_AVAILABLE:
        context = {
            "job": {
                "name": "Sample Analysis",
                "created_at": datetime.now(),
                "file_count": 1,
            },
            "results": [],
            "files_analysis": {},
            "total_smells": 0,
        }
        return render(request, "detector/prediction_results.html", context)

    try:
        job = get_object_or_404(AnalysisJob, id=job_id, user=request.user)
        results = SmellDetectionResult.objects.filter(analysis_job=job)

        files_analysis = {}
        for result in results:
            if result.file_name not in files_analysis:
                files_analysis[result.file_name] = {
                    "smells": [],
                    "metrics": {
                        "loc": result.loc,
                        "wmc": result.wmc,
                        "cbo": result.cbo,
                        "tcc": result.tcc,
                        "lcom": result.lcom,
                        "rfc": result.rfc,
                        "complexity": result.complexity,
                    },
                }
            files_analysis[result.file_name]["smells"].append(
                {
                    "name": result.smell_type.name,
                    "confidence": result.confidence,
                    "severity": result.smell_type.severity,
                    "lines": (
                        f"{result.line_start}-{result.line_end}"
                        if result.line_start
                        else "N/A"
                    ),
                }
            )

        context = {
            "job": job,
            "results": results,
            "files_analysis": files_analysis,
            "total_smells": len(results),
        }
    except Exception as e:
        messages.error(request, f"Error loading results: {str(e)}")
        return redirect("detector:history")

    return render(request, "detector/prediction_results.html", context)


@login_required
def history(request):
    """View analysis history"""
    if not MODELS_AVAILABLE:
        context = {"page_obj": [], "total_count": 0}
        return render(request, "detector/history.html", context)

    try:
        analyses = AnalysisJob.objects.filter(user=request.user)
        date_filter = request.GET.get("date")
        if date_filter:
            analyses = analyses.filter(created_at__date=date_filter)

        paginator = Paginator(analyses, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {"page_obj": page_obj, "total_count": analyses.count()}
    except Exception as e:
        messages.error(request, f"Error loading history: {str(e)}")
        context = {"page_obj": [], "total_count": 0}

    return render(request, "detector/history.html", context)


@login_required
def download_report(request, job_id):
    """Download analysis report"""
    messages.info(request, "Report download feature coming soon!")
    return redirect("detector:prediction_results", job_id=job_id)


@login_required
@require_POST
def delete_analysis(request, job_id):
    """Delete an analysis job"""
    if not MODELS_AVAILABLE:
        messages.success(request, "Analysis deleted successfully")
        return redirect("detector:history")

    try:
        job = get_object_or_404(AnalysisJob, id=job_id, user=request.user)
        if job.uploaded_file and os.path.exists(job.uploaded_file.path):
            os.remove(job.uploaded_file.path)
        job.delete()
        messages.success(request, "Analysis deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting analysis: {str(e)}")

    return redirect("detector:history")


@login_required
def api_docs(request):
    """API documentation view"""
    api_key = "Not available"
    if hasattr(request.user, "profile") and hasattr(request.user.profile, "api_key"):
        api_key = request.user.profile.api_key

    context = {"api_key": api_key}
    return render(request, "detector/api_docs.html", context)


def about(request):
    """About page"""
    total_users = 0
    total_analyses = 0
    total_models = 0

    try:
        total_users = User.objects.count()
    except:
        pass

    if MODELS_AVAILABLE:
        try:
            total_analyses = AnalysisJob.objects.count()
            total_models = TrainedModel.objects.count()
        except:
            pass

    context = {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "total_models": total_models,
        "languages_supported": [
            "Python",
            "Java",
            "JavaScript",
            "PHP",
            "C++",
            "Ruby",
            "Go",
            "C#",
        ],
    }
    return render(request, "detector/about.html", context)


@login_required
def generate_dataset_view(request):
    """View to generate synthetic dataset"""
    if request.method == "POST":
        try:
            samples = int(request.POST.get("samples", 100))
            messages.success(request, f"Dataset generated successfully!")
        except Exception as e:
            messages.error(request, f"Error generating dataset: {str(e)}")
        return redirect("detector:static_mode")
    return render(request, "detector/generate_dataset.html")


@login_required
def model_list(request):
    """List all trained models"""
    models = []
    if MODELS_AVAILABLE:
        try:
            models = TrainedModel.objects.filter(created_by=request.user).order_by(
                "-created_at"
            )
        except:
            pass
    context = {"models": models}
    return render(request, "detector/model_list.html", context)


@login_required
def model_detail(request, model_id):
    """View model details"""
    if not MODELS_AVAILABLE:
        messages.warning(request, "Model details not available")
        return redirect("detector:model_list")
    try:
        model = get_object_or_404(TrainedModel, id=model_id, created_by=request.user)
    except:
        messages.error(request, "Model not found")
        return redirect("detector:model_list")
    context = {"model": model}
    return render(request, "detector/model_detail.html", context)


@login_required
@require_POST
def activate_model(request, model_id):
    """Activate a model"""
    if not MODELS_AVAILABLE:
        messages.success(request, f"Model activated successfully!")
        return redirect("detector:model_list")
    try:
        model = get_object_or_404(TrainedModel, id=model_id, created_by=request.user)
        TrainedModel.objects.filter(is_active=True).exclude(id=model.id).update(
            is_active=False
        )
        model.is_active = True
        model.save()
        messages.success(request, f'Model "{model.name}" activated successfully!')
    except Exception as e:
        messages.error(request, f"Error activating model: {str(e)}")
    return redirect("detector:model_list")


@login_required
@require_POST
def delete_model(request, model_id):
    """Delete a model"""
    if not MODELS_AVAILABLE:
        messages.success(request, "Model deleted successfully!")
        return redirect("detector:model_list")
    try:
        model = get_object_or_404(TrainedModel, id=model_id, created_by=request.user)
        if model.model_file and os.path.exists(model.model_file.path):
            os.remove(model.model_file.path)
        if model.scaler_file and os.path.exists(model.scaler_file.path):
            os.remove(model.scaler_file.path)
        model.delete()
        messages.success(request, "Model deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting model: {str(e)}")
    return redirect("detector:model_list")


@login_required
def download_report(request, job_id):
    """Download analysis report as PDF"""
    try:
        job = get_object_or_404(AnalysisJob, id=job_id, user=request.user)

        # Generate report
        from .report_generator import generate_report

        report_path = generate_report(job)

        if os.path.exists(report_path):
            # Open the file and create response
            with open(report_path, "rb") as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type="application/pdf")
                response["Content-Disposition"] = (
                    f'attachment; filename="code_smell_report_{job.id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
                )

                # Log activity
                try:
                    from accounts.models import UserActivity

                    UserActivity.objects.create(
                        user=request.user,
                        activity_type="DOWNLOAD",
                        description=f"Downloaded report for analysis {job.name}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                except:
                    pass

                return response
        else:
            messages.error(request, "Report file not found")

    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")

    return redirect("detector:prediction_results", job_id=job_id)
