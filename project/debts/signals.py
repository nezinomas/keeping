from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.db.models import Model
from .models import Debt, DebtReturn
from .services.model_services import DebtReturnModelService


@receiver(post_save, sender=DebtReturn)
@receiver(post_delete, sender=DebtReturn)
def update_debt_model(sender: object, instance: Model, *args, **kwargs):
    user = instance.debt.journal.users.first()
    debt_type = instance.debt.debt_type

    total_return = DebtReturnModelService(user, debt_type).total_returned_for_debt(instance)

    debt = Debt.objects.get(pk=instance.debt.pk)
    debt.returned = total_return
    debt.save(update_fields=["returned"])