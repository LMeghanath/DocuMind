from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/',views.login_view,name='login'),
    path('signup/',views.signup_view,name='signup'),
    path('logout/',views.logout_view,name='logout'),
    path('chatpage/',views.chatpage,name='chatpage'),
    path('profile/',views.profile_view,name='profile'),
    path('delete_account/',views.delete_account_view,name='delete_account'),
    path('password_reset/',views.password_reset_view,name='password_reset'),
]