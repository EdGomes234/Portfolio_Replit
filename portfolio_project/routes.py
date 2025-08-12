import os
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse
from app import app, db
from models import User, Project, Category, Tag, Comment, Like, Notification, project_tags
from forms import LoginForm, RegisterForm, ProjectForm, CommentForm, ProfileForm, CategoryForm
from utils import save_uploaded_file, create_notification, format_date
from github_api import create_github_client

# Template filter
@app.template_filter('time_ago')
def time_ago_filter(date):
    return format_date(date)

# Static file serving
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Home page / Feed
@app.route('/')
def index():
    category_filter = request.args.get('category', type=int)
    
    # Criar cliente GitHub
    github_client = create_github_client()
    
    # Obter projetos fixados do GitHub
    try:
        github_projects = github_client.get_pinned_repositories_details()
        projects = []
        
        for github_repo in github_projects:
            # Criar objeto Project temporário com dados do GitHub
            project = Project(
                title=github_repo.get('name', '').replace('-', ' ').replace('_', ' ').title(),
                description=github_repo.get('description', 'Projeto do GitHub') or f"Projeto interessante: {github_repo.get('name', '')}",
                github_link=github_repo.get('html_url', ''),
                demo_link=github_repo.get('homepage') if github_repo.get('homepage') else None,
                is_published=True,
                is_featured=True
            )
            
            # Adicionar informações extras como atributos temporários
            project.github_stars = github_repo.get('stargazers_count', 0)
            project.github_forks = github_repo.get('forks_count', 0)
            project.github_language = github_repo.get('language', 'N/A')
            project.github_updated = github_repo.get('updated_at', '')
            
            projects.append(project)
            
    except Exception as e:
        app.logger.error(f"Erro ao buscar projetos do GitHub: {e}")
        # Fallback para projetos estáticos em caso de erro
        pinned_project_names = ["Biblioteca", "Spectra", "Site-com-bootstrap", "Sistema-Solar", "Exercicios-JS"]
        projects = []
        for name in pinned_project_names:
            project = Project(
                title=name.replace("-", " ").replace("_", " ").title(),
                description=f"Um projeto interessante do GitHub: {name}",
                github_link=f"https://github.com/EdGomes234/{name}",
                is_published=True,
                is_featured=True
            )
            projects.append(project)
    
    # Get categories for filter (still needed for other parts of the site, if any)
    categories = Category.query.all()
    
    # Featured projects will be the pinned projects for now
    featured_projects = projects
    
    return render_template('index.html', projects=projects, categories=categories, 
                         featured_projects=featured_projects, current_category=category_filter)

# Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page)
        flash('Email ou senha incorretos.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

# Profile
@app.route('/profile')
@login_required
def profile():
    user_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('profile.html', user_projects=user_projects)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        current_user.profession = form.profession.data
        current_user.location = form.location.data
        current_user.linkedin_url = form.linkedin_url.data
        current_user.github_url = form.github_url.data
        current_user.website_url = form.website_url.data
        
        if form.profile_image.data:
            image_path = save_uploaded_file(form.profile_image.data, 'profiles')
            if image_path:
                current_user.profile_image = image_path
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate form
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.bio.data = current_user.bio
        form.profession.data = getattr(current_user, 'profession', None)
        form.location.data = getattr(current_user, 'location', None)
        form.linkedin_url.data = getattr(current_user, 'linkedin_url', None)
        form.github_url.data = getattr(current_user, 'github_url', None)
        form.website_url.data = getattr(current_user, 'website_url', None)
    
    return render_template('profile.html', form=form, edit_mode=True)

# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem acessar esta área.', 'error')
        return redirect(url_for('index'))
    
    user_projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    categories = Category.query.all()
    
    # Statistics
    total_projects = len(user_projects)
    published_projects = len([p for p in user_projects if p.is_published])
    total_likes = sum(p.get_like_count() for p in user_projects)
    total_comments = sum(len(p.comments) for p in user_projects)
    
    stats = {
        'total_projects': total_projects,
        'published_projects': published_projects,
        'total_likes': total_likes,
        'total_comments': total_comments
    }
    
    return render_template('admin_dashboard.html', projects=user_projects, 
                         categories=categories, stats=stats)

# Project CRUD
@app.route('/admin/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem criar projetos.', 'error')
        return redirect(url_for('index'))
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            demo_link=form.demo_link.data,
            github_link=form.github_link.data,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            user_id=current_user.id
        )
        
        # Handle category
        if form.category_id.data and form.category_id.data > 0:
            project.category_id = form.category_id.data
        
        # Handle file uploads
        if form.image.data:
            image_path = save_uploaded_file(form.image.data, 'projects')
            if image_path:
                project.image_path = image_path
        
        if form.video.data:
            video_path = save_uploaded_file(form.video.data, 'projects')
            if video_path:
                project.video_path = video_path
        
        db.session.add(project)
        db.session.flush()  # Get project ID
        
        # Handle tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                project.tags.append(tag)
        
        db.session.commit()
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_project_form.html', form=form, title='Novo Projeto')

