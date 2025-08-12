from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, URL, Regexp
from models import User, Category

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Nome de usuário', validators=[
        DataRequired(), 
        Length(min=3, max=20),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Nome de usuário deve conter apenas letras, números e underscore.')
    ])
    first_name = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Sobrenome', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar senha', 
                             validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Cadastrar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Nome de usuário já existe. Escolha outro.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email já cadastrado. Use outro email.')

class ProjectForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Descrição', validators=[DataRequired(), Length(max=1000)])
    content = TextAreaField('Conteúdo detalhado', validators=[Optional(), Length(max=5000)])
    category_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    tags = StringField('Tags (separadas por vírgula)', validators=[Optional(), Length(max=200)])
    demo_link = StringField('Link de demonstração', validators=[Optional(), URL()])
    github_link = StringField('Link do GitHub', validators=[Optional(), URL()])
    image = FileField('Imagem', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas.')])
    video = FileField('Vídeo', validators=[FileAllowed(['mp4', 'webm', 'ogg'], 'Apenas vídeos MP4, WebM ou OGG são permitidos.')])
    is_published = BooleanField('Publicar')
    is_featured = BooleanField('Destacar na página inicial')
    submit = SubmitField('Salvar')
    
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(0, 'Selecione uma categoria')] + \
                                  [(c.id, c.name) for c in Category.query.all()]

class CommentForm(FlaskForm):
    content = TextAreaField('Comentário', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Comentar')

class ProfileForm(FlaskForm):
    first_name = StringField('Nome', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Sobrenome', validators=[DataRequired(), Length(max=50)])
    bio = TextAreaField('Biografia', validators=[Optional(), Length(max=1000)])
    profession = StringField('Profissão', validators=[Optional(), Length(max=100)])
    location = StringField('Localização', validators=[Optional(), Length(max=100)])
    linkedin_url = StringField('LinkedIn URL', validators=[Optional(), URL()])
    github_url = StringField('GitHub URL', validators=[Optional(), URL()])
    website_url = StringField('Website URL', validators=[Optional(), URL()])
    profile_image = FileField('Foto de perfil', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG, JPEG ou PNG são permitidas.')])
    submit = SubmitField('Atualizar perfil')

class CategoryForm(FlaskForm):
    name = StringField('Nome da categoria', validators=[DataRequired(), Length(min=1, max=50)])
    color = StringField('Cor (hex)', validators=[
        DataRequired(), 
        Length(min=7, max=7),
        Regexp(r'^#[0-9A-Fa-f]{6}$', message='Cor deve estar no formato hexadecimal (#RRGGBB).')
    ])
    submit = SubmitField('Salvar')
    
    def validate_name(self, name):
        # Check if name already exists (but allow current category name)
        existing = Category.query.filter_by(name=name.data).first()
        if existing and (not hasattr(self, '_obj') or existing.id != self._obj.id):
            raise ValidationError('Uma categoria com este nome já existe.')

class SearchForm(FlaskForm):
    q = StringField('Buscar', validators=[DataRequired(), Length(min=1, max=100)])
    submit = SubmitField('Buscar')
