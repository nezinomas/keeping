from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse


@login_required()
def set_year(request, year, view_name):

    user = request.user
    user.profile.year = year
    user.save()

    return redirect(
        reverse(
            view_name,
            kwargs={}
        )
    )


@login_required
def set_month(request, month, view_name):
    user = request.user
    user.profile.month = month
    user.save()

    return redirect(
        reverse(
            view_name,
            kwargs={}
        )
    )


@login_required
def index(request):
    return render(request, 'core/index.html')
