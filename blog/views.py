from django.http import HttpResponse
from django.shortcuts import render
from .models import Blogpost

# Create your views here.
def index(request):
    allblogs = Blogpost.objects.all()
    return render(request,'blog/index.html', {'allblogs': allblogs})

def blogpost(request, id):
    post = Blogpost.objects.filter(post_id = id)[0]
    allblogs = Blogpost.objects.all()
    for index, blog in enumerate( allblogs):
        if blog.post_id == id:
            if index != 0 and index < len(allblogs)-1:
                prev = allblogs[index - 1].post_id
                next = allblogs[index+1].post_id
            else: 
                if index == 0 and index < len(allblogs)-1:
                    prev = allblogs[len(allblogs) - 1].post_id
                    next = allblogs[1].post_id
                elif index == len(allblogs)-1 and index != 0:
                    prev = allblogs[index - 1].post_id
                    next = allblogs[0].post_id
                
        
    return render(request, 'blog/blogpost.html', {'post': post, 'next': next, 'prev': prev})