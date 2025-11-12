
from flask import redirect, render_template, session
from functools import wraps


def apology(message):
    return render_template('apology.html',error=message)
#验证是否为管理员
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is not 1:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
#验证是否登录
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
