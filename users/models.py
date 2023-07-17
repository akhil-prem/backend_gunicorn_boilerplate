import threading
from django.db import models
from django.template.loader import render_to_string
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from django.core.mail import EmailMessage


class MyUserManager(BaseUserManager):
    def create_user(self, email, first_name, password):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
        )
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, password=None):
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user


def content_file_name(instance, filename):
    path = '/avatars/' + str(instance.id) + '.png'
    return path


class Account(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=255, null=True)
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    avatar = models.ImageField(
        upload_to=content_file_name, null=True, blank=True)
    retrieve_password_otp = models.IntegerField(blank=True, null=True)
    objects = MyUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    def save(self, *args, **kwargs):
        print(self.email)
        self.username = self.email
        super().save(*args, **kwargs)
        return self

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def forgot_password(self):
        # self.retrieve_password_link = get_random_string(64).lower()
        self.retrieve_password_otp = randint(100000, 999999)
        self.save()
        # invitee = self.invitee
        # inviter = self.inviter
        # url = settings.HOST_ADDRESS_FRONT_END + '/invited/' + self.inviting_key
        template_name = 'users/forgot_password.html'

        context = {
            "otp": self.retrieve_password_otp,
            "name": self.first_name
        }
        subject = "Reset your Abaci Signage password"
        sender = settings.ADMIN_EMAIL
        receivers = [self.email]
        html_message = render_to_string('users/forgot_password.html', context)
        temp_emailsending = SendEmail(
            subject, html_message, sender, receivers).start()
        # temp_emailsending.run()


class SendEmail(threading.Thread):
    def __init__(self, subject, html_message, sender, receivers):
        self.subject = subject
        self.html_message = html_message
        self.sender = sender
        self.receivers = receivers
        threading.Thread.__init__(self)

    def run(self):
        message = EmailMessage(
            self.subject, self.html_message, self.sender, self.receivers)
        message.content_subtype = 'html'
        message.send()


class Invitation(models.Model):
    invitee_email = models.EmailField(null=True)
    invitee_firstname = models.CharField(max_length=100, null=True)
    invitee_lastname = models.CharField(max_length=100, null=True)
    inviter = models.ForeignKey(
        Account, related_name='inviter', on_delete=models.CASCADE, null=True)
    is_admin = models.BooleanField(null=True)
    inviting_key = models.CharField(max_length=100, blank=True, null=True)
    registration_key = models.CharField(max_length=100, blank=True, null=True)
    invited_date = models.DateTimeField(
        verbose_name='created', default=timezone.now)
    invite_expiry_date = models.DateTimeField(
        verbose_name='created', null=True)
    choices = [('A', 'Accepted'), ('P', 'Pending')]
    invitation_status = models.CharField(
        max_length=10, choices=choices, default='P')
    def send_mail(self):
        invitee_email = self.invitee_email
        inviter = self.inviter
        url = settings.SIGNUP_URL + self.inviting_key
        template_name = 'users/invite_email.html'

        if (isinstance(self.invitee_firstname, type(None))):
            invitee_name = "Invitee"
        else:
            invitee_name = self.invitee_firstname
            if (isinstance(self.invitee_lastname, type(None))):
                pass
            else:
                invitee_name += " " + self.invitee_lastname

        if (isinstance(self.inviter.first_name, type(None))):
            inviter_name = "Inviter"
        else:
            inviter_name = self.inviter.first_name
            if (isinstance(self.inviter.last_name, type(None))):
                pass
            else:
                inviter_name += " " + self.inviter.last_name

        context = {
            "invitee": invitee_name,
            "inviter": inviter_name,
            "link": url
        }
        subject = "Invitation to Join SUEZ MYWASTE"
        sender = settings.ADMIN_EMAIL
        receivers = [self.invitee_email]
        html_message = render_to_string(template_name, context)
        temp_emailsending = SendEmail(
            subject, html_message, sender, receivers).start()
