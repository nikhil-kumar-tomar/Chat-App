from django.shortcuts import render,HttpResponseRedirect, HttpResponse
from .forms import *
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .miscellaneous import object_exists, object_creator
from django.db.models import Q
from django.views import View
import redis
from chat.models import Chats 
from django.conf import settings

# Create your views here.

class registration(View):
    form_class = user_create
    template_name = "chat_platform/registration.html"

    def get(self, request):
        context = {
            "form": self.form_class,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = self.form_class(request.POST)
        if User.objects.filter(Q(email = request.POST["email"]) | Q(username = request.POST["username"])):
            messages.error(request,"Email or Username Already Exists, Please use a different email")
            return HttpResponseRedirect("/registration/")

        if form.is_valid():
            form.save()
            messages.success(request, "Signed Up Successfully")
            return HttpResponseRedirect("/login/")
        else:
            messages.error(request, f"{form.errors}")
            
        return HttpResponseRedirect("/registration/")

class logins(View):
    
    form_class = user_sign
    template_name = "chat_platform/login.html"
    def get(self, request):
        context={
            "form": self.form_class,
        }
        return render(request, self.template_name, context)
        
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(username = request.POST.get("username"),
                                password = request.POST.get("password") 
                                )
   
            if user != None:
                login(request,user)
                messages.success(request,f"Welcome {request.user.first_name}, You have Logged In Succesfully")
                return HttpResponseRedirect("/join_room/")
            
            messages.error(request,"Email/Password does not exist")
            return HttpResponseRedirect("/login/")

class logouts(View):
    
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "Logout Successfull")
            return HttpResponseRedirect("/login/")

        messages.error(request,"Logout failed, Not Logged in currently")
        return HttpResponseRedirect("/login/")
        


def index(request):
    
    return render(request, "chat_platform/index.html")

def room(request, room_name):
    context = {
        "room_name": room_name,
    }
    if "_" in room_name:
        if request.user.id is None or not f"{request.user.id}" in room_name:
            return render(request, "chat_platform/401_forbidden.html",context={})
        
    return render(request, "chat_platform/room.html", context = context)

def private_room(request, user_1, user_2):
    redis_connection = redis.from_url(settings.CACHES["default"]["LOCATION"])
    private_rooms = [
        f"chat_{user_1}_{user_2}",
        f"chat_{user_2}_{user_1}"
        ]
    for room in private_rooms:
        if redis_connection.exists(f"{room}") or redis_connection.exists(f"asgi:group:{room}"):
            room = room.replace("chat_", "")
            return HttpResponseRedirect(f"/room/{room}/")
        elif Chats.objects.filter(room=room).exists():
            room = room.replace("chat_", "")
            return HttpResponseRedirect(f"/room/{room}/")
    
    return HttpResponseRedirect(f"/room/{user_1}_{user_2}/")
