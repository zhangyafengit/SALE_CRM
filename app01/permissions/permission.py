from django.utils.deprecation import MiddlewareMixin
from  django.shortcuts import HttpResponse,redirect,render
import re

class  PermissionMiddleWare(MiddlewareMixin):  # 中间件

    def process_request(self, request):

        current_path=request.path

        # url的白名单

        white_list = ["/login/", "/reg/", "/admin/*", "/index/", "/logout/"]

        for reg in white_list:
            ret = re.search(reg, current_path)
            if ret:
                return None
        # 确定是否登陆

        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("/login/")

        # 校验权限

        permission_list=request.session.get("permission_list")

        # /stark/app01/user/1/change/

        for permission_rex in permission_list:

            permission_rex = "^%s$"%permission_rex
            ret=re.search(permission_rex,current_path)

            if ret:
                return None

        return HttpResponse("没有访问权限!")


