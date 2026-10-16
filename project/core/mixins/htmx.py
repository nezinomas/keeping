class HxResponseMixin:
    hx_trigger_django = ""
    hx_redirect = ""

    def get_hx_trigger_django(self):
        return self.hx_trigger_django

    def get_hx_redirect(self):
        return self.hx_redirect
