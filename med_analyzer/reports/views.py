from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, UploadReportForm
from django.http import JsonResponse
from .models import MedicalReport
from pathlib import Path
from .pipeline_wrapper import process_report  # We will wrap your pipeline
import json
from .chatbot.chat_service import answer_report_question

def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "reports/home.html")

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "reports/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
    return render(request, "reports/login.html")

@login_required
def dashboard_view(request):
    reports = MedicalReport.objects.filter(user=request.user)
    return render(request, "reports/dashboard.html", {"reports": reports})

@login_required
def upload_report_view(request):
    if request.method == "POST":
        form = UploadReportForm(request.POST, request.FILES)

        if form.is_valid():
            report_obj = form.save(commit=False)
            report_obj.user = request.user
            report_obj.save()

            try:
                report_path = Path(report_obj.upload.path)
                report_json, llm_explanation = process_report(report_path)

                report_obj.report_json = report_json
                report_obj.llm_explanation = llm_explanation
                report_obj.processed = True
                report_obj.save()

                return redirect("dashboard")

            except RuntimeError as e:
                if str(e) == "AI_QUOTA_EXCEEDED":
                    # Delete the uploaded object since we don't want partial state
                    report_obj.delete()

                    form.add_error(None, "AI service is temporarily unavailable due to usage limits. Please try again later.")
                    return render(request, "reports/upload.html", {"form": form})

                raise  # unknown runtime error → crash visibly during dev

            except Exception as e:
                report_obj.delete()
                form.add_error(None, f"Processing failed: {str(e)}")
                return render(request, "reports/upload.html", {"form": form})

    else:
        form = UploadReportForm()

    return render(request, "reports/upload.html", {"form": form})

@login_required
def report_detail_view(request, id):
    report = get_object_or_404(MedicalReport, id=id, user=request.user)

    # Only allow access if the report has been processed
    if not report.processed:
        return redirect("dashboard")

    return render(request, "reports/report_detail.html", {"report": report})

def logout_view(request):
    logout(request)  # Log the user out
    return redirect("login")

@login_required
@require_POST
def ask_report_question(request, id):
    try:
        report= get_object_or_404(MedicalReport, id=id, user=request.user)

        data=json.loads(request.body)
        question=data.get("question","").strip()

        if not question:
            return JsonResponse({"answer":"please ask a valid question."})
        
        answer=answer_report_question(
            report_json=report.report_json,
            llm_explanation=report.llm_explanation,
            question=question,
        )

        return JsonResponse({"answer":answer})

    except Exception as e:
            print("❌ CHATBOT ERROR:", str(e))  # VERY IMPORTANT
            return JsonResponse(
                {"answer": "Internal error while answering your question."},
                status=500
            )