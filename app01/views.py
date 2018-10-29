from django.shortcuts import render, HttpResponse, redirect
from app01.models import User


# Create your views here.


# 登录校验

def login(request):
    if request.method == 'POST':
        user = request.POST.get('username')
        pwd = request.POST.get('pwd')
        user = User.objects.filter(username=user, pwd=pwd).first()
        if user:  # 如果存在那么校验成功。
            request.session['user_id'] = user.pk  # 保存登录状态在session表中
            request.session['username'] = user.username

            # 权限列表
            permission_list = []
            permissions = user.roles.all().values("permmissions__url", "permmissions__code",
                                                  "permmissions__title").distinct()  # 从permission表跨到role表，取出值之后进行过滤。
            # print(permissions)
            permisssion_menu_list = []  # 权限菜单
            for item in permissions:
                permission_list.append(item.get("permmissions__url"))

                if item.get("permmissions__code") == "list":    # 在这里只过滤permission为list功能的。
                    permisssion_menu_list.append({
                        "url": item.get("permmissions__url"),
                        "title": item.get("permmissions__title"),
                    })   # 在permission_menu_list中添加，对应的权限名以及对应的url。

            print(permission_list)

            print(permisssion_menu_list)

            # 注册权限列表到session中
            request.session["permission_list"] = permission_list

            # 注册权限字典到字典中

            request.session["permisssion_menu_list"] = permisssion_menu_list

            return redirect("/index/")

    return render(request, "login.html")

        # url白名单
        # 确定登录状态
        # 校验权限。


def index(request):

    return render(request,'index.html')


def logout(request):
    request.session.flush()
    return redirect('/index/')
