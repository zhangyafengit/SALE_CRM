from django.conf.urls import url

from django.shortcuts import HttpResponse, redirect, render

from django.utils.safestring import mark_safe
from django.urls import reverse
from stark.utils.page import Pagination
from django.db.models import Q

# 通过showlist将要展示的类封装起来。在Modellist中调用这个类，进行实例化。
class Showlist(object):
    def __init__(self, conf_obj, request, queryset):  # 在这里接收我们需要的参数，这里的conf_obj就是我们传过来的self，也就是配置类对象。
        self.conf_obj = conf_obj
        self.request = request
        self.queryset = queryset

        print('*' * 50, self.conf_obj)
        # 分页
        current_page = self.request.GET.get("page")  # 当前页码
        pagination = Pagination(current_page, self.queryset.count(), self.request.GET, per_page_num=2)
        # 通过内置的分页类，来实例化出我们自己的分页方法。
        self.pagination = pagination
        self.page_queryset = self.queryset[self.pagination.start:self.pagination.end]

    def get_head_list(self):
        # 表头数据
        # header_list=["名称","价格","出版社"]
        header_list = []

        for field_or_func in self.conf_obj.get_new_list_display():  # ["title","price","publish",delete_col]

            if isinstance(field_or_func, str):  # 首先判断field_or_func是不是字符串。

                if field_or_func == "__str__":  # 再判断是不是是不是自定制的配置类。
                    val = self.conf_obj.model._meta.model_name.upper()  # 把取到的类名变大写。

                else:
                    field_obj = self.conf_obj.model._meta.get_field(
                        field_or_func)  # 这里的get_field是一个方法，字段对应的对象。app_label和model_name

                    val = field_obj.verbose_name  # 在上一步拿到对应的类对象，再拿到我们在类中定义的verbose_name属性。

            else:
                val = field_or_func(self.conf_obj, is_header=True)  # 如果field_or_func不是一个字符串，那么就是一个方法。

            header_list.append(val)
            # print(header_list)
        return header_list

    def get_data_list(self):
        # 表单数据
        data_list = []
        for obj in self.page_queryset:  # 得到的是分页之后的所有的数据。全部的对象[obj1,obj2,obj3]
            temp = []

            for field_or_func in self.conf_obj.get_new_list_display():  # list_display = ["title","price","publish",delete_col]

                if isinstance(field_or_func, str):  # 判断field_or_func是不是字符串。
                    val = getattr(obj, field_or_func)
                    if field_or_func in self.conf_obj.list_display_links:  # 判断字段是否在林科所中，如果在的话将其变成a标签。
                        val = mark_safe("<a href='%s'>%s</a>" % (self.conf_obj.get_reverse_url("change", obj), val))
                else:
                    val = field_or_func(self.conf_obj, obj)

                temp.append(val)

            data_list.append(temp)
            print(data_list)
        return data_list

    def get_actions(self):
        temp = []
        for func in self.conf_obj.actions:  # [patch_delete,]
            temp.append({
                "name": func.__name__,
                "desc": func.desc
            })

        return temp  # [{"name":"patch_delete","desc":"批量删除"},]

    # filter分类操作。
    def get_filter(self):
        # 取到的是一个字典key为表名，value为字段对一个的值
        filter_dict = {}
        for filter_field in self.conf_obj.list_filter:  # 从配置类对象中去到filter_field。
            filter_field_obj = self.conf_obj.model._meta.get_field(filter_field)  # 通过get_field拿到对应字段的对象。
            print('+'*50, filter_field)   # ++publish               ++ authors
            print(filter_field_obj)      # app01.Book.publish      app01.Book.authors
            queryset = filter_field_obj.rel.to.objects.all()
            # <QuerySet [<Publish: 人民出版社>, <Publish: 上海出版社>]> <QuerySet [<Author: 莫言>, <Author: 冰心>]>
            print(queryset)
            temp = []
            import copy
            params = copy.deepcopy(self.request.GET)

            # 渲染标签
            current_filter_field_id = self.request.GET.get(filter_field)  # 既然要渲染标签，那么我们首先要拿到标签的id。
            # 在for循环中，第一次为publish，然后为author
            #  all 的链接标签
            params2 = copy.deepcopy(self.request.GET)
            if filter_field in params2:    # 说明有字段被选中，那么进行all操作，的时候就是去掉被选中字段。
                params2.pop(filter_field)  # 点击all的时候应该把当前所有的字段去掉。
                all_link = "<a href='?%s'>All</a>" % params2.urlencode()  # 返回所有查询字符串参数的编码字符串。
            else:  # 否则的话直接清空。
                all_link = "<a href=''>All</a>"
            temp.append(all_link)

            for obj in queryset:
                params[filter_field] = obj.pk   #
                _url = params.urlencode()       # 生成对应的问号？后的参数。publish=1，publish=2，authors=1，authors=2
                print('='*50,_url)

                if current_filter_field_id == str(obj.pk):  # 如果当前选中的id等于我们对象关联的主键值，那么说明选中状态。
                    s = "<a class='item active' href='?%s'>%s</a>" % (_url, str(obj))
                else:                                       # 否则没被选中状态。
                    s = "<a class='item' href='?%s'>%s</a>" % (_url, str(obj))
                temp.append(s)

                filter_dict[filter_field] = temp   # 往filter_dict中添加键值。

        return filter_dict

# 
class ModelStark():  # 默认配置类对象。

    def __init__(self, model):
        self.model = model  # 引入model，self为model对应的配置类对象。
        self.model_name = self.model._meta.model_name
        self.app_label = self.model._meta.app_label
        self.app_model_name = (self.app_label, self.model_name)
        self.key_word = ""

    list_display = ["__str__"]  # 定制父类的list_display，当子类中没有重定义的时候使用。
    list_display_links = []  # 父类list_display_links默认为空。
    model_form_class = []  # 父类的model_form_class默认为空。

    actions = []  # 批量操作默认为空。

    search_fields = []  # 搜索字段默认为空。
    list_filter=[]

    # 通过反向解析的到对应的url。
    def get_reverse_url(self, type, obj=None):  # 关键字参数放到位置形参之后。

        url_name = "%s_%s_%s" % (self.app_label, self.model_name, type)
        if obj:
            _url = reverse(url_name, args=(obj.pk,))
        else:
            _url = reverse(url_name)

        return _url

        # print('*' * 50, _url)  # 反向解析出的url为： /stark/app01/book/1/delete/
        # return _url  # 这里的mark_safe相当于我们在HTML中的{{。。。| safe}}，返回一个a标签。

    #  自定制三个按钮：check，delete，edit。
    def delete_col(self, obj=None, is_header=False):  # 这里引入obj但是把它设成默认为None，为什么呢？因为我们在往new_list_display添加的时候，不需要obj。

        if is_header:
            return "删除"

        return mark_safe(
            "<a href='%s'>删除</a>" % self.get_reverse_url('delete',
                                                         obj))  # 这里的mark_safe相当于我们在HTML中的{{。。。| safe}}，返回一个a标签。

    def edit_col(self, obj=None, is_header=False):
        if is_header:
            return "编辑"
        return mark_safe(
            "<a href='%s'>删除</a>" % self.get_reverse_url('change',
                                                         obj))  # 这里的mark_safe相当于我们在HTML中的{{。。。| safe}}，返回一个a标签。

    def check_col(self, obj=None, is_header=False):
        if is_header:
            return "选择"

        return mark_safe("<input type='checkbox' name='selected_action' value=%s>"%obj.pk)

    def get_new_list_display(self):  # 新的list_display在原list_display的基础上添加了edit_col，delete_col，check_col。
        new_list_display = []

        new_list_display.extend(self.list_display)  # 使用extend直接扩展列表。
        if not self.list_display_links:  # 如果没有添加links，就添加edit_col这个选项。
            new_list_display.append(ModelStark.edit_col)  # 这里可以直接使用点
        new_list_display.append(ModelStark.delete_col)
        new_list_display.insert(0, ModelStark.check_col)  # 将check_col添加到第一位，因为位置形参。

        return new_list_display

    # 定义search函数，进行search操作。

    def search_filter(self, request, queryset):
        # search 操作

        key_word = request.GET.get("search")  # 通过取到search的值作为搜索的关键字。

        print(self.search_fields)  # ["title","price"]
        self.key_word = ""  # 如果没有输入的时候，输入框默认为空。
        if key_word:  # 如果输入框中输入了值。

            self.key_word = key_word

            search_condition = Q()  # 生成一个queryset对象。
            search_condition.connector = "or"  # 然后将Q查询逻辑变成 or
            for field in self.search_fields:
                search_condition.children.append((field + "__icontains", key_word))  # 向queryset中添加键值。查看字段中是否含有key_word。


            queryset = queryset.filter(search_condition)  # 然后再取出search_condition中的数据。

        return queryset

    # 定义一个filter_list
    def filter_list(self,request,queryset):
        # filter 操作
        filter_condition = Q()
        for key, val in request.GET.items():  # 拿到对应的url中的参数，publish=1&b=2这种格式的参数。
            if key in self.list_filter:
                filter_condition.children.append((key, val),)  # 这里为什么可以直接赋值？
        if filter_condition:
            queryset = queryset.filter(filter_condition)
        return queryset

    def list_view(self, request):
        """
       采用列表套列表的形式
        """
        #  action操作
        if request.method == "POST":  # 如果为post请求，那么就有数据。
            action = request.POST.get("action")  # 首先拿到action操作，以此来反射出action函数。
            pk_list = request.POST.getlist("selected_action")  # 选中的数据对应的pk。
            queryset = self.model.objects.filter(pk__in=pk_list)  # 通过pk可以取到对应对象。

            func = getattr(self, action)  # 通过反射拿到action方法。

            func(request, queryset)  # 执行该方法。

        # 用户访问的模型表：  self.model
        print("self.model:", self.model)
        queryset = self.model.objects.all()
        print("self.list_display", self.list_display)  # ["nid","title","price","publish"]

        # search操作
        queryset = self.search_filter(request, queryset)

        # filter 操作
        queryset = self.filter_list(request, queryset)

        showlist = Showlist(self, request, queryset)  # 在这里调用showlist类，将self，request，queryset传入showlist类，
                                                      # 实例化得到我们的一个对象，其中self表示当前类的配置类对象。

        # 通过反射拿到添加add的url
        add_url = self.get_reverse_url("add")

        return render(request, "stark/list_view.html", locals())

    def get_model_form_class(self):
        if self.model_form_class:  # 如果不为空，就是用自己的。
            return self.model_form_class
        else:  # 如果为空的话，也就是没有自定义的，就是用父类的。
            from django import forms

            class ModelFormDemo(forms.ModelForm):
                class Meta:
                    model = self.model
                    fields = "__all__"

            return ModelFormDemo

    # 分别写每个页面的功能，返回相应的页面。
    def add_view(self, request):
        """
          if GET请求：
           GET请求：
           form = BookModelForm()
           form:渲染

        if POST请求:
               form = BookModelForm(request.POST)
               form.is_valid()
               form.save()  # 添加数据 create

        :param request:
        :return:
        :param request: 
        :return: 
        """
        ModelFormDemo = self.get_model_form_class()
        from django.forms.boundfield import BoundField
        from django.forms.models import ModelChoiceField
        if request.method == 'GET':
            form = ModelFormDemo()
            for bfield in form :    # 这里我们要区分model中的类与form中的类。

                print(type(bfield.field))
                '''<class 'django.forms.fields.CharField'>
                    <class 'django.forms.fields.DateField'>
                    <class 'django.forms.fields.DecimalField'>
                    <class 'django.forms.models.ModelChoiceField'>
                    <class 'django.forms.models.ModelMultipleChoiceField'>
                '''
                print(bfield) # 可看出这个拿到的是输入框对应的所有信息。
                '''<input type="text" name="title" maxlength="32" required id="id_title" />
                    <input type="text" name="publishDate" required id="id_publishDate" />
                    <input type="number" name="price" step="0.01" required id="id_price" />
                    ...
                '''
                print(bfield.field)  # 拿到的是一个个对象。
                '''<django.forms.fields.CharField object at 0x00000181567FD9E8>
                '''
                if isinstance(bfield.field, ModelChoiceField):
                    bfield.is_pop = True  # 该对象属于这个类，那么就是应该加上pop功能。

                    filed_rel_model=self.model._meta.get_field(bfield.name).rel.to  # 通过表名拿到相关表
                    model_name=filed_rel_model._meta.model_name                     # 取到表名
                    app_label=filed_rel_model._meta.app_label                       # 取app名

                    _url = reverse("%s_%s_add" % (app_label, model_name))
                    bfield.url = _url + "?pop_back_id=" + bfield.auto_id              # 这里的auto_id可以自动取到对应id，这里拿到的url传到页面上去。
                   # 也可以写成这样bfield.url=url+"?pop_back_id="+bfield.name

            return render(request, 'stark/add_view.html', locals())
        else:
            form = ModelFormDemo(request.POST)
            if form.is_valid():
                obj = form.save()   # 可以直接拿到保存的对象。
                pop_back_id = request.GET.get("pop_back_id")   # 然后拿到返回页面的id。
                if pop_back_id:                                # 如果存在的话。
                    pk = obj.pk
                    text = str(obj)
                    return render(request, "stark/pop.html", locals())

                return redirect(self.get_reverse_url("list"))
            else:
                return render(request, "stark/add_view.html", locals())

    def change_view(self, request, id):
        ModelFormDemo = self.get_model_form_class()
        edit_obj = self.model.objects.get(pk=id)
        if request.method == "GET":
            form = ModelFormDemo(instance=edit_obj)
            return render(request, "stark/change_view.html", locals())
        else:
            form = ModelFormDemo(data=request.POST, instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_reverse_url("list"))
            else:
                return render(request, "stark/change_view.html", locals())

    def delete_view(self, request, id):
        if request.method == "POST":
            self.model.objects.get(pk=id).delete()
            return redirect(self.get_reverse_url("list"))

        list_url = self.get_reverse_url("list")
        return render(request, "stark/delete_view.html", locals())

    def get_urls(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        temp = [
            url("^$", self.list_view, name="%s_%s_list" % (self.app_model_name)),
            url("^add/$", self.add_view, name="%s_%s_add" % (self.app_model_name)),
            url("^(\d+)/change/$", self.change_view, name="%s_%s_change" % (self.app_model_name)),
            url("^(\d+)/delete/$", self.delete_view, name="%s_%s_delete" % (self.app_model_name)),
        ]

        return temp

    @property
    def urls(self):

        return self.get_urls(), None, None


class StarkSite(object):  # 用来创建单例的类，他给我们提供一个接口，每次调用都是一个实例对象。
    def __init__(self, name='admin'):
        self._registry = {}

    def register(self, model, admin_class=None, **options):
        if not admin_class:
            admin_class = ModelStark  # 配置类

        self._registry[model] = admin_class(model)

    # {Book:BookConfig(Book),Publish:ModelAdmin(Publish)}



    def get_urls(self):

        temp = [

        ]

        for model_class, config_obj in self._registry.items():  # 注册的类以及对应的配置类对象在_registry中。
            print("===>", model_class, config_obj)

            model_name = model_class._meta.model_name
            app_label = model_class._meta.app_label
            print("===>", app_label, model_name)

            temp.append(url(r'^%s/%s/' % (app_label, model_name), config_obj.urls))

        '''
        创建url：

            url("app01/book/$",self.list_view,name="app01_book_list"),
            url("app01/book/add$",self.add_view,name="app01_book_add"),
            url("app01/book/(\d+)/change/$",self.change_view),
            url("app01/book/(\d+)/delete/$",self.delete_view),



            url("app01/publish/$",self.list_view,name="app01_publish_list"),
            url("app01/publish/add$",self.add_view,name="app01_publish_add"),
            url("app01/publish/(\d+)/change/$",self.change_view),
            url("app01/publish/(\d+)/delete/$",self.delete_view),





        '''

        return temp

    @property
    def urls(self):

        return self.get_urls(), None, None


site = StarkSite()