import os
import re

backend_dir = r"c:\Users\Parthiv Vanapalli\Desktop\site-security-analyzer\backend"

def patch_backend():
    app_py_path = os.path.join(backend_dir, "app.py")
    celery_tasks_path = os.path.join(backend_dir, "celery_tasks.py")
    
    # 1. Patch app.py
    with open(app_py_path, 'r', encoding='utf-8') as f:
        app_content = f.read()
        
    # Replace utcnow
    app_content = app_content.replace("datetime.datetime.utcnow()", "datetime.datetime.now(datetime.timezone.utc)")
    app_content = app_content.replace("default=datetime.datetime.utcnow", "default=lambda: datetime.datetime.now(datetime.timezone.utc)")
    
    # Patch IPv6 SSRF check
    old_check = """                # Block private, loopback, link-local, multicast, reserved
                if (ip_obj.is_private or ip_obj.is_loopback or 
                    ip_obj.is_link_local or ip_obj.is_multicast or 
                    ip_obj.is_reserved):
                    return False, url, f"Access to private/internal addresses not allowed ({ip_str})\""""
    
    new_check = """                # Allow IPv6 NAT64 prefix (64:ff9b::/96) which is considered reserved by ipaddress but is public
                is_nat64 = isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj in ipaddress.IPv6Network('64:ff9b::/96')
                
                # Block private, loopback, link-local, multicast, reserved
                if not is_nat64 and (ip_obj.is_private or ip_obj.is_loopback or 
                    ip_obj.is_link_local or ip_obj.is_multicast or 
                    ip_obj.is_reserved):
                    return False, url, f"Access to private/internal addresses not allowed ({ip_str})\""""
    app_content = app_content.replace(old_check, new_check)
    
    with open(app_py_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
        
    # 2. Patch celery_tasks.py
    with open(celery_tasks_path, 'r', encoding='utf-8') as f:
        celery_content = f.read()
        
    celery_content = celery_content.replace("datetime.datetime.utcnow()", "datetime.datetime.now(datetime.timezone.utc)")
    celery_content = celery_content.replace("_dt.datetime.utcnow()", "_dt.datetime.now(_dt.timezone.utc)")
    
    with open(celery_tasks_path, 'w', encoding='utf-8') as f:
        f.write(celery_content)
        
    print("Backend patched successfully")

if __name__ == "__main__":
    patch_backend()
