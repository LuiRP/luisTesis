from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def profile(request):
    if request.method == "POST":
        if request.FILES.get("profile_picture"):
            user = request.user
            user.profile_picture = request.FILES["profile_picture"]
            user.save()
            return redirect("profile")
    return render(request, "account/profile.html")
