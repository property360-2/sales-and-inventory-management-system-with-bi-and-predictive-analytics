from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('switch-branch/<int:branch_id>/', views.switch_branch, name='switch_branch'),
    path('list/', views.user_list, name='user_list'),
]