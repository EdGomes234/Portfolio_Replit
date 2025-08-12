import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from models import Notification

def save_uploaded_file(file, subfolder=''):
    """
    Salva um arquivo enviado pelo usuário
    """
    if file and file.filename:
        # Gerar nome único para o arquivo
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join('uploads', subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Retornar caminho relativo
        return os.path.join(subfolder, unique_filename)
    
    return None

def create_notification(user_id, message, project_id=None):
    """
    Cria uma notificação para um usuário
    """
    notification = Notification(
        user_id=user_id,
        message=message,
        project_id=project_id
    )
    db.session.add(notification)
    return notification

def format_date(date):
    """
    Formata uma data para exibição amigável
    """
    if not date:
        return ""
    
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 dia atrás"
        elif diff.days < 30:
            return f"{diff.days} dias atrás"
        elif diff.days < 365:
            months = diff.days // 30
            if months == 1:
                return "1 mês atrás"
            else:
                return f"{months} meses atrás"
        else:
            years = diff.days // 365
            if years == 1:
                return "1 ano atrás"
            else:
                return f"{years} anos atrás"
    
    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return "1 hora atrás"
        else:
            return f"{hours} horas atrás"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return "1 minuto atrás"
        else:
            return f"{minutes} minutos atrás"
    
    return "Agora mesmo"

def allowed_file(filename, allowed_extensions):
    """
    Verifica se um arquivo tem extensão permitida
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

