from django.shortcuts import redirect


# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return redirect("/balance")
    else:
        return redirect("/accounts/login")
