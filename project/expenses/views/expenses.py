from django.shortcuts import render


def lists(request):
    return render(request, 'expenses/expenses_list.html')


def new(request):
    pass


def update(request, pk):
    pass


def delete(request, pk):
    pass
