from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from ...core.lib.utils import int_or_zero
from ..forms_import import ReceiptUploadForm, ReviewFormSet, ReviewReceiptForm
from ..receipts.errors import UnreadableReceiptTextError, UnrecognisedReceiptError
from ..receipts.reader import ReceiptReader
from ..services.model_services import ExpenseKeywordModelService
from ..services.receipt_import import ReceiptImport

UPLOAD_TEMPLATE = "expenses/includes/import_upload.html"
REVIEW_TEMPLATE = "expenses/includes/import_review.html"


def _review_context(
    receipt_form, formset, *, lines_total, receipt_total, shop_money, shop_money_line
):
    return {
        "receipt_form": receipt_form,
        "formset": formset,
        "shop_money": shop_money,
        "shop_money_line": shop_money_line,
        "lines_total": lines_total,
        "receipt_total": receipt_total,
        "totals_disagree": lines_total != receipt_total + shop_money,
    }


class Import(View):
    template_name = "expenses/import.html"

    def get(self, request):
        form = ReceiptUploadForm(user=request.user)
        return render(request, self.template_name, {"upload_form": form})

    def post(self, request):
        upload_form = ReceiptUploadForm(
            user=request.user, data=request.POST, files=request.FILES
        )
        if not upload_form.is_valid():
            return render(request, UPLOAD_TEMPLATE, {"upload_form": upload_form})

        try:
            receipt = ReceiptReader.read(upload_form.cleaned_data["pdf"])
        except UnrecognisedReceiptError:
            upload_form.add_error(
                "pdf", _("This PDF is not a receipt from a supported shop.")
            )
            return render(request, UPLOAD_TEMPLATE, {"upload_form": upload_form})
        except UnreadableReceiptTextError:
            upload_form.add_error("pdf", _("The receipt could not be read."))
            return render(request, UPLOAD_TEMPLATE, {"upload_form": upload_form})

        upload_html = render_to_string(
            UPLOAD_TEMPLATE, {"upload_form": upload_form}, request
        )
        review_html = render_to_string(
            REVIEW_TEMPLATE,
            self._review_context_for(request, receipt, upload_form),
            request,
        )
        return HttpResponse(upload_html + review_html)

    def _review_context_for(self, request, receipt, upload_form):
        date = upload_form.cleaned_data["date"]
        account = upload_form.cleaned_data["account"]
        keywords = ExpenseKeywordModelService(request.user).year(date.year)

        receipt_initial = ReviewReceiptForm.initial_from(receipt, date, account)
        receipt_form = ReviewReceiptForm(user=request.user, initial=receipt_initial)
        formset = ReviewFormSet(
            initial=ReviewFormSet.initial_from(receipt, keywords),
            shop_money=receipt.shop_money,
            shop_money_line=receipt_initial["shop_money_line"],
            form_kwargs={"user": request.user, "year": date.year},
        )

        return _review_context(
            receipt_form,
            formset,
            lines_total=receipt.lines_total,
            receipt_total=receipt.total,
            shop_money=receipt.shop_money,
            shop_money_line=receipt_initial["shop_money_line"],
        )


class ImportSave(View):
    def post(self, request):
        receipt_form = ReviewReceiptForm(user=request.user, data=request.POST)
        receipt_valid = receipt_form.is_valid()

        year = request.user.year
        if receipt_valid:
            year = receipt_form.cleaned_data["date"].year

        shop_money = int_or_zero(request.POST.get("shop_money"))
        shop_money_line = int_or_zero(request.POST.get("shop_money_line"))

        formset = ReviewFormSet(
            data=request.POST,
            shop_money=shop_money,
            shop_money_line=shop_money_line,
            form_kwargs={"user": request.user, "year": year},
        )
        formset_valid = formset.is_valid()

        if not receipt_valid or not formset_valid:
            lines_total = sum(
                form.cleaned_data.get("price") or 0 for form in formset.forms
            )
            context = _review_context(
                receipt_form,
                formset,
                lines_total=lines_total,
                receipt_total=int_or_zero(request.POST.get("total")),
                shop_money=shop_money,
                shop_money_line=shop_money_line,
            )
            return render(request, REVIEW_TEMPLATE, context)

        ReceiptImport.save(
            lines=formset.reviewed_lines(),
            shop_money=receipt_form.cleaned_data["shop_money"],
            date=receipt_form.cleaned_data["date"],
            account=receipt_form.cleaned_data["account"],
            journal=request.user.journal,
        )
        return HttpResponseClientRedirect(
            reverse(
                "expenses:index",
                kwargs={"month": receipt_form.cleaned_data["date"].month},
            )
        )
