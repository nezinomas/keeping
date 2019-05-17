from django.template.loader import render_to_string
from django.http import JsonResponse

from ..models import Expense


def form_valid(data):
    objects = (
        Expense.objects.all().
        prefetch_related('expense_type', 'expense_name', 'account')
    )
    data.update({
        'form_is_valid': True,
        'html_list': render_to_string(
            template_name='expenses/includes/partial_expenses_list.html',
            context={
                'objects': objects
            }
        )
    })


def save_data(request, context, form):
    data = {}

    if request.method == 'POST':
        if form.is_valid():
            form.save()

            form_valid(data)
        else:
            data['form_is_valid'] = False

    context.update({'form': form})
    data.update({
        'html_form': render_to_string(
            'expenses/includes/partial_expenses_form_modal.html',
            context,
            request
        )
    })

    return JsonResponse(data)
