from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from .models import Product, Contact, Orders, OrderUpdate
import json
from math import ceil
from django.views.decorators.csrf import csrf_exempt
import hashlib
from paytmchecksum import PaytmChecksum
import razorpay
#Razorpay
RAZORPAY_KEY_ID = "rzp_test_xmNMq9SNRQI4E6h"
RAZORPAY_SECRET = "cwMAqz3M69w6T4flpY7gVvFgt"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))
#paytm
MERCHANT_KEY = 'bKMfNxPPf_QdZppa'

# Create your views here.
def index(request):
    allProds = []
    catprods = Product.objects.values('category','id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category = cat)
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allprods': allProds}
    return render(request,"shop/index.html",params)
def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False
def search(request):
    query = request.GET.get('search','')
    allProds = []
    catprods = Product.objects.values('category','id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category = cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n//4 + ceil((n/4)-(n//4))
        if len(prod) != 0:
         allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allprods': allProds}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request,"shop/search.html",params)
def about(request):
    return render(request,"shop/about.html")
def contact(request):
    if request.method == "POST":
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        desc = request.POST.get('desc','')
        contact = Contact(name=name,email=email,phone=phone,desc=desc)
        contact.save()
        massege = {'id':contact.msg_id, 'submit':True }
    else:
        massege = {'submit':False}
    return render(request,"shop/contact.html",massege)

def tracker(request):
    if request.method == "POST":
        orderId = request.POST.get('orderId','')
        email = request.POST.get('email','')
        try:
            order = Orders.objects.filter(order_id=orderId,email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text':item.update_desc, 'time':item.timestamp.isoformat()})
                    response = json.dumps({"status": "success", "updates": updates , "itemsJson": order[0].items_json}, default = str )
                return HttpResponse(response)
            else:
                return HttpResponse(json.dumps({"status": "no item"}))
        except Exception as e:
            return HttpResponse(json.dumps({"status": "error"}))           
    return render(request,"shop/tracker.html")

def productView(request, myid):
    # Fetch the product using the id
    product = Product.objects.filter(id = myid)
    return render(request,"shop/prodView.html", {'product': product[0]})

def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemJson','')
        name = request.POST.get('name','')
        amount = int(request.POST.get('amount',''))*100
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        address = request.POST.get('address1','') +" "+request.POST.get('address2','')
        city = request.POST.get('city','')
        state = request.POST.get('state','')
        pin_code = request.POST.get('pin_code','')
        payment_method = request.POST.get('payment_method', '')
        # Request paytm to transfer the amount to your account after payment  by user
        if payment_method == "paytm":
           param_dict = {
            "MID": 'DIY12386817555501617',
            "ORDER_ID": str(email),
            "CUST_ID": str(phone), 
            "MOBILE_NO": str(phone),  
            "EMAIL": email,  
            "CHANNEL_ID": 'WEB',
           "TXN_AMOUNT": str(amount),
           "WEBSITE": 'WEBSTAGING', 
           "INDUSTRY_TYPE_ID": 'Retail',
            "CALLBACK_URL": "http://127.0.0.1:8000/shop/handlerequest/"
        }
           paytm_checksum = PaytmChecksum.generateSignature(param_dict, MERCHANT_KEY)  
           param_dict["CHECKSUMHASH"] = paytm_checksum
           return render(request, 'shop/paytm.html', {'param_dict': param_dict})
        # Request razorpay to transfer the amount to your account after payment  by user
        elif payment_method == "razorpay":
            razorpay_order = razorpay_client.order.create({
                "amount": amount  ,
                "currency": "INR",
                "payment_capture": "1"
                })
            return render(request, "shop/razorpay.html", {
                "payment_order_id": razorpay_order["id"],
                "razorpay_key": RAZORPAY_KEY_ID,
                "amount": amount // 100 ,"items_json" : items_json, "name": name,"email": email,"phone":phone,"address":address,"city":city,"state":state , "pin_code": pin_code
            })
    else:
        context = {'thank': False}
    return render(request,"shop/checkout.html", context) 
def checkout_success(request, id):
    order = get_object_or_404(Orders, order_id=id)  
    return render(request, "shop/checkout_success.html", {'order': order})



#callback url for rozerpay
@csrf_exempt
def razorpay_success(request):
    if request.method == "POST":
        print("hello")
        
        try:
            data = json.loads(request.body)  # ✅ Parse only if request is POST

            # order_id = data.get("payment_order_id")
            payment_order_id = data.get("payment_order_id")
            payment_id = data.get("payment_id")
            payment_status = data.get("status")
            name = data.get("name")
            email = data.get("email")
            address = data.get("address")
            phone = data.get("phone")
            amount = data.get("amount")
            items_json = data.get("items_json")
            city = data.get("city")
            pin_code = data.get("pin_code")
            state = data.get("state")
            # ✅ Order का Status Update करें
            order = Orders(payment_order_id = payment_order_id, name = name, payment_id = payment_id, payment_status = payment_status, email = email, phone = phone, address = address, amount = amount, items_json = items_json, city = city, pin_code = pin_code, state = state)
            order.save()  # ✅ Save the updated order
            # Use filter().first() for safety
            update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
            update.save()
            return JsonResponse({"success": True, "order_id" : order.order_id}) 
            
        
        except Orders.DoesNotExist:
            return JsonResponse({"success": False, "message": "Order Not Found"})
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON Data"})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    else:
        return JsonResponse({"success": False, "message": "Invalid Request Method"}, status=400)

@csrf_exempt
def handlerequest(request):
    #paytm will send  you post request here
    return HttpResponse("Done")
