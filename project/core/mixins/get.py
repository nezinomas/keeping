class GetQuerysetMixin():
    context_object_name = 'items'

    def get_queryset(self):
        try:
            print(f'>>>>>>>>>> try year in {self.model}')
            qs = self.model.objects.year(self.request.user.profile.year)
        except Exception as e1:
            try:
                print(f'>>>>>>>>>> try intems because {e1}')
                qs = self.model.objects.items()
            except Exception as e2:
                print(f'>>>>>>>>>> all because {e2}')
                qs = self.model.objects.all()

        return qs


class GetFormKwargsMixin():
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['year'] = self.request.user.profile.year

        return kwargs
