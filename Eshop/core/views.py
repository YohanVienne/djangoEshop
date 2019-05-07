from django.shortcuts import render
from django.views.generic import ListView


def HomeView(request):
    return render(request, "home.html")
    # model = Item
    # paginate_by = 10
    # template_name = "home.html"
