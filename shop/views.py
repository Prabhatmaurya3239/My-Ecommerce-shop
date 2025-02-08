from django.http import HttpResponse,JsonResponse
from django.shortcuts import render,redirect
from .models import Product, Contact, Orders, OrderUpdate
import json
from math import ceil
from django.views.decorators.csrf import csrf_exempt
import hashlib
from paytmchecksum import PaytmChecksum
import razorpay
#Razorpay
RAZORPAY_KEY_ID = "rzp_test_xmNMq9SNRQI4E6"
RAZORPAY_SECRET = "cwMAqz3M69w6T4flpY7gVvFg"
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
                    response = json.dumps([updates , order[0].items_json], default = str )
                return HttpResponse(response)
            else:
                return HttpResponse({})
        except Exception as e:
            return HttpResponse({})           
    return render(request,"shop/tracker.html")

def productView(request, myid):
    # Fetch the product using the id
    product = Product.objects.filter(id = myid)
    return render(request,"shop/prodView.html", {'product': product[0]})

def search(request):
    return render(request,"shop/search.html")

def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemJson','')
        name = request.POST.get('name','')
        amount = request.POST.get('amount','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        address = request.POST.get('address1','') +" "+request.POST.get('address2','')
        city = request.POST.get('city','')
        state = request.POST.get('state','')
        pin_code = request.POST.get('pin_code','')
        order = Orders( items_json = items_json, name=name,email=email,phone=phone,address=address,city=city,state=state,pin_code=pin_code, amount = amount)
        OI = order.order_id
        order.save()
        context = { 'id' : order.order_id, 'thank' : True}
        payment_method = request.POST.get('payment_method', '')
        # Request paytm to transfer the amount to your account after payment  by user
        if payment_method == "paytm":
           param_dict = {
            "MID": 'DIY12386817555501617',
            "ORDER_ID": str(order.order_id),
            "CUST_ID": str(order.order_id), 
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
                "amount": amount ,
                "currency": "INR",
                "payment_capture": "1"
            })
            order = Orders.objects.filter(order_id=order.order_id).first()
            print(order)
            order.payment_order_id = razorpay_order["id"]
            order.save()
            return render(request, "shop/razorpay.html", {
                "payment_order_id": razorpay_order["id"],
                "razorpay_key": RAZORPAY_KEY_ID,
                "amount": amount
            })
    else:
        context = {'thank': False}
    return render(request,"shop/checkout.html", context)
def checkout_success(request):
    return render(request, "shop/checkout_success.html")



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
            status = data.get("status")
            

            # ✅ Order का Status Update करें
            order = Orders.objects.filter(payment_order_id=payment_order_id).first()  # Use filter().first() for safety

            if order:
                print(f"Updating Order: {order}")
                order.payment_status = status  
                order.payment_id = payment_id 
                update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
                update.save()
                order.save()  # ✅ Save the updated order
            else:
                 print(f"Order with order_id={order} not found!")
            return JsonResponse({"success": True})
            
        
        except Orders.DoesNotExist:
            return JsonResponse({"success": False, "message": "Order Not Found"})
            print("hello2")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON Data"})

        except Exception as e:
            print("this")
            return JsonResponse({"success": False, "message": str(e)})

    else:
        return JsonResponse({"success": False, "message": "Invalid Request Method"}, status=400)

@csrf_exempt
def handlerequest(request):
    #paytm will send  you post request here
    return HttpResponse("Done")
