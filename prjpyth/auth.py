"""
Système d'authentification moderne avec session management
"""
import streamlit as st
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from queries import UserQueries

logger = logging.getLogger(__name__)

class AuthenticationSystem:
    """Gestion complète de l'authentification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash le mot de passe (simplifié - en production utiliser bcrypt)"""
        # Note: En production, utiliser bcrypt avec sel
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(username: str, password: str):
        try:
            # استعلام مباشر
            query = """
                SELECT u.id, u.username, u.role, u.linked_id, u.email,
                       CASE u.role
                           WHEN 'etudiant' THEN 'Étudiant Test'
                           WHEN 'professeur' THEN 'Professeur Test'
                           ELSE u.username
                       END as display_name
                FROM users u
                WHERE u.username = %s 
                    AND u.is_active = TRUE
            """
            
            from connection import execute_query
            result = execute_query(query, (username,))
            
            if result:
                user = result[0]
                
                # في التطوير، اقبل أي كلمة مرور
                if password:
                    return {
                        'username': user['username'],
                        'role': user['role'],
                        'linked_id': user['linked_id'],
                        'display_name': user['display_name']
                    }
            
            return None
        except:
            return None
    
    @staticmethod
    def initialize_session(user_data: Dict[str, Any]):
        """
        Initialise la session utilisateur
        """
        st.session_state.update({
            'authenticated': True,
            'user': user_data,
            'login_time': datetime.now(),
            'last_activity': datetime.now()
        })
        
        # Stocker des informations spécifiques au rôle
        role = user_data['role']
        st.session_state[f'{role}_id'] = user_data['linked_id']
        st.session_state[f'{role}_name'] = user_data.get('display_name', user_data['username'])
    
    @staticmethod
    def logout():
        """
        Déconnexion de l'utilisateur
        """
        username = st.session_state.get('user', {}).get('username', 'Inconnu')
        logger.info(f"Déconnexion de l'utilisateur: {username}")
        
        # Nettoyer la session
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    @staticmethod
    def check_session_timeout(timeout_minutes: int = 60) -> bool:
        """
        Vérifie si la session a expiré
        """
        if 'last_activity' not in st.session_state:
            return True
            
        last_activity = st.session_state['last_activity']
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity)
        
        timeout_delta = timedelta(minutes=timeout_minutes)
        return datetime.now() - last_activity > timeout_delta
    
    @staticmethod
    def update_activity():
        """
        Met à jour le timestamp de dernière activité
        """
        if 'authenticated' in st.session_state and st.session_state['authenticated']:
            st.session_state['last_activity'] = datetime.now()
    
    @staticmethod
    def render_login_form():
        """
        Affiche le formulaire de connexion
        """
        st.markdown("""
            <style>
            .login-container {
                max-width: 400px;
                margin: 0 auto;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .login-title {
                text-align: center;
                color: white;
                margin-bottom: 2rem;
                font-size: 1.8rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<h2 class="login-title">🔐 Connexion Plateforme Examens</h2>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Nom d'utilisateur", 
                                        placeholder="Entrez votre nom d'utilisateur")
                password = st.text_input("🔒 Mot de passe", 
                                        type="password",
                                        placeholder="Entrez votre mot de passe")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submit = st.form_submit_button("Se connecter", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Veuillez remplir tous les champs")
                    else:
                        with st.spinner("Authentification en cours..."):
                            user = AuthenticationSystem.authenticate(username, password)
                            if user:
                                AuthenticationSystem.initialize_session(user)
                                st.success(f"Bienvenue {user.get('display_name', username)}!")
                                st.rerun()
                            else:
                                st.error("Nom d'utilisateur ou mot de passe incorrect")
            
            st.markdown("""
                <div style="text-align: center; margin-top: 1rem; color: white; font-size: 0.9rem;">
                    <p>Plateforme d'Optimisation des Emplois du Temps d'Examens</p>
                    <p>Université - Faculté des Sciences</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)