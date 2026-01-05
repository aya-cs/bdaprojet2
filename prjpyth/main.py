"""
Application principale Streamlit - Plateforme d'Optimisation des Examens
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import AuthenticationSystem
from student import render_student_dashboard
from professor import render_professor_dashboard
from department_head import render_department_head_dashboard

# Configuration de la page
st.set_page_config(
    page_title="🎓 Plateforme Examens Universitaires",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
    <style>
    /* Styles globaux */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0 0 10px 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Cartes */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Boutons */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Tableaux */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

def main():
    """
    Fonction principale de l'application
    """
    # Initialiser le système d'authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Vérifier le timeout de session
    if st.session_state.authenticated:
        if AuthenticationSystem.check_session_timeout():
            st.warning("Session expirée. Veuillez vous reconnecter.")
            AuthenticationSystem.logout()
            st.rerun()
        else:
            AuthenticationSystem.update_activity()
    
    # Afficher l'interface appropriée
    if not st.session_state.authenticated:
        show_login_interface()
    else:
        show_main_interface()

def show_login_interface():
    """
    Affiche l'interface de connexion
    """
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🎓 Plateforme d'Optimisation des Emplois du Temps d'Examens</h1>
            <p>Université • Faculté des Sciences • Gestion intelligente des examens</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Contenu principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        AuthenticationSystem.render_login_form()
    
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 3rem; padding: 2rem; color: #6c757d;">
            <p>📊 <strong>13,000+ étudiants</strong> • 🏛️ <strong>7 départements</strong> • 📚 <strong>200+ formations</strong></p>
            <p>⚡ <strong>Optimisation automatique en &lt;45 secondes</strong></p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">© 2025 Plateforme Examens Universitaires • Tous droits réservés</p>
        </div>
    """, unsafe_allow_html=True)

def show_main_interface():
    """
    Affiche l'interface principale après connexion
    """
    user = st.session_state.user
    
    # Sidebar avec informations utilisateur
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 1rem;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
                    <h3>👋 Bienvenue</h3>
                    <p><strong>{user.get('display_name', user['username'])}</strong></p>
                    <p><small>{user['role'].replace('_', ' ').title()}</small></p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Menu de navigation
        st.markdown("### 📋 Navigation")
        
        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True):
            AuthenticationSystem.logout()
            st.rerun()
        
        # Informations système
        st.markdown("---")
        st.markdown("### ℹ️ Informations")
        
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.caption(f"Dernière activité: {current_time}")
        
        # Statistiques rapides (selon le rôle)
        if user['role'] == 'etudiant':
            st.metric("📅 Examens à venir", user.get('examens_a_venir', 0))
            st.metric("📚 Modules inscrits", user.get('modules_inscrits', 0))
        elif user['role'] == 'professeur':
            st.metric("👁️ Surveillances", user.get('examens_a_surveiller', 0))
            st.metric("📖 Modules responsables", user.get('modules_responsables', 0))
        elif user['role'] == 'chef_departement':
            st.metric("🏛️ Formations", user.get('nb_formations', 0))
            st.metric("👨‍🎓 Étudiants", user.get('nb_etudiants', 0))
    
    # Header principal
    col1, col2 = st.columns([4, 1])
    
    with col1:
        role_titles = {
            'etudiant': 'Étudiant',
            'professeur': 'Professeur',
            'chef_departement': 'Chef de Département',
            'admin_examens': 'Administrateur Examens',
            'vice_doyen': 'Vice-Doyen'
        }
        
        st.title(f"🎓 Tableau de bord - {role_titles.get(user['role'], user['role'])}")
    
    with col2:
        st.metric("🕒 Heure système", datetime.now().strftime("%H:%M"))
    
    st.markdown("---")
    
    # Afficher le dashboard selon le rôle
    try:
        if user['role'] == 'etudiant':
            render_student_dashboard()
        elif user['role'] == 'professeur':
            render_professor_dashboard()
        elif user['role'] == 'chef_departement':
            render_department_head_dashboard()
        elif user['role'] == 'admin_examens':
            st.warning("Interface administrateur en cours de développement")
            st.info("Vous avez accès à toutes les fonctionnalités d'administration")
        elif user['role'] == 'vice_doyen':
            st.warning("Interface vice-doyen en cours de développement")
            st.info("Vue stratégique globale avec tous les KPIs académiques")
        else:
            st.error("Rôle non reconnu. Veuillez contacter l'administrateur.")
    
    except Exception as e:
        st.error(f"Une erreur est survenue: {str(e)}")
        st.info("Veuillez rafraîchir la page ou contacter le support technique")
    
    # Footer
    st.markdown("""
        <div style="text-align: center; margin-top: 3rem; padding: 2rem; color: #6c757d; border-top: 1px solid #dee2e6;">
            <p><strong>Plateforme d'Optimisation des Examens Universitaires</strong></p>
            <p>📞 Support technique: support@univ.dz • 🕒 Disponible 24/7 pendant les périodes d'examens</p>
            <p style="font-size: 0.9rem;">v2.0 • Optimisé pour 130,000+ inscriptions • Génération de planning en &lt;45s</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()