from django.shortcuts import render
from django.http import JsonResponse,QueryDict
from kubernetes import client
from devops import k8s

@k8s.self_login_required
def service(request):
    return render(request, 'loadbalancer/services.html')

@k8s.self_login_required
def service_api(request):
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
            for svc in core_api.list_namespaced_service(namespace=namespace).items:
                name = svc.metadata.name
                namespace = svc.metadata.namespace
                labels = svc.metadata.labels
                type = svc.spec.type
                cluster_ip = svc.spec.cluster_ip
                ports = []
                for p in svc.spec.ports:  # 不是序列，不能直接返回
                    port_name = p.name
                    port = p.port
                    target_port = p.target_port
                    protocol = p.protocol
                    node_port = ""
                    if type == "NodePort":
                        node_port = " <br> NodePort: %s" % p.node_port

                    port = {'port_name': port_name, 'port': port, 'protocol': protocol, 'target_port': target_port,
                            'node_port': node_port}
                    ports.append(port)

                selector = svc.spec.selector
                create_time = k8s.dt_format(svc.metadata.creation_timestamp)

                # 确认是否关联Pod
                endpoint = ""
                for ep in core_api.list_namespaced_endpoints(namespace=namespace).items:
                    if ep.metadata.name == name and ep.subsets is None:
                        endpoint = "未关联"
                    else:
                        endpoint = "已关联"

                svc = {"name": name, "namespace": namespace, "type": type,
                       "cluster_ip": cluster_ip, "ports": ports, "labels": labels,
                       "selector": selector, "endpoint": endpoint, "create_time": create_time}
                # 搜索，适配带条件查询
                if search_key:
                    if search_key in name:
                        data.append(svc)
                else:
                    data.append(svc)
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
            core_api.delete_namespaced_service(namespace=namespace, name=name)
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
def ingress(request):
    return render(request, 'loadbalancer/ingresses.html')

@k8s.self_login_required
def ingress_api(request):
    # 命名空间选择和命名空间列表功能使用
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    namespace = request.GET.get("namespace")
    data = []  # [{},{}]
    k8s.load_auth_config(auth_type, token)
    networking_api = client.NetworkingV1beta1Api()

    if request.method == "GET":
        search_key = request.GET.get('search_key')
        try:
            for ing in networking_api.list_namespaced_ingress(namespace=namespace).items:
                name = ing.metadata.name
                namespace = ing.metadata.namespace
                labels = ing.metadata.labels
                service = "None"
                http_hosts = "None"
                for h in ing.spec.rules:
                    host = h.host
                    path = ("/" if h.http.paths[0].path is None else h.http.paths[0].path)
                    service_name = h.http.paths[0].backend.service_name
                    service_port = h.http.paths[0].backend.service_port
                    http_hosts = {'host': host, 'path': path, 'service_name': service_name,
                                  'service_port': service_port}

                https_hosts = "None"
                if ing.spec.tls is None:
                    https_hosts = ing.spec.tls
                else:
                    for tls in ing.spec.tls:
                        host = tls.hosts[0]
                        secret_name = tls.secret_name
                        https_hosts = {'host': host, 'secret_name': secret_name}

                create_time = k8s.dt_format(ing.metadata.creation_timestamp)

                ing = {"name": name, "namespace": namespace, "labels": labels, "http_hosts": http_hosts,
                       "https_hosts": https_hosts, "service": service, "create_time": create_time}

                # 搜索，适配带条件查询
                if search_key:
                    if search_key in name:
                        data.append(ing)
                else:
                    data.append(ing)
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
            networking_api.delete_namespaced_ingress(namespace=namespace, name=name)
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
