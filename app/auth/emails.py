from flask import url_for, render_template

def render_confirm_email(user, token):
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    return render_template("auth/email_confirm.html", user=user, confirm_url=confirm_url)

def render_reset_email(user, token):
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    return render_template("auth/email_reset.html", user=user, reset_url=reset_url)
