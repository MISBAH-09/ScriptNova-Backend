# """
# URL configuration for ScriptNova app.
# """
# from django.urls import path
# from ScriptNova.views import signupAPI, loginAPI, getByIdApi, updateAPI
# from ScriptNova.views.Blogs import SaveBlog, BlogPublishView, GenerateBlog, GenerateKeywords, BlogListCreateView, BlogDetailView, BlogStatsView

# app_name = 'ScriptNova'

# urlpatterns = [
#     # Authentication endpoints
#     path('signup/', signupAPI.as_view(), name='signup'),
#     path('login/', loginAPI.as_view(), name='login'),
#     path('user/<int:id>/', getByIdApi.as_view(), name='get-user'),
#     path('user/update/', updateAPI.as_view(), name='update-user'),
#     path('generate-blog/', GenerateBlog.as_view(), name='generate-blog'),
#     path("generate-keywords/", GenerateKeywords.as_view()),
#     path('saveblog/',SaveBlog.as_view(), name='save-blog'),
#      path('', BlogListCreateView.as_view(), name='blog-list-create'),
#     path('stats/', BlogStatsView.as_view(), name='blog-stats'),
#     path('<int:pk>/', BlogDetailView.as_view(), name='blog-detail'),
#     path('<int:pk>/publish/', BlogPublishView.as_view(), name='blog-publish'),

# ]


from django.urls import path
from ScriptNova.views import signupAPI, loginAPI, getByIdApi, updateAPI
from ScriptNova.views.Blogs import (
    GenerateBlog,
    GenerateKeywords,
    BlogListCreateView,
    BlogDetailView,
    BlogStatsView,
    BlogPublishView,
)

app_name = 'ScriptNova'

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path('signup/', signupAPI.as_view(), name='signup'),
    path('login/', loginAPI.as_view(), name='login'),
    path('user/<int:id>/', getByIdApi.as_view(), name='get-user'),
    path('user/update/', updateAPI.as_view(), name='update-user'),

    # ── AI Generation ─────────────────────────────────────────────────────────
    path('generate-blog/', GenerateBlog.as_view(), name='generate-blog'),
    path('generate-keywords/', GenerateKeywords.as_view(), name='generate-keywords'),

    # ── Blog CRUD ─────────────────────────────────────────────────────────────
    # IMPORTANT: stats/ must come BEFORE <int:pk>/ or Django will try to match
    # "stats" as a pk integer and fail
    path('blogs/', BlogListCreateView.as_view(), name='blog-list-create'),
    path('blogs/stats/', BlogStatsView.as_view(), name='blog-stats'),
    path('blogs/<int:pk>/', BlogDetailView.as_view(), name='blog-detail'),
    path('blogs/<int:pk>/publish/', BlogPublishView.as_view(), name='blog-publish'),
]