from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Order
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from .forms import OrderUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def ad(request):
    return render(request, 'orders/ad.html')


def home(request):
    context = {
        'orders': Order.objects.filter(uAccount__isnull = True)
    }
    return render(request, 'orders/home.html', context)


class PostListView(ListView):
    model = Order
    template_name = 'orders/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'orders'
    paginate_by = 7


class UserPostListView(ListView):
    model = Order
    template_name = 'orders/user_orders.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'orders'
    paginate_by = 7

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Order.objects.filter(uAccount = user)


class PostDetailView(DetailView):
    model = Order
    template_name = 'orders/order_detail.html'  # <app>/<model>_<viewtype>.html



class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Order
    form_class = OrderUpdateForm

    def form_valid(self, form):
        form.instance.uAccount = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.get(pk=self.kwargs['pk'])
        return context

    def test_func(self):
        order = self.get_object()
        if self.request.user == order.uAccount:
            if order.status == 'status1' or order.status == 'status2':
                return True
        return False  

# @login_required
# def order(request):
#     if request.method == 'POST':
#         o_form = OrderUpdateForm(request.POST)
#         if o_form.is_valid():
#             o_form.save()
#             messages.success(request, f'The destination of your package has been updated!')
#             return redirect('order-detail')
#     else:
#         messages.success(request, f'Failed to update the destination!')

#     context = {
#         'o_form': o_form
#     }

#     return render(request, 'orders/order_detail.html', context)      

