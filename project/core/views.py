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
