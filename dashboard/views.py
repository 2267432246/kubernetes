from django.shortcuts import render,redirect,HttpResponse
from django.http import JsonResponse
from devops import k8s
import hashlib,random
from dashboard.models import User
from kubernetes import client
from dashboard import node_data

# Create your views here.
@k8s.self_login_required
def index(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    # 命名空间：ajax从接口获取动态渲染
    # 计算资源（echart）：ajax从接口获取动态渲染
    # 存储资源：下面获取，模板渲染
    # 节点状态：下面获取，模板渲染

    node_resource = node_data.node_resource(core_api)
    pv_list = []
    for pv in core_api.list_persistent_volume().items:
        pv_name = pv.metadata.name
        capacity = pv.spec.capacity["storage"]  # 返回字典对象
        access_modes = pv.spec.access_modes
        reclaim_policy = pv.spec.persistent_volume_reclaim_policy
        status = pv.status.phase
        if pv.spec.claim_ref is not None:
            pvc_ns = pv.spec.claim_ref.namespace
            pvc_name = pv.spec.claim_ref.name
            claim = "%s/%s" %(pvc_ns,pvc_name)
        else:
            claim = "未关联PVC"
        storage_class = pv.spec.storage_class_name
        create_time = k8s.dt_format(pv.metadata.creation_timestamp)

        data = {"pv_name": pv_name, "capacity": capacity, "access_modes": access_modes,
                "reclaim_policy": reclaim_policy, "status": status,
                "claim": claim,"storage_class": storage_class,"create_time": create_time}
        pv_list.append(data)

    return render(request, 'index.html', {"node_resource": node_resource, "pv_list": pv_list})

# 计算资源（echart）
def node_resource(request):
    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)
    core_api = client.CoreV1Api()

    res = node_data.node_resource(core_api)
    return  JsonResponse(res)

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        token = request.POST.get("token")
        # 处理token登录
        if token:
            # 验证你的token是不是有效，对于k8s来说这个token能不能用，如果能用跳转到首页
            if k8s.auth_check('token', token):
                request.session['is_login'] = True
                request.session['auth_type'] = "token"
                request.session['token'] = token # 还需要标识用户，之前我们写的是用户名
                code = 0
                msg = "登录成功"
            else:
                code = 1
                msg = "Token无效！"
        else:
        # 处理kubeconfig文件登录
            file_obj = request.FILES.get("file")
            # 生成一个随时字符串（token）保存到session中作为kubeconfig登录标识用户
            token_random = hashlib.md5(str(random.random()).encode()).hexdigest()
            try:
                content = file_obj.read().decode()  # bytes to str
                User.objects.create(
                    auth_type="kubeconfig",
                    token=token_random,
                    content=content
                )
            except Exception:
                code = 1
                msg = "文件类型错误！"
            if k8s.auth_check('kubeconfig', token_random):
                request.session['is_login'] = True
                request.session['auth_type'] = "kubeconfig"
                request.session['token'] = token_random  # 标识kubeconfig登录用户
                code = 0
                msg = "登录成功"
            else:
                code = 1
                msg = "kubeconfig文件无效！"

        result = {'code': code, 'msg': msg}
        return  JsonResponse(result)

def logout(request):
    request.session.flush()
    return redirect(login)

def export_resource_api(request):
    namespace = request.GET.get("namespace")
    resource = request.GET.get("resource")
    name = request.GET.get("name")

    auth_type = request.session.get("auth_type")
    token = request.session.get("token")
    k8s.load_auth_config(auth_type, token)

    core_api = client.CoreV1Api()  # namespace,pod,service,pv,pvc
    apps_api = client.AppsV1Api()  # deployment
    networking_api = client.NetworkingV1beta1Api()  # ingress
    storage_api = client.StorageV1Api()  # storage_class

    code = 0
    msg = ""
    import yaml,json

    if resource == "namespace":
        try:
            json_str = core_api.read_namespace(name=name,
                                               _preload_content=False).read().decode()  # bytes -> str，或者 str(result,"utf-8")
            result = yaml.safe_dump(json.loads(json_str))  # json -> yaml
        except Exception as e:
            code = 1
            msg = e
    elif resource == "deployment":
        try:
            json_str = apps_api.read_namespaced_deployment(name=name, namespace=namespace,
                                                           _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "replicaset":
        try:
            json_str = apps_api.read_namespaced_replica_set(name=name, namespace=namespace,
                                                            _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "daemonset":
        try:
            json_str = apps_api.read_namespaced_daemon_set(name=name, namespace=namespace,
                                                           _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "statefulset":
        try:
            json_str = apps_api.read_namespaced_stateful_set(name=name, namespace=namespace,
                                                             _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pod":
        try:
            json_str = core_api.read_namespaced_pod(name=name, namespace=namespace,
                                                    _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "service":
        try:
            json_str = core_api.read_namespaced_service(name=name, namespace=namespace,
                                                        _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "ingress":
        try:
            json_str = networking_api.read_namespaced_ingress(name=name, namespace=namespace,
                                                              _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pvc":
        try:
            json_str = core_api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace,
                                                                        _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "pv":
        try:
            json_str = core_api.read_persistent_volume(name=name, _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "node":
        try:
            json_str = core_api.read_node(name=name, _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "configmap":
        try:
            json_str = core_api.read_namespaced_config_map(name=name, namespace=namespace,
                                                           _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    elif resource == "secret":
        try:
            json_str = core_api.read_namespaced_secret(name=name, namespace=namespace,
                                                       _preload_content=False).read().decode()
            result = yaml.safe_dump(json.loads(json_str))
        except Exception as e:
            code = 1
            msg = e
    else:
        code = 1
        msg = "未配置！"
    res = {"code": code, "msg": msg, "data": result}
    return JsonResponse(res)

from django.views.decorators.clickjacking import xframe_options_exempt
@xframe_options_exempt
def ace_editor(request):
    # 点击YAML按钮，通过URL参数传递
    namespace = request.GET.get("namespace")
    resource = request.GET.get("resource")
    name = request.GET.get("name")
    data = {}
    data['namespace'] = namespace
    data['resource'] = resource
    data['name'] = name
    return  render(request, 'ace_editor.html', {'data': data}) # 传递给在线编辑器页面 -> 拿着属性去请求导出接口