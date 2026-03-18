"""
URL configuration for ScriptNova app.
"""
from django.urls import path
from ScriptNova.views import signupAPI, loginAPI, getByIdApi, updateAPI
from ScriptNova.views.Blogs import GenerateBlog, GenerateKeywords

app_name = 'ScriptNova'

urlpatterns = [
    # Authentication endpoints
    path('signup/', signupAPI.as_view(), name='signup'),
    path('login/', loginAPI.as_view(), name='login'),
    path('user/<int:id>/', getByIdApi.as_view(), name='get-user'),
    path('user/update/', updateAPI.as_view(), name='update-user'),
    path('generate-blog/', GenerateBlog.as_view(), name='generate-blog'),
    path("generate-keywords/", GenerateKeywords.as_view()),

]
