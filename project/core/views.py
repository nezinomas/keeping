from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, reverse


@login_required()
def set_year(request, year, view_name):
    request.session['year'] = year
    return redirect(
        reverse(
            view_name,
            kwargs={}
        )
    )
