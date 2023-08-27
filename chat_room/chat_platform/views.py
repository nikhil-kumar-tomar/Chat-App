from django.shortcuts import render,HttpResponseRedirect
from .forms import *
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .miscellaneous import object_exists, object_creator
from django.db.models import Q
from django.views import View

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
        print(request.POST)
        if User.objects.filter(Q(email = request.POST["email"]) | Q(username = request.POST["username"])):
            messages.error(request,"Email or Username Already Exists, Please use a different email")

        if form.is_valid():
            instance = form.save()
            print(instance)
            messages.success(request, "Signed Up Successfully")
            return HttpResponseRedirect("/login/")
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
    return render(request, "chat_platform/room.html", context = context)


