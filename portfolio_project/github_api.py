import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GitHubAPI:
    """
    Classe para interagir com a API do GitHub
    """
    
    def __init__(self, username: str, token: Optional[str] = None):
        self.username = username
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"Portfolio-{username}"
        }
        
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    def get_user_info(self) -> Optional[Dict]:
        """
        Obtém informações do usuário do GitHub
        """
        try:
            url = f"{self.base_url}/users/{self.username}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar informações do usuário: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para API do GitHub: {e}")
            return None
    
    def get_repositories(self, per_page: int = 30) -> List[Dict]:
        """
        Obtém lista de repositórios do usuário
        """
        try:
            url = f"{self.base_url}/users/{self.username}/repos"
            params = {
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar repositórios: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para API do GitHub: {e}")
            return []
    
    def get_repository_details(self, repo_name: str) -> Optional[Dict]:
        """
        Obtém detalhes específicos de um repositório
        """
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar detalhes do repositório {repo_name}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para API do GitHub: {e}")
            return None
    
    def get_repository_languages(self, repo_name: str) -> Dict[str, int]:
        """
        Obtém as linguagens utilizadas em um repositório
        """
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}/languages"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar linguagens do repositório {repo_name}: {response.status_code}")
                return {}
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para API do GitHub: {e}")
            return {}
    
    def get_repository_readme(self, repo_name: str) -> Optional[str]:
        """
        Obtém o conteúdo do README de um repositório
        """
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}/readme"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                readme_data = response.json()
                # O conteúdo vem em base64, precisa decodificar
                import base64
                content = base64.b64decode(readme_data['content']).decode('utf-8')
                return content
            else:
                logger.warning(f"README não encontrado para o repositório {repo_name}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para API do GitHub: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao decodificar README: {e}")
            return None
    
    def get_pinned_repositories(self) -> List[str]:
        """
        Obtém lista de repositórios fixados (pinned)
        Nota: A API oficial do GitHub não expõe repositórios fixados diretamente.
        Esta função retorna uma lista hardcoded baseada na análise manual.
        """
        # Lista baseada na análise manual do perfil do usuário
        pinned_repos = [
            "Biblioteca",
            "Spectra", 
            "Site-com-bootstrap",
            "Sistema-Solar",
            "Exercicios-JS"
        ]
        return pinned_repos
    
    def get_pinned_repositories_details(self) -> List[Dict]:
        """
        Obtém detalhes dos repositórios fixados
        """
        pinned_repos = self.get_pinned_repositories()
        repositories_details = []
        
        for repo_name in pinned_repos:
            repo_details = self.get_repository_details(repo_name)
            if repo_details:
                # Adiciona informações extras
                repo_details['languages'] = self.get_repository_languages(repo_name)
                repo_details['readme'] = self.get_repository_readme(repo_name)
                repositories_details.append(repo_details)
        
        return repositories_details

def create_github_client(username: str = "EdGomes234", token: Optional[str] = None) -> GitHubAPI:
    """
    Factory function para criar uma instância do cliente GitHub
    """
    return GitHubAPI(username, token)

