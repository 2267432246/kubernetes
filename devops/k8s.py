from kubernetes import client,config
import os, yaml
from dashboard.models import User
from django.shortcuts import redirect
from datetime import date, timedelta


api_server = "https://10.10.101.126:6443"

def auth_check(auth_type, token):
    if auth_type == "token":
        configuration = client.Configuration()
        configuration.host = api_server  # APISERVER地址
        # ca_file = os.path.join(os.getcwd(),"ca.crt") # K8s集群CA证书（/etc/kubernetes/pki/ca.crt）
        # configuration.ssl_ca_cert= ca_file
        configuration.verify_ssl = False  # 启用证书验证
        configuration.api_key = {"authorization": "Bearer " + token}
        client.Configuration.set_default(configuration)
        try:
            core_api = client.CoreApi()
            core_api.get_api_versions()
            return True
        except Exception as e:
            return False
    elif auth_type == "kubeconfig":
        try:
            user = User.objects.filter(token=token)
            content = user[0].content
            yaml_content = yaml.load(content, Loader=yaml.FullLoader)
            config.load_kube_config_from_dict(yaml_content)
            core_api = client.CoreApi()
            core_api.get_api_versions()
            return True
        except Exception as e:
            return False

# 登录认证装饰器
def self_login_required(func):
    def inner(request, *args, **kwargs):
        is_login = request.session.get('is_login', False)
        if is_login:
            return func(request, *args, **kwargs)
        else:
            return redirect("/login")
    return inner

# 加载认证配置
def load_auth_config(auth_type, token):
    if auth_type == "token":
        configuration = client.Configuration()
        configuration.host = api_server
        configuration.verify_ssl = False  # 启用证书验证
        configuration.api_key = {"authorization": "Bearer " + token}
        client.Configuration.set_default(configuration)
    elif auth_type == "kubeconfig":
        user = User.objects.filter(token=token)
        content = user[0].content
        yaml_content = yaml.load(content, Loader=yaml.FullLoader)
        config.load_kube_config_from_dict(yaml_content)

# 时间格式化
def dt_format(dt):
    current_datetime = dt + timedelta(hours=8)
    dt = date.strftime(current_datetime, '%Y-%m-%d %H:%M:%S')
    return dt