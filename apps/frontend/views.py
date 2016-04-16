from django.shortcuts import render

from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "frontpage.html"


class DetectionStatusView(TemplateView):
    template_name = "status.html"

    def get_context_data(self, *args, **kwargs):
        ret = super(DetectionStatusView, self).get_context_data(*args, **kwargs)
        return ret


