from django.urls import path
from . import views

urlpatterns = [
    path('login', views.LoginView.as_view()),
    path('userslist', views.AccountList.as_view()),
    path('inviteuser', views.InviteUserView.as_view()),
    path('inviteduserlist', views.InvitedUsersView.as_view()),
    path('activateuser/<str:key>', views.ActivateUserView.as_view()),
    path('userdetails/<int:pk>', views.AccountDetail.as_view(), name="user-detail"),
    path('profile/', views.ProfileView.as_view(), name="profile"),
    path('avatarupdate/', views.AvatarUpdateView.as_view()),
    path('changepassword/', views.ChangePasswordView.as_view()),
    path('forgotpassword/<str:email>', views.ForgotPasswordView.as_view()),
    path('deleteuser/', views.DeleteUserView.as_view()),
    path('updateuser/', views.UpdateUserView.as_view()),
]