from django.core.files import File as Files
import datetime
from django.utils import timezone
from django.utils.crypto import get_random_string
import os
from rest_framework import generics, status, mixins
from rest_framework import authentication, permissions
from functools import partial
from django.db.models.query import QuerySet
from rest_framework import generics
from rest_framework.decorators import APIView
from . import serializers
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from .models import Account, Invitation
from rest_framework.renderers import JSONRenderer
from PIL import Image
from io import BytesIO
import base64
from django.conf import settings
from rest_framework.decorators import authentication_classes, permission_classes
from users import serializers
from users import models
from rest_framework import authentication, exceptions
import jwt

class LoginView(APIView):
    serializer_class = serializers.LoginSerializer
    permission_classes = (permissions.AllowAny, )
    
    def post(self, request):
        data = request.data
        email = data.get('email', '')
        password = data.get('password', '')
        user = Account.objects.filter(email = email).first()
        if(user == None):
            raise exceptions.AuthenticationFailed(
                'Invalid credentials!')
        else:
            password_validity = user.check_password(password)
            if (password_validity):
                auth_token = jwt.encode(
                        {'client': 'add_the_client_here', 'mall':'add_the_mall_here', 'username': user.username}, settings.JWT_SECRET_KEY, algorithm="HS256")
                serializer = serializers.UserSerializer(user)
                data = {'user': serializer.data, 'token': auth_token}
                response = Response()
                response.set_cookie(key='token', value=auth_token, httponly=True)
                response.data = data
                return response
            else:
                raise exceptions.AuthenticationFailed(
                    'Invalid credentials!')
                        
class AccountList(APIView):
    def get(self, request):
        users = Account.objects.all()
        serializer = serializers.AccountSerializer(users, many=True)
        content = serializer.data
        return Response(content, status=status.HTTP_200_OK)

class InviteUserView(APIView):
    serializer_class = serializers.InvitationSerializer
    permission_classes = [permissions.IsAdminUser]
    def post(self, request):
        serializer = serializers.InvitationSerializer(data=request.data)
        if serializer.is_valid():
            invitee_email = serializer.validated_data.get('email')
            check_in_userlist = Account.objects.filter(email=invitee_email)
            if(len(check_in_userlist) != 0):
                content = {'error': 'Invited User is already existing. !!!'}
                return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else:
                invitee_firstname = serializer.validated_data.get(
                    'firstname').capitalize()
                invitee_lastname = serializer.validated_data.get(
                    'lastname').capitalize()
                is_admin = serializer.validated_data.get('is_admin')
                record = models.Invitation.objects.filter(
                    invitee_email=invitee_email)
                if(len(record) != 0):
                    record = models.Invitation.objects.get(
                        invitee_email=invitee_email)
                    record.inviter = request.user
                    record.invitee_firstname = invitee_firstname
                    record.invitee_lastname = invitee_lastname
                    record.inviting_key = get_random_string(64).lower()
                    record.invited_date = timezone.now()
                    record.invite_expiry_date = timezone.now() + datetime.timedelta(3)
                    record.is_admin = is_admin
                    record.save()
                    record.send_mail()
                    content = {
                        'message': 'Invitation Updated Successfully !!!'}
                    return Response(content, status=status.HTTP_200_OK)
                else:
                    temp_model = models.Invitation.objects.create(
                        invitee_email=invitee_email,
                        invitee_firstname=invitee_firstname,
                        invitee_lastname=invitee_lastname,
                        inviter=request.user,
                        is_admin=is_admin,
                        inviting_key=get_random_string(64).lower(),
                        invited_date=timezone.now(),
                        invite_expiry_date=(
                            timezone.now() + datetime.timedelta(3)),
                    )
                    temp_model.send_mail()
                    content = {'message': 'User Invited Successfully !!!'}
                    return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'error': 'Submitted data is not valid !!!'}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)


class InvitedUsersView(generics.ListAPIView):
    queryset = Invitation.objects.all()
    serializer_class = serializers.InvitedUsersSerializer


