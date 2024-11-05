from django.shortcuts import render
from django.http import JsonResponse,QueryDict
from kubernetes import client
from devops import k8s

@k8s.self_login_required
def pvc(request):
    return render(request, 'storage/pvc.html')

@k8s.self_login_required
def pvc_api(request):
    # 命名空间选择和命名空间列表功能使用
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    namespace = request.GET.get("namespace")
    data = []  # [{},{}]
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    if request.method == "GET":
        # 调用k8s api，获取命名空间，返回一个json数据
        search_key = request.GET.get('search_key')
        try:
            for pvc in core_api.list_namespaced_persistent_volume_claim(namespace=namespace).items:
                name = pvc.metadata.name
                namespace = pvc.metadata.namespace
                labels = pvc.metadata.labels
                storage_class_name = pvc.spec.storage_class_name
                access_modes = pvc.spec.access_modes
                capacity = (pvc.status.capacity if pvc.status.capacity is None else pvc.status.capacity["storage"])
                volume_name = pvc.spec.volume_name
                status = pvc.status.phase
                create_time = k8s.dt_format(pvc.metadata.creation_timestamp)

                pvc = {"name": name, "namespace": namespace, "lables": labels,
                       "storage_class_name": storage_class_name, "access_modes": access_modes, "capacity": capacity,
                       "volume_name": volume_name, "status": status, "create_time": create_time}

                # 搜索，适配带条件查询
                if search_key:
                    if search_key in name:
                        data.append(pvc)
                else:
                    data.append(pvc)
            code = 0
            msg = "查询成功"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限！"
            else:
                msg = "查询失败！"
            code = 1
        count = len(data)
        # 适配命名空间选择
        if request.GET.get('page'):
            current_page = int(request.GET.get('page',1))
            page_item_num = int(request.GET.get('limit', 10))
            start = (current_page - 1) * page_item_num
            end = current_page * page_item_num
            data = data[start:end]
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)
    elif request.method == "POST":
        # 新增
        pass
    elif request.method == "DELETE":
        # 删除
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_persistent_volume_claim(namespace=namespace, name=name)
            code = 0
            msg = "删除成功！"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有删除权限！"
            else:
                msg = "删除失败！"
            code = 1
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
    elif request.method == "PUT":
        # 更新
        pass

@k8s.self_login_required
def configmap(request):
    return render(request, 'storage/configmaps.html')

@k8s.self_login_required
def configmap_api(request):
    # 命名空间选择和命名空间列表功能使用
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    namespace = request.GET.get("namespace")
    data = []  # [{},{}]
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    if request.method == "GET":
        # 调用k8s api，获取命名空间，返回一个json数据
        search_key = request.GET.get('search_key')
        try:
            for cm in core_api.list_namespaced_config_map(namespace=namespace).items:
                name = cm.metadata.name
                namespace = cm.metadata.namespace
                data_length = ("0" if cm.data is None else len(cm.data))
                create_time = k8s.dt_format(cm.metadata.creation_timestamp)

                cm = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                # 搜索，适配带条件查询
                if search_key:
                    if search_key in name:
                        data.append(cm)
                else:
                    data.append(cm)
            code = 0
            msg = "查询成功"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限！"
            else:
                msg = "查询失败！"
            code = 1
        count = len(data)
        # 适配命名空间选择
        if request.GET.get('page'):
            current_page = int(request.GET.get('page',1))
            page_item_num = int(request.GET.get('limit', 10))
            start = (current_page - 1) * page_item_num
            end = current_page * page_item_num
            data = data[start:end]
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)
    elif request.method == "POST":
        # 新增
        pass
    elif request.method == "DELETE":
        # 删除
        print(request.body)
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_config_map(namespace=namespace, name=name)
            code = 0
            msg = "删除成功！"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有删除权限！"
            else:
                msg = "删除失败！"
            code = 1
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
    elif request.method == "PUT":
        # 更新
        pass

@k8s.self_login_required
def secret(request):
    return render(request, 'storage/secrets.html')

@k8s.self_login_required
def secret_api(request):
    # 命名空间选择和命名空间列表功能使用
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    namespace = request.GET.get("namespace")
    data = []  # [{},{}]
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    if request.method == "GET":
        # 调用k8s api，获取命名空间，返回一个json数据
        search_key = request.GET.get('search_key')
        try:
            for secret in core_api.list_namespaced_secret(namespace=namespace).items:
                name = secret.metadata.name
                namespace = secret.metadata.namespace
                data_length = ("空" if secret.data is None else len(secret.data))
                create_time = k8s.dt_format(secret.metadata.creation_timestamp)

                se = {"name": name, "namespace": namespace, "data_length": data_length, "create_time": create_time}
                # 搜索，适配带条件查询
                if search_key:
                    if search_key in name:
                        data.append(se)
                else:
                    data.append(se)
            code = 0
            msg = "查询成功"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有访问权限！"
            else:
                msg = "查询失败！"
            code = 1
        count = len(data)
        # 适配命名空间选择
        if request.GET.get('page'):
            current_page = int(request.GET.get('page',1))
            page_item_num = int(request.GET.get('limit', 10))
            start = (current_page - 1) * page_item_num
            end = current_page * page_item_num
            data = data[start:end]
        result = {'code': code, 'msg': msg, 'count': count, 'data': data}
        return JsonResponse(result)
    elif request.method == "POST":
        # 新增
        pass
    elif request.method == "DELETE":
        # 删除
        print(request.body)
        request_data = QueryDict(request.body)
        name = request_data.get("name")
        namespace = request_data.get("namespace")
        try:
            core_api.delete_namespaced_secret(namespace=namespace, name=name)
            code = 0
            msg = "删除成功！"
        except Exception as e:
            status = getattr(e, 'status')
            if status == 403:
                msg = "没有删除权限！"
            else:
                msg = "删除失败！"
            code = 1
        result = {'code': code, 'msg': msg}
        return JsonResponse(result)
    elif request.method == "PUT":
        # 更新
        pass
