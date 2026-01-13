from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("upload/", views.upload_report_view, name="upload"),
    path("report/<int:id>/", views.report_detail_view, name="report_detail"),
    path('logout/', views.logout_view, name='logout'),
    path('report/<int:id>/ask',views.ask_report_question,name="ask_report_question"),
]
