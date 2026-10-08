from django.urls import path
from . import auth, views

urlpatterns = [
    path('health', views.health), path('catalog', views.catalog),
    path('auth/csrf', auth.csrf), path('auth/register', auth.register), path('auth/login', auth.login),
    path('auth/logout', auth.logout), path('auth/me', auth.me),
    path('resumes', views.reports), path('resumes/<str:resource_id>', views.report_detail),
    path('drafts', views.drafts), path('drafts/<str:resource_id>', views.draft_detail), path('drafts/<str:resource_id>/pdf', views.draft_pdf),
    path('exams', views.exam_start), path('exams/active', views.exam_active), path('exams/<str:resource_id>', views.exam_detail),
    path('exams/<str:resource_id>/answers', views.exam_answer), path('exams/<str:resource_id>/events', views.exam_event),
    path('exams/<str:resource_id>/heartbeat', views.exam_heartbeat), path('exams/<str:resource_id>/submit', views.exam_submit),
    path('leaderboard', views.leaderboard), path('progress', views.progress),
    path('interviews', views.interview_start), path('interviews/<str:resource_id>', views.interview_detail), path('interviews/<str:resource_id>/answers', views.interview_answer),
    path('coding', views.coding_start), path('coding/<str:resource_id>', views.coding_detail), path('coding/<str:resource_id>/submissions', views.coding_submit),
    path('submissions/<str:resource_id>', views.submission_detail),
]
