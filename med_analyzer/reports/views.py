from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, UploadReportForm
from .models import MedicalReport
from pathlib import Path
from .pipeline_wrapper import process_report  # We will wrap your pipeline

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

            # Process report in the background or immediately
            report_path = Path(report_obj.upload.path)
            report_json, llm_explanation = process_report(report_path)

            report_obj.report_json = report_json
            report_obj.llm_explanation = llm_explanation
            report_obj.processed = True
            report_obj.save()

            return redirect("dashboard")
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