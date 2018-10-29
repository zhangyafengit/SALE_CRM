from app01.models import User, Role, Permmission
from django.shortcuts import HttpResponse, render, redirect
from django.conf.urls import url
from stark.service.stark import site, ModelStark

site.register(User)
site.register(Role)


class Permission_conf(ModelStark):
    list_display = ['title', 'url']
    list_display_links = ['title']


site.register(Permmission)


#####
from app01.models import *
site.register(UserInfo)
site.register(Department)
site.register(Course)

# 学校自定制类：
class SchoolConfig(ModelStark):
    list_display = ['title']

site.register(School, SchoolConfig)

# 自定制班级类
class ClassConfig(ModelStark):
    # 因为每个班级不止一个老师，所以如果要显示所有的老师，那么要使用自定制方法
    def teacher_display(self, obj=None, is_header=False):
        if is_header:    # 表头
            return "讲师"
        temp = []
        for i in obj.teachers.all():
            # 在classlist中，通过teachers与老师建立多对多的关系,正向查找按字段，找到所有的teacher。
            temp.append(i.name)
        return ",".join(temp)

    def classname_display(self, obj=None, is_header=False):
        # 拿到班级名，以及期数，展示出来。
        if is_header:
            return "班级"
        ret = "%s(%s)班" %(obj.course,str(obj.semester))  # obj为自定义配置类的对象。
        return ret
    list_display = [classname_display, 'tutor', teacher_display]

site.register(ClassList, ClassConfig)

class CustomerConfig(ModelStark):
    list_display = ['name', 'gender']

site.register(Customer, CustomerConfig)
site.register(ConsultRecord)

class StudentConfig(ModelStark):
    def class_display(self, obj=None,is_header=False):
        if is_header:
            return "已报班级"
        temp = []
        for i in obj.class_list.all():
            # 因为学生可以不止报一个班级。
            temp.append(str(i))  # 这里加str的目的是因为
        return ','.join(temp)
    list_display = ['customer', class_display]
site.register(Student, StudentConfig)

from django.utils.safestring import mark_safe

# 班级学习成绩记录
class ClassStudyRecordConfig(ModelStark):
    def study_display(self,obj=None,is_header=False):
        if is_header:
            return "学习详情"
        # 这里我们的url可以使用reverse来的到。
        _url="/stark/app01/studentstudyrecord/?classstudyrecord=%s"%obj.pk
        return mark_safe("<a href='%s'>学生学习记录</a>"%_url)
    def record_score_display(self,obj=None,is_header=False):
        if is_header:
            return "录入成绩"
        _url = "/stark/app01/studentstudyrecord/record_score/%s" % obj.pk
        return mark_safe("<a href='%s'>录入成绩</a>" % _url)
    list_display = ['class_obj','day_num','course_title',study_display,record_score_display]

    def patch_init(self,request,queryset):
        # 对班级成绩进行批量初始化
        for classstudyrecord_obj in queryset:
            # 查询与classstudyrecord_obj对应的班级下的所有学生
            student_list = Student.objects.filter(class_list=classstudyrecord_obj.class_obj.pk)
            print("student_list", student_list)
            for obj in student_list:
                StudentStudyRecord.objects.create(classstudyrecord=classstudyrecord_obj, student=obj)

    patch_init.desc = "批量创建学生学习记录"

    actions = [patch_init]

    # 班级成绩详情显示
    def record_score_view(self,request,classstudyrecord_id):
        if request.method == "GET":  # 查看班级成绩为GET请求
            # 得到对应班级的成绩
            classstudyrecord = ClassStudyRecord.objects.get(pk=classstudyrecord_id)
            # 得到班级下的学生成绩列表
            studentstudyrecord_list = StudentStudyRecord.objects.filter(classstudyrecord=classstudyrecord)
            # 学生成绩
            score_choices = StudentStudyRecord.score_choices
            # ok用于判断
            ok = request.GET.get("ok")

            return render(request, "record_score_view.html", locals())
        else:
            flag = True
            try:
                # 取数据
                print(request.POST)
                # 下面的操作主要是为了得到一个数据结构，{pk：{key:value}}
                update_dict = {}
                for key, val in request.POST.items():
                    if key == "csrfmiddlewaretoken":
                        continue
                    # 按下下划线分割而且只分割一次
                    field_name, pk = key.rsplit("_", 1)

                    if pk not in update_dict:

                        update_dict[pk] = {field_name: val}
                    else:
                        update_dict[pk][field_name] = val

                for pk, update_data in update_dict.items():
                    # 更新指定pk的学生成绩记录，使用**将字典打散
                    StudentStudyRecord.objects.filter(pk=pk).update(**update_data)
            except Exception as e:
                flag = False

            return redirect(request.path + "?ok=1")

    def extra_urls(self):

            temp = []

            temp.append(
                url("record_score/(\d+)", self.record_score_view)
            )

            return temp

site.register(ClassStudyRecord, ClassStudyRecordConfig)

class StudentStudyRecordConfig(ModelStark):
    def record_display(self, obj=None, is_header=False):
        if is_header:
            return "考勤"
        html = ""
        for t in StudentStudyRecord.record_choices:
            # 下面主要是设置默认的值，设置select框的默认值。
            if obj.record == t[0]:
                s = "<option selected value=%s>%s</option>" % t
            else:
                s = "<option value=%s>%s</option>" % t

            html += s

        return mark_safe("<select class='xxx' pk=%s >%s</select>" % (obj.pk, html))

    list_display = ["student", "classstudyrecord", "record", record_display, "score"]

    def patch_late(self, request, queryset):
        # 批量设置迟到
        queryset.update(record="late")

    patch_late.desc = "迟到"

    actions = [patch_late]

    def update_record(self, request):
        # 更新记录
        val = request.POST.get("val")
        student_record_pk = request.POST.get("student_record_pk")
        StudentStudyRecord.objects.filter(pk=student_record_pk).update(record=val)

        return HttpResponse("OK")

    def extra_urls(self):
        temp = []
        temp.append(
            url("update_record/", self.update_record)
        )
        return temp

site.register(StudentStudyRecord, StudentStudyRecordConfig)



















