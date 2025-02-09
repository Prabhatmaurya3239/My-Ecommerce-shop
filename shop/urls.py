from django.contrib import admin
from django.urls import path
from .import views

urlpatterns = [
    path("", views.index, name="ShopHome"),
    path("about/", views.about, name="AboutUs"),
    path("contact/", views.contact, name="ContactUs"),
    path("tracker/", views.tracker, name="TrackingStatus"),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path("search/", views.search, name="Search"),
    path("checkout/", views.checkout, name="checkout"),
    path("handlerequest/", views.handlerequest, name = "HandleRequest"),
    path('payment/razorpay_success/', views.razorpay_success, name='razorpay_success'),
    path('checkout_success/<int:id>', views.checkout_success, name="checkout_success")
]
