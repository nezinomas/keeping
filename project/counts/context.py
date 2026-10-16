from .services.model_services import CountTypeModelService


def counts_menu(request):
    if not request.user.is_authenticated:
        return {"counts_menu": []}

    return {"counts_menu": CountTypeModelService(request.user).objects}