class ActivateUserView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, key, format=None):
        record = Invitation.objects.get(inviting_key=key)
        print('record', record)
        
        try:
            record = Invitation.objects.get(inviting_key=key)
            user = models.Account.objects.filter(
                email=record.invitee_email)
            if(len(user) != 0):
                content = {'error': 'Invited User is already Active !!!'}
                return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            else:
                if (record.invite_expiry_date >= timezone.now()):
                    registration_key = get_random_string(64).lower()
                    record.registration_key = registration_key
                    record.save()
                    content = {
                        "registration_key": registration_key,
                        "email": record.invitee_email
                    }
                    return Response(content, status=status.HTTP_200_OK)
                else:
                    content = {'error': 'The link is expired !!!'}
                    return Response(content, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except:
            content = {'error': 'Invitation not found !!!'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)
    def post(self, request, key):
        serializer = serializers.ActivateUserSerializer(data=request.data)
        if serializer.is_valid():
            invitee_email = serializer.validated_data.get('email')
            qs = Invitation.objects.filter(invitee_email=invitee_email)
            if (len(qs) == 0):
                content = {'error': 'Invitation not found !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            elif (qs[0].registration_key != key):
                content = {'error': 'Invalid registration key !!!'}
                return Response(content, status=status.HTTP_404_NOT_FOUND)
            else:
                record = qs[0]
                Account.objects.create(
                    email=record.invitee_email,
                    username=record.invitee_email,
                    first_name=record.invitee_firstname,
                    last_name=record.invitee_lastname,
                    is_active=True,
                    is_admin=record.is_admin,
                    password=make_password(
                        serializer.validated_data.get('password'))
                )
                record.delete()
                content = {'Success': 'User Activated Successfully !!!'}
                return Response(content, status=status.HTTP_202_ACCEPTED)

class AccountDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = serializers.AccountSerializer
    
class AccountEditView(APIView):
    def put(self, request, pk):
        try:
            record = Account.objects.get(pk=pk)
            data = request.data
            record.first_name = data['first_name']
            record.last_name = data['last_name']
            record.password = make_password(data['password'])
            record.is_admin = data['is_admin']
            record.save()
            serialized = serializers.AccountSerializer(
                Account.objects.get(pk=pk)).data
            return Response(serialized, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Error occured !"}, status=status.HTTP_400_BAD_REQUEST)





class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers. AccountSerializer

    def get_object(self):
        object = Account.objects.get(id=self.request.user.id)
        return object


class AvatarUpdateView(APIView):
    # lookup_field = [self.request.user]
    serializer_class = serializers.AvatarUpdateSerializer
    # def get_queryset(self):
    #     return Account.objects.filter(email=self.request.user)

    def get_object(self, queryset=None):
        obj = Account.objects.get(email=self.request.user)
        return obj
    # def get(self, request):
    #     serializer = ProfileSerializer(self.get_object())
    #     return Response(serializer.data, status = status.HTTP_200_OK)

    def post(self, request):
        serializer = serializers.AvatarUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # print(serializer.data['avatar'].split('base64,')[1])
            imagedata = serializer.data['avatar'].split(',')[1]
            # print(imagedata)
            avatar = Image.open(BytesIO(base64.b64decode(imagedata)))
            if avatar.width > 200:
                avatar = avatar.resize((200, 200))
            avatar = avatar.convert('RGB')
            blob = BytesIO()
            avatar.save(blob, 'JPEG')
            avatar = Files(blob)

            # avatar.show()
            userobject = self.get_object()
            # print(settings.BASE_URL)
            userobject.avatar.save('name.jpg', avatar)
            # avatar.save(os.path.join(settings.MEDIA_ROOT, 'profile_images', str(userobject.id)+'-'+userobject.first_name+'.png'))
            # userobject.save(settings.MEDIA_URL + '123.pnsettings.MEDIA_ROOT, 'profile_images', str(userobject.id)+'-'+userobject.first_name+'.png')g')
            # userobject.avatar = '/profile_images/'+ str(userobject.id)+'-'+userobject.first_name+'.png'
            # userobject.save()
            # content = {
            #     "avatar": 'media/profile_images/'+ str(userobject.id)+'-'+userobject.first_name+'.png'
            # }
            content = serializers.AccountSerializer(userobject).data
        #     serializer.save()
        return Response(content, status=status.HTTP_202_ACCEPTED)


class ChangePasswordView(APIView):
    serializer_class = serializers.ChangePasswordSerializer

    def get_object(self, queryset=None):
        obj = Account.objects.get(email=self.request.user)
        return obj

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        # retrieve_password_otp = int(request.data['retrieve_password_otp'])
        record = self.get_object()
        # if (retrieve_password_otp == record.retrieve_password_otp):
        if serializer.is_valid():
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password')
            if(request.user.check_password(old_password)):
                record.password = make_password(new_password)
                record.save()
                # Now we need to make same changes in the global user available in client model also
                with schema_context('public'):
                    client_user = ClientModels.ClientUsers.objects.get(
                        email=self.request.user)
                    client_user.password = make_password(new_password)
                    client_user.save()

                content = {'Success': 'Password Updated Successfully !!!'}
                return Response(content, status=status.HTTP_200_OK)
            else:
                content = {
                    'error': 'Old password provided is not matching !!!'}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)
        else:
            try:
                content = {'error': serializer.errors['password'][0]}
            except:
                content = {'error': 'The input details are not valid!'}
            return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ForgotPasswordSerializer

    def get(self, request, email, format=None):
        try:
            record = Account.objects.get(email=email)
            record.forgot_password()
            content = {
                'message': f'Please enter the OTP received in your email {email}'}
            return Response(content, status=status.HTTP_202_ACCEPTED)
        except:
            content = {'error': 'User not found !!!'}
            return Response(content, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, email):
        serializer = serializers.ForgotPasswordSerializer(data=request.data)
        retrieve_password_otp = int(request.data['retrieve_password_otp'])
        record = Account.objects.get(email=email)
        if (retrieve_password_otp == record.retrieve_password_otp):
            if serializer.is_valid():
                password = serializer.validated_data.get('password')
                record.password = make_password(password)
                record.save()

                with schema_context('public'):
                    client_user = ClientModels.ClientUsers.objects.get(
                        email=email)
                    client_user.password = make_password(password)
                    client_user.save()

                content = {'Success': 'Pasword Updated Successfully !!!'}
                return Response(content, status=status.HTTP_200_OK)
            else:
                try:
                    content = {'error': serializer.errors['password'][0]}
                except:
                    content = {'error': 'The input details are not valid!'}
                return Response(content, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            content = {'error': 'Provided OTP is invalid !!!'}
            return Response(content, status=status.HTTP_403_FORBIDDEN)


class UpdateUserView(APIView):
    serializer_class = serializers.InvitationSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        id = request.data['id']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        is_admin = request.data['is_admin']
        user = models.Account.objects.get(id=id)
        user.first_name = first_name
        user.last_name = last_name
        user.is_admin = is_admin
        user.save()
        content = {'message': 'User has been updated successfully!'}
        return Response(content, status=status.HTTP_200_OK)


class DeleteUserView(APIView):
    serializer_class = serializers.InvitationSerializer
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        id = request.data['id']
        user = models.Account.objects.get(id=id)
        try:
            with schema_context('public'):
                public_user_instance = ClientModels.objects.get(
                    email=user.email)
                public_user_instance.delete()
        except:
            pass
        user.delete()
        content = {'message': 'User has been deleted successfully!'}
        return Response(content, status=status.HTTP_200_OK)





# class AccountCreateView(APIView):
#     def post(self, request):
#         data = request.data
#         email = data['email']
#         username = data['username']
#         # Now test, the account with same email is existing or not
#         tempEmailCheck = Account.objects.filter(email=email)
#         tempUsernameCheck = Account.objects.filter(username=username)
#         if len(tempEmailCheck) > 0:
#             return Response({"message": "User with same email address already exists !"}, status=status.HTTP_401_UNAUTHORIZED)
#         elif len(tempUsernameCheck) > 0:
#             return Response({"message": "User already exists !"}, status=status.HTTP_401_UNAUTHORIZED)
#         else:
#             try:
#                 created_object = Account.objects.create(
#                     username=username,
#                     email=email,
#                     first_name=data['first_name'],
#                     last_name=data['last_name'],
#                     password=make_password(request.data['password']),
#                     is_active=True,
#                     is_admin=request.data['is_admin'],
#                     is_staff=True,
#                 )
#                 serialized = serializers.AccountSerializer(created_object).data
#                 return Response(serialized, status=status.HTTP_200_OK)
#             except:
#                 return Response({"message": "Error occured !"}, status=status.HTTP_400_BAD_REQUEST)

#         # if serializer.is_valid():
#         #     print(">>>>>>>>>>>>>>>>>>>>>>>>")
#         #     password = make_password(request.data['password'])
#         #     serializer.save(password=password)
#         #     return Response(serializer.data)
#         # else:
#         #     print(serializer.errors)
#         #     return Response(serializer.errors)