@app.route('/admin/project/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem editar projetos.', 'error')
        return redirect(url_for('index'))
    project = Project.query.get_or_404(id)
    
    # Check if user owns this project
    if project.user_id != current_user.id:
        flash('Você não tem permissão para editar este projeto.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.content = form.content.data
        project.demo_link = form.demo_link.data
        project.github_link = form.github_link.data
        project.is_published = form.is_published.data
        project.is_featured = form.is_featured.data
        
        # Handle category
        if form.category_id.data and form.category_id.data > 0:
            project.category_id = form.category_id.data
        else:
            project.category_id = None
        
        # Handle file uploads
        if form.image.data:
            image_path = save_uploaded_file(form.image.data, 'projects')
            if image_path:
                project.image_path = image_path
        
        if form.video.data:
            video_path = save_uploaded_file(form.video.data, 'projects')
            if video_path:
                project.video_path = video_path
        
        # Handle tags
        project.tags.clear()
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                project.tags.append(tag)
        
        db.session.commit()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Pre-populate tags field
    if request.method == 'GET':
        form.tags.data = ', '.join([tag.name for tag in project.tags])
    
    return render_template('admin_project_form.html', form=form, project=project, 
                         title='Editar Projeto')

@app.route('/admin/project/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem excluir projetos.', 'error')
        return redirect(url_for('index'))
    project = Project.query.get_or_404(id)
    
    # Check if user owns this project
    if project.user_id != current_user.id:
        flash('Você não tem permissão para excluir este projeto.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Delete associated files
    if project.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], project.image_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project.image_path))
    
    if project.video_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], project.video_path)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project.video_path))
    
    db.session.delete(project)
    db.session.commit()
    flash('Projeto excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))

# Project Detail
@app.route('/project/<int:id>')
def project_detail(id):
    # Criar cliente GitHub
    github_client = create_github_client()
    
    try:
        # Obter projetos fixados do GitHub
        github_projects = github_client.get_pinned_repositories_details()
        
        # Verificar se o ID está dentro do range válido
        if id < 1 or id > len(github_projects):
            flash('Projeto não encontrado.', 'error')
            return redirect(url_for('index'))
        
        # Obter o projeto específico (ID é 1-based)
        github_repo = github_projects[id - 1]
        
        # Criar objeto Project temporário com dados do GitHub
        project = Project(
            id=id,  # ID temporário
            title=github_repo.get('name', '').replace('-', ' ').replace('_', ' ').title(),
            description=github_repo.get('description', 'Projeto do GitHub') or f"Projeto interessante: {github_repo.get('name', '')}",
            content=github_repo.get('readme', '')[:500] + '...' if github_repo.get('readme') else None,
            github_link=github_repo.get('html_url', ''),
            demo_link=github_repo.get('homepage') if github_repo.get('homepage') else None,
            is_published=True,
            is_featured=True,
            user_id=1,  # ID do usuário Edgar
            created_at=datetime.strptime(github_repo.get('created_at', ''), '%Y-%m-%dT%H:%M:%SZ') if github_repo.get('created_at') else datetime.utcnow()
        )
        
        # Adicionar informações extras como atributos temporários
        project.github_stars = github_repo.get('stargazers_count', 0)
        project.github_forks = github_repo.get('forks_count', 0)
        project.github_language = github_repo.get('language', 'N/A')
        project.github_updated = github_repo.get('updated_at', '')
        
        # Simular comentários e curtidas (em uma implementação real, estes viriam do banco)
        project.comments = []
        project.likes = []
        
        # Adicionar métodos necessários
        def get_like_count():
            return len(project.likes)
        
        def is_liked_by_user(user_id):
            return False  # Por enquanto, sempre False
        
        project.get_like_count = get_like_count
        project.is_liked_by_user = is_liked_by_user
        
    except Exception as e:
        app.logger.error(f"Erro ao buscar projeto do GitHub: {e}")
        flash('Projeto não encontrado.', 'error')
        return redirect(url_for('index'))
    
    comment_form = CommentForm()
    
    return render_template('project_detail.html', project=project, comment_form=comment_form)

# Comments
@app.route('/project/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    project = Project.query.get_or_404(id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            project_id=project.id
        )
        db.session.add(comment)
        
        # Create notification for project owner
        if project.user_id != current_user.id:
            message = f"{current_user.get_full_name()} comentou no seu projeto '{project.title}'"
            create_notification(project.user_id, message, project.id)
        
        db.session.commit()
        flash('Comentário adicionado com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {field}: {error}', 'error')
    
    return redirect(url_for('project_detail', id=id))

# Likes (AJAX)
@app.route('/project/<int:id>/like', methods=['POST'])
@login_required
def toggle_like(id):
    project = Project.query.get_or_404(id)
    
    # Check if user already liked this project
    existing_like = Like.query.filter_by(user_id=current_user.id, project_id=project.id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        liked = False
    else:
        # Like
        like = Like(user_id=current_user.id, project_id=project.id)
        db.session.add(like)
        liked = True
        
        # Create notification for project owner
        if project.user_id != current_user.id:
            message = f"{current_user.get_full_name()} curtiu seu projeto '{project.title}'"
            create_notification(project.user_id, message, project.id)
    
    db.session.commit()
    
    return jsonify({
        'liked': liked,
        'like_count': project.get_like_count()
    })

# Categories
@app.route('/admin/categories')
@login_required
def manage_categories():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem gerenciar categorias.', 'error')
        return redirect(url_for('index'))
    categories = Category.query.all()
    return render_template('admin_categories.html', categories=categories)

@app.route('/admin/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem criar categorias.', 'error')
        return redirect(url_for('index'))
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, color=form.color.data)
        db.session.add(category)
        db.session.commit()
        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('manage_categories'))
    return render_template('admin_category_form.html', form=form, title='Nova Categoria')

@app.route('/admin/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem editar categorias.', 'error')
        return redirect(url_for('index'))
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.color = form.color.data
        db.session.commit()
        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('manage_categories'))
    
    return render_template('admin_category_form.html', form=form, category=category, title='Editar Categoria')

@app.route('/admin/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    if not current_user.is_admin:
        flash('Acesso negado. Apenas administradores podem excluir categorias.', 'error')
        return redirect(url_for('index'))
    category = Category.query.get_or_404(id)
    
    # Check if category has projects
    if category.projects:
        flash('Não é possível excluir uma categoria que possui projetos.', 'error')
        return redirect(url_for('manage_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('manage_categories'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# User public profile
@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_projects = Project.query.filter_by(user_id=user.id, is_published=True).order_by(Project.created_at.desc()).all()
    return render_template('user_profile.html', user=user, user_projects=user_projects)

# Search functionality
@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('index'))
    
    # Search in projects
    projects = Project.query.filter(
        Project.is_published == True,
        db.or_(
            Project.title.contains(query),
            Project.description.contains(query),
            Project.content.contains(query)
        )
    ).order_by(Project.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('search_results.html', projects=projects, query=query)
