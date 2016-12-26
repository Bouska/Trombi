"""Administration panel."""

from flask import request, url_for, redirect
from wtforms import form, fields, validators
from wtforms.widgets import TextArea
from wtforms.fields import TextAreaField
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
import flask_admin as flask_admin
import flask_login as login
from werkzeug.security import check_password_hash

from models import TrombiAdmin, Person, Team, Trivia
from app import db, app


class LoginForm(form.Form):
    """Define login and registration forms (for flask-login)."""

    login = fields.StringField(u'Login', validators=[validators.required()])
    password = fields.PasswordField(
        u'Password',
        validators=[validators.required()]
    )

    def validate_login(self, field):
        """Check if the user is administrator."""
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        """Get the admin from the database."""
        return db.session.query(TrombiAdmin).filter_by(
            login=self.login.data
        ).first()


def init_login():
    """Initialize flask-login."""
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Create user loader function."""
        return db.session.query(TrombiAdmin).get(user_id)


class MyAdminIndexView(flask_admin.AdminIndexView):
    """Create customized view class that handles login & registration."""

    @expose('/')
    def index(self):
        """The root of the admin panel."""
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        """Handle user login."""
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        """Handle user logout."""
        login.logout_user()
        return redirect(url_for('.index'))


class CKEditorWidget(TextArea):
    """A custom text editor for the admin panel."""

    def __call__(self, field, **kwargs):
        """Declare the text editor."""
        if kwargs.get('class'):
            kwargs['class'] += " ckeditor"
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKEditorWidget, self).__call__(field, **kwargs)


class CKEditorField(TextAreaField):
    """A custom text editor for the admin panel."""

    widget = CKEditorWidget()

# TODO : Rename MyModelView


class MyModelView(sqla.ModelView):
    """Create customized model view class."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated
    # Change edit in the admin
    form_overrides = dict(text=CKEditorField)
    can_view_details = True
    create_template = 'edit.html'
    edit_template = 'edit.html'


def init():
    """Create the administration system."""
    # Initialize flask-login
    init_login()

    # Create admin
    admin = flask_admin.Admin(
        app,
        'Trombi admin',
        index_view=MyAdminIndexView(),
        base_template='master.html'
    )

    # Add view

    # Do we want the admin to editate this ?
    # admin.add_view(MyModelView(TrombiAdmin, db.session))

    admin.add_view(MyModelView(Person, db.session))
    admin.add_view(MyModelView(Team, db.session))
    admin.add_view(MyModelView(Trivia, db.session))
