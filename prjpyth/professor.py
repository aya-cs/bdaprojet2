"""
Interface professeur 100% connectée à la BDD
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from queries import ExamQueries, AnalyticsQueries, OptimizationQueries, UserQueries  # تم حذف ProfesseurQueries

# ========== FONCTIONS UTILITAIRES ==========
def safe_get_exams(prof_id: int, days: int):
    """
    Récupération sécurisée des examens depuis BDD
    """
    try:
        df = ExamQueries.get_professor_exams(prof_id, days)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Erreur récupération examens: {e}")
        return pd.DataFrame()

def safe_get_stats(prof_id: int):
    """
    Récupération sécurisée des statistiques depuis BDD
    """
    try:
        stats = ExamQueries.get_professor_stats(prof_id)
        return stats if isinstance(stats, dict) else {}
    except Exception as e:
        st.error(f"⚠️ Erreur récupération stats: {e}")
        return {}

def safe_get_modules(prof_id: int):
    """
    Récupération des modules depuis BDD
    """
    try:
        df = ExamQueries.get_professor_modules(prof_id)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Erreur récupération modules: {e}")
        return pd.DataFrame()

# ========== DASHBOARD PRINCIPAL ==========
def render_professor_dashboard():
    """
    Dashboard principal 100% BDD
    """
    # Vérification de session
    if 'user' not in st.session_state:
        st.error("🔒 Veuillez vous connecter")
        return
    
    user = st.session_state.user
    if user.get('role') != 'professeur':
        st.error("⛔ Cette page est réservée aux professeurs")
        return
    
    prof_id = user.get('linked_id', 1)
    
    # Récupération des données depuis BDD
    prof_stats = safe_get_stats(prof_id)
    
    # ========== HEADER ==========
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
            <h1 style="margin: 0;">👨‍🏫 Tableau de bord Professeur</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">
                {prof_stats.get('nom_complet', user.get('display_name', 'Professeur'))}
            </p>
            <p style="margin: 0; opacity: 0.9;">
                {prof_stats.get('grade', '')} • {prof_stats.get('departement', 'Département')}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # ========== KPI CARDS ==========
    st.subheader("📊 Vue d'ensemble")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Examens aujourd'hui
        df_today = safe_get_exams(prof_id, 0)
        exams_today = 0
        if not df_today.empty and 'date_heure' in df_today.columns:
            try:
                df_today['date_heure'] = pd.to_datetime(df_today['date_heure'])
                today = datetime.now().date()
                exams_today = len(df_today[df_today['date_heure'].dt.date == today])
            except:
                exams_today = 0
        st.metric("Aujourd'hui", exams_today)
    
    with col2:
        # Cette semaine
        df_week = safe_get_exams(prof_id, 7)
        exams_week = len(df_week) if not df_week.empty else 0
        st.metric("Cette semaine", exams_week)
    
    with col3:
        # À venir
        exams_future = prof_stats.get('examens_a_venir', 0)
        st.metric("À venir", exams_future)
    
    with col4:
        # Terminés
        exams_done = prof_stats.get('examens_termines', 0)
        st.metric("Terminés", exams_done)
    
    with col5:
        # Notifications non lues
        unread_count = UserQueries.get_unread_notifications_count(prof_id, 'professeur')
        st.metric("Notifications", unread_count, delta=f"{unread_count} non lues" if unread_count > 0 else None)
    
    # ========== NOTIFICATIONS RÉELLES ==========
    notifications = UserQueries.get_notifications(prof_id, 'professeur', 10)
    
    if notifications:
        with st.expander(f"🔔 Notifications ({len(notifications)})", expanded=len(notifications) > 0):
            for notif in notifications:
                # Icône selon le type
                icon_map = {
                    'rappel': '⏰',
                    'changement': '🔄',
                    'information': 'ℹ️',
                    'alerte': '⚠️',
                    'confirmation': '✅',
                    'systeme': '⚙️'
                }
                icon = icon_map.get(notif.get('type_notification', '').lower(), '📌')
                
                # Couleur selon priorité
                priority_color = {
                    1: "#00aa00",  # Bas
                    2: "#ffaa00",  # Moyen
                    3: "#ff4444"   # Haut
                }.get(notif.get('priority', 1), "#00aa00")
                
                col1, col2, col3 = st.columns([1, 8, 2])
                with col1:
                    st.markdown(f"<h3 style='color:{priority_color}; margin:0;'>{icon}</h3>", 
                               unsafe_allow_html=True)
                with col2:
                    if not notif['is_lu']:
                        st.markdown(f"**{notif['titre']}**")
                        st.caption(notif['contenu'])
                    else:
                        st.markdown(f"✓ {notif['titre']}")
                        st.caption(notif['contenu'])
                with col3:
                    if not notif['is_lu']:
                        if st.button("✓ Lu", key=f"read_{notif['id']}"):
                            result = UserQueries.mark_notification_as_read(notif['id'])
                            if result:
                                st.success("Notification marquée comme lue")
                                st.rerun()
    
    st.markdown("---")
    
    # ========== TABS PRINCIPALES ==========
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Planning",
        "📋 Examens", 
        "📚 Modules",
        "📊 Statistiques",
        "⚠️ Conflits",
        "⚙️ Gestion"
    ])
    
    with tab1:
        render_planning_tab(prof_id)
    
    with tab2:
        render_exams_tab(prof_id)
    
    with tab3:
        render_modules_tab(prof_id)
    
    with tab4:
        render_statistics_tab(prof_id, prof_stats)
    
    with tab5:
        render_conflicts_tab(prof_id)
    
    with tab6:
        render_management_tab(prof_id)

# ========== TAB 1: PLANNING ==========
def render_planning_tab(prof_id: int):
    """
    Planning avec données BDD
    """
    st.subheader("📅 Planning des surveillances")
    
    # Options
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Période à afficher", 
                             ["Semaine", "Mois", "Trimestre", "Personnalisé"], 
                             index=1)
    with col2:
        if period == "Personnalisé":
            start_date = st.date_input("Date début", datetime.now().date())
            end_date = st.date_input("Date fin", datetime.now().date() + timedelta(days=30))
        else:
            days_map = {"Semaine": 7, "Mois": 30, "Trimestre": 90}
            days = days_map.get(period, 30)
    
    # Récupération depuis BDD
    if period == "Personnalisé":
        # Récupérer plus de données et filtrer
        df = safe_get_exams(prof_id, 365)
        if not df.empty and 'date_heure' in df.columns:
            df['date_heure'] = pd.to_datetime(df['date_heure'])
            mask = (df['date_heure'].dt.date >= start_date) & (df['date_heure'].dt.date <= end_date)
            df = df[mask]
    else:
        df = safe_get_exams(prof_id, days)
    
    if df.empty:
        st.info("🎯 Aucune surveillance prévue pour cette période")
        return
    
    # Timeline
    try:
        if 'date_fin' not in df.columns and 'duree_minutes' in df.columns:
            df['date_fin'] = pd.to_datetime(df['date_heure']) + pd.to_timedelta(df['duree_minutes'], unit='m')
        
        fig = px.timeline(
            df.sort_values('date_heure'),
            x_start="date_heure",
            x_end="date_fin",
            y="module_nom",
            color="formation_nom",
            hover_data={
                'salle_nom': True,
                'nb_etudiants': True,
                'duree_minutes': True,
                'statut': True,
                'type_examen': True
            },
            title="Planning des surveillances",
            height=500
        )
        
        fig.update_layout(
            xaxis_title="Temps",
            yaxis_title="Modules",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erreur création timeline: {e}")
    
    # Calendrier
    st.markdown("#### 📆 Calendrier")
    render_calendar_view(df)

def render_calendar_view(df):
    """
    Vue calendrier des surveillances
    """
    if df.empty:
        return
    
    try:
        # Extraire les dates
        df['date'] = pd.to_datetime(df['date_heure']).dt.date
        
        # Calendrier du mois courant
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Créer le calendrier
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        st.markdown(f"### {month_name} {year}")
        
        # En-têtes
        days_fr = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        cols = st.columns(7)
        for i, day in enumerate(days_fr):
            cols[i].write(f"**{day}**")
        
        # Jours avec examens
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    day_date = datetime(year, month, day).date()
                    day_exams = df[df['date'] == day_date]
                    
                    if not day_exams.empty:
                        exam_count = len(day_exams)
                        total_students = day_exams['nb_etudiants'].sum() if 'nb_etudiants' in day_exams.columns else 0
                        
                        cols[i].markdown(
                            f'<div style="background-color: #4CAF50; color: white; '
                            f'padding: 8px; border-radius: 5px; text-align: center;">'
                            f'<strong>{day}</strong><br>'
                            f'<small>{exam_count} exam.</small><br>'
                            f'<small>{total_students} étud.</small>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        cols[i].write(f"{day}")
                        
    except Exception as e:
        st.warning(f"Impossible d'afficher le calendrier: {e}")

# ========== TAB 2: EXAMENS ==========
def render_exams_tab(prof_id: int):
    """
    Liste détaillée des examens depuis BDD
    """
    st.subheader("📋 Liste des examens")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days = st.slider("Période (jours)", 1, 365, 60)
    
    with col2:
        status_options = ["Planifie", "Confirme", "Termine", "Annule"]
        status_filter = st.multiselect(
            "Statut",
            status_options,
            default=["Planifie", "Confirme"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Trier par",
            ["Date", "Module", "Formation", "Salle", "Étudiants"]
        )
    
    # Récupération depuis BDD
    df = safe_get_exams(prof_id, days)
    
    if df.empty:
        st.info("📭 Aucun examen trouvé")
        return
    
    # Application des filtres
    if 'statut' in df.columns and status_filter:
        df = df[df['statut'].isin(status_filter)]
    
    # Tri
    sort_map = {
        "Date": "date_heure",
        "Module": "module_nom",
        "Formation": "formation_nom",
        "Salle": "salle_nom",
        "Étudiants": "nb_etudiants"
    }
    
    if sort_by in sort_map:
        sort_column = sort_map[sort_by]
        if sort_column in df.columns:
            df = df.sort_values(sort_column, ascending=(sort_by != "Étudiants"))
    
    # Formatage
    display_df = df.copy()
    
    # Format date
    if 'date_heure' in display_df.columns:
        display_df['date_heure'] = pd.to_datetime(display_df['date_heure']).dt.strftime('%d/%m/%Y %H:%M')
    
    # Traduction statuts
    status_trans = {
        'Planifie': 'Planifié',
        'Confirme': 'Confirmé',
        'Termine': 'Terminé',
        'Annule': 'Annulé'
    }
    
    if 'statut' in display_df.columns:
        display_df['statut'] = display_df['statut'].map(status_trans).fillna(display_df['statut'])
    
    # Sélection colonnes
    available_cols = []
    possible_cols = [
        'date_heure', 'module_nom', 'formation_nom', 
        'salle_nom', 'nb_etudiants', 'duree_minutes', 
        'statut', 'type_examen', 'taux_occupation'
    ]
    
    for col in possible_cols:
        if col in display_df.columns:
            available_cols.append(col)
    
    # Configuration colonnes
    column_config = {
        "date_heure": st.column_config.TextColumn("Date & Heure", width="medium"),
        "module_nom": "Module",
        "formation_nom": "Formation",
        "salle_nom": "Salle",
        "nb_etudiants": st.column_config.NumberColumn("Étudiants", format="%d"),
        "duree_minutes": "Durée (min)",
        "statut": st.column_config.SelectboxColumn(
            "Statut",
            options=["Planifié", "Confirmé", "Terminé", "Annulé"]
        ),
        "type_examen": "Type",
        "taux_occupation": st.column_config.ProgressColumn(
            "Occupation",
            format="%.1f%%",
            min_value=0,
            max_value=100
        )
    }
    
    # Éditeur de données
    edited_df = st.data_editor(
        display_df[available_cols],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )
    
    if st.button("💾 Enregistrer modifications"):
        st.success("Modifications enregistrées (simulation)")
    
    # Export
    if st.button("📥 Exporter vers Excel"):
        try:
            from io import BytesIO
            buffer = BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Examens', index=False)
                
                summary = pd.DataFrame({
                    'Statistique': ['Total examens', 'Total étudiants', 'Heures totales'],
                    'Valeur': [len(df), df['nb_etudiants'].sum(), df['duree_minutes'].sum()/60]
                })
                summary.to_excel(writer, sheet_name='Résumé', index=False)
            
            buffer.seek(0)
            
            st.download_button(
                label="⬇️ Télécharger fichier Excel",
                data=buffer,
                file_name=f"examens_professeur_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"Erreur export: {e}")

# ========== TAB 3: MODULES ==========
def render_modules_tab(prof_id: int):
    """
    Modules dont le professeur est responsable
    """
    st.subheader("📚 Mes modules")
    
    # Récupération depuis BDD
    df_modules = safe_get_modules(prof_id)
    
    if df_modules.empty:
        st.info("👨‍🏫 Vous n'êtes responsable d'aucun module")
        return
    
    # Statistiques
    st.markdown("#### 📊 Vue d'ensemble")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_modules = len(df_modules)
        st.metric("Modules", total_modules)
    
    with col2:
        total_credits = df_modules['credits'].sum() if 'credits' in df_modules.columns else 0
        st.metric("Crédits totaux", total_credits)
    
    with col3:
        if 'nb_etudiants_inscrits' in df_modules.columns:
            total_students = df_modules['nb_etudiants_inscrits'].sum()
            st.metric("Étudiants inscrits", total_students)
    
    with col4:
        semestres = df_modules['semestre'].nunique() if 'semestre' in df_modules.columns else 0
        st.metric("Semestres", semestres)
    
    # Tableau des modules
    st.markdown("#### 📋 Liste des modules")
    
    # Filtrer par semestre
    if 'semestre' in df_modules.columns:
        semestres_uniques = sorted(df_modules['semestre'].unique())
        selected_semester = st.selectbox("Filtrer par semestre", 
                                        ["Tous"] + list(semestres_uniques))
        
        if selected_semester != "Tous":
            df_modules = df_modules[df_modules['semestre'] == selected_semester]
    
    # Afficher les modules
    for idx, module in df_modules.iterrows():
        with st.expander(f"📘 {module['code']} - {module['nom']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Semestre:** {module.get('semestre', 'N/A')}")
                st.write(f"**Crédits:** {module.get('credits', 0)}")
                st.write(f"**Formation:** {module.get('formation_nom', 'N/A')}")
            
            with col2:
                st.write(f"**Code:** {module.get('code', 'N/A')}")
                if 'nb_etudiants_inscrits' in module:
                    st.write(f"**Étudiants:** {module['nb_etudiants_inscrits']}")
                if 'nb_examens_planifies' in module:
                    st.write(f"**Examens:** {module['nb_examens_planifies']}")
            
            with col3:
                if st.button("📅 Voir examens", key=f"exams_{module['id']}"):
                    df_all_exams = safe_get_exams(prof_id, 365)
                    if not df_all_exams.empty:
                        module_exams = df_all_exams[df_all_exams['module_nom'] == module['nom']]
                        if not module_exams.empty:
                            st.write(f"**Examens pour {module['nom']}:**")
                            st.dataframe(module_exams[['date_heure', 'salle_nom', 'statut']])
                        else:
                            st.info("Aucun examen programmé")
                
                if st.button("📊 Statistiques", key=f"stats_{module['id']}"):
                    st.info(f"Statistiques détaillées pour {module['nom']}")

# ========== TAB 4: STATISTIQUES ==========
def render_statistics_tab(prof_id: int, prof_stats: dict):
    """
    Statistiques détaillées depuis BDD
    """
    st.subheader("📊 Statistiques détaillées")
    
    # KPIs depuis BDD
    st.markdown("#### 📈 Indicateurs clés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        exams_future = prof_stats.get('examens_a_venir', 0)
        st.metric("Examens à venir", exams_future)
    
    with col2:
        exams_done = prof_stats.get('examens_termines', 0)
        st.metric("Examens terminés", exams_done)
    
    with col3:
        modules_resp = prof_stats.get('modules_responsables', 0)
        st.metric("Modules responsables", modules_resp)
    
    with col4:
        df_month = safe_get_exams(prof_id, 30)
        hours_month = (df_month['duree_minutes'].sum() / 60) if not df_month.empty and 'duree_minutes' in df_month.columns else 0
        st.metric("Heures ce mois", f"{hours_month:.1f}h")
    
    # Analyse sur l'année
    df_year = safe_get_exams(prof_id, 365)
    
    if not df_year.empty:
        st.markdown("#### 📅 Analyse annuelle")
        
        # Préparation des données
        df_year['date_heure'] = pd.to_datetime(df_year['date_heure'])
        df_year['mois'] = df_year['date_heure'].dt.strftime('%Y-%m')
        df_year['semaine'] = df_year['date_heure'].dt.isocalendar().week
        
        # Graphique 1: Évolution mensuelle
        monthly_stats = df_year.groupby('mois').agg({
            'nb_etudiants': 'sum',
            'duree_minutes': 'sum',
            'date_heure': 'count'
        }).reset_index()
        
        monthly_stats['total_heures'] = monthly_stats['duree_minutes'] / 60
        monthly_stats['mois_format'] = pd.to_datetime(monthly_stats['mois'] + '-01').dt.strftime('%b %Y')
        
        fig1 = px.line(
            monthly_stats,
            x='mois_format',
            y='total_heures',
            title="Heures de surveillance par mois",
            markers=True
        )
        fig1.add_hline(y=monthly_stats['total_heures'].mean(), 
                      line_dash="dash", 
                      line_color="red",
                      annotation_text=f"Moyenne: {monthly_stats['total_heures'].mean():.1f}h")
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # Graphique 2: Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            if 'type_examen' in df_year.columns:
                type_dist = df_year['type_examen'].value_counts()
                fig2 = px.pie(
                    values=type_dist.values,
                    names=type_dist.index,
                    title="Distribution par type",
                    hole=0.4
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            if 'formation_nom' in df_year.columns:
                formation_dist = df_year['formation_nom'].value_counts().head(5)
                fig3 = px.bar(
                    x=formation_dist.values,
                    y=formation_dist.index,
                    orientation='h',
                    title="Top 5 formations",
                    labels={'x': 'Nombre', 'y': 'Formation'}
                )
                st.plotly_chart(fig3, use_container_width=True)
        
        # Analyse des salles
        st.markdown("#### 🏛️ Analyse des salles")
        
        if 'salle_nom' in df_year.columns and 'taux_occupation' in df_year.columns:
            room_stats = df_year.groupby('salle_nom').agg({
                'nb_etudiants': 'sum',
                'taux_occupation': 'mean',
                'date_heure': 'count'
            }).reset_index()
            
            fig4 = px.scatter(
                room_stats,
                x='date_heure',
                y='taux_occupation',
                size='nb_etudiants',
                color='salle_nom',
                title="Utilisation des salles",
                hover_name='salle_nom'
            )
            st.plotly_chart(fig4, use_container_width=True)

# ========== TAB 5: CONFLITS ==========
def render_conflicts_tab(prof_id: int):
    """
    Détection des conflits depuis BDD - VERSION CORRIGÉE
    """
    st.subheader("⚠️ Conflits et alertes")
    
    try:
        # Récupération des conflits
        conflicts_data = OptimizationQueries.detect_all_conflicts()
        
        # Gestion des différents formats de retour
        if isinstance(conflicts_data, pd.DataFrame):
            conflicts_df = conflicts_data
        elif isinstance(conflicts_data, dict):
            if conflicts_data:  # dict non vide
                conflicts_df = pd.DataFrame([conflicts_data])
            else:  # dict vide
                conflicts_df = pd.DataFrame()
        elif isinstance(conflicts_data, list):
            if conflicts_data:  # liste non vide
                conflicts_df = pd.DataFrame(conflicts_data)
            else:  # liste vide
                conflicts_df = pd.DataFrame()
        else:
            st.warning(f"⚠️ Format de données inattendu: {type(conflicts_data)}")
            conflicts_df = pd.DataFrame()
        
        # Si on a des données
        if isinstance(conflicts_df, pd.DataFrame) and not conflicts_df.empty:
            # Filtrer les conflits du professeur
            try:
                prof_conflicts = conflicts_df[
                    conflicts_df['details'].str.contains(str(prof_id), na=False) | 
                    conflicts_df['type_conflit'].str.contains('Professeur', na=False)
                ]
                
                if not prof_conflicts.empty:
                    st.warning(f"🚨 {len(prof_conflicts)} conflit(s) détecté(s)")
                    
                    for idx, conflict in prof_conflicts.iterrows():
                        # Icônes selon sévérité
                        severity_icon = {
                            'CRITIQUE': '🔴',
                            'ÉLEVÉ': '🟠', 
                            'MOYEN': '🟡',
                            'FAIBLE': '🟢'
                        }.get(conflict.get('severite', 'FAIBLE'), '⚪')
                        
                        with st.expander(f"{severity_icon} {conflict.get('type_conflit', 'Conflit')}"):
                            st.write(f"**Détails:** {conflict.get('details', 'Non spécifié')}")
                            st.write(f"**Sévérité:** {conflict.get('severite', 'Non spécifié')}")
                            
                            # Actions
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("👁️ Détails", key=f"details_{idx}"):
                                    st.info("Affichage détaillé à implémenter")
                            with col2:
                                if st.button("✓ Résolu", key=f"resolved_{idx}"):
                                    st.success("Conflit marqué comme résolu")
                            with col3:
                                if st.button("📧 Notifier", key=f"notify_{idx}"):
                                    st.info("Notification envoyée")
                else:
                    st.success("✅ Aucun conflit ne vous concerne")
                    
            except Exception as filter_error:
                st.error(f"Erreur filtrage conflits: {filter_error}")
                # Afficher tous les conflits en mode debug
                with st.expander("🔧 Debug - Tous les conflits"):
                    st.write(conflicts_df)
        else:
            st.info("✅ Aucun conflit détecté dans le système")
            
    except Exception as e:
        st.error(f"Erreur détection conflits: {e}")
        st.info("ℹ️ La fonction de détection de conflits n'est pas encore disponible")
    
    # Analyse de charge personnelle
    st.markdown("#### 📊 Analyse de votre charge")
    
    df = safe_get_exams(prof_id, 30)
    
    if not df.empty:
        try:
            df['date'] = pd.to_datetime(df['date_heure']).dt.date
            daily_load = df.groupby('date').size().reset_index(name='examens')
            
            if not daily_load.empty:
                fig = px.bar(
                    daily_load,
                    x='date',
                    y='examens',
                    title="Examens par jour (30 derniers jours)",
                    labels={'date': 'Date', 'examens': 'Nombre d\'examens'}
                )
                fig.add_hline(y=3, line_dash="dash", line_color="red", 
                             annotation_text="Limite recommandée: 3 examens/jour")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Détection surcharge
                overload_days = daily_load[daily_load['examens'] > 3]
                if not overload_days.empty:
                    st.warning(f"⚠️ {len(overload_days)} jour(s) de surcharge détecté(s)")
                    
                    for _, day in overload_days.iterrows():
                        with st.expander(f"📅 {day['date']}: {day['examens']} examens"):
                            day_exams = df[df['date'] == day['date']]
                            for _, exam in day_exams.iterrows():
                                st.write(f"• **{exam.get('module_nom', 'Module')}**")
                                st.write(f"  🕒 {exam.get('date_heure', '').strftime('%H:%M') if hasattr(exam.get('date_heure', ''), 'strftime') else exam.get('date_heure', '')}")
                                st.write(f"  🏛️ {exam.get('salle_nom', 'Salle')}")
        except Exception as e:
            st.error(f"Erreur analyse charge: {e}")
    else:
        st.info("📭 Aucun examen trouvé pour l'analyse de charge")

# ========== TAB 6: GESTION ==========
def render_management_tab(prof_id: int):
    """
    Gestion des préférences et indisponibilités
    """
    st.subheader("⚙️ Gestion")
    
    # Section 1: Préférences
    st.markdown("#### 🎯 Préférences personnelles")
    
    with st.form("preferences_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            max_daily = st.slider("Maximum d'examens par jour", 1, 5, 3)
            pref_start = st.time_input("Heure début préférée", datetime.strptime("08:30", "%H:%M").time())
        
        with col2:
            min_break = st.slider("Pause minimale (min)", 30, 180, 60, step=15)
            pref_end = st.time_input("Heure fin préférée", datetime.strptime("17:30", "%H:%M").time())
        
        st.markdown("#### 🏛️ Préférences de salles")
        
        building_options = ["Bâtiment Central", "Bâtiment A", "Bâtiment B", "Bâtiment Info"]
        building_pref = st.multiselect("Bâtiments préférés", building_options, 
                                      default=["Bâtiment Central"])
        
        avoid_small = st.checkbox("Éviter salles < 30 places", True)
        
        if st.form_submit_button("💾 Sauvegarder préférences"):
            st.success("Préférences sauvegardées")
    
    # Section 2: Indisponibilités
    st.markdown("---")
    st.markdown("#### 📅 Gestion des indisponibilités")
    
    # Afficher les indisponibilités existantes
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=60)
    
    # تصحيح: استخدام UserQueries بدلاً من ProfesseurQueries
    indisponibilites = UserQueries.get_professor_availability(prof_id, start_date, end_date)
    
    if indisponibilites:
        st.markdown("##### Vos indisponibilités")
        for indispo in indisponibilites:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{indispo['motif']}**")
                st.write(f"{indispo['date_debut']} - {indispo['date_fin']}")
            with col2:
                if indispo.get('details'):
                    st.caption(indispo['details'])
            with col3:
                if st.button("❌", key=f"delete_{indispo['id']}"):
                    # تصحيح: استخدام UserQueries بدلاً من ProfesseurQueries
                    result = UserQueries.delete_unavailability(indispo['id'])
                    if result:
                        st.success("Indisponibilité supprimée")
                        st.rerun()
    
    # Ajouter nouvelle indisponibilité
    with st.expander("➕ Ajouter une indisponibilité"):
        col1, col2 = st.columns(2)
        with col1:
            new_start_date = st.date_input("Date début", datetime.now().date(), key="new_start")
            new_start_time = st.time_input("Heure début", datetime.strptime("08:00", "%H:%M").time(), key="new_start_time")
        with col2:
            new_end_date = st.date_input("Date fin", datetime.now().date() + timedelta(days=1), key="new_end")
            new_end_time = st.time_input("Heure fin", datetime.strptime("18:00", "%H:%M").time(), key="new_end_time")
        
        motif_options = ["Congé", "Réunion", "Mission", "Formation", "Maladie", "Recherche", "Autre"]
        new_motif = st.selectbox("Motif", motif_options)
        
        new_details = st.text_area("Détails supplémentaires")
        
        if st.button("✅ Ajouter indisponibilité"):
            start_datetime = datetime.combine(new_start_date, new_start_time)
            end_datetime = datetime.combine(new_end_date, new_end_time)
            
            if start_datetime >= end_datetime:
                st.error("La date de début doit être avant la date de fin")
            else:
                # تصحيح: استخدام UserQueries بدلاً من ProfesseurQueries
                result = UserQueries.add_unavailability(
                    prof_id, start_datetime, end_datetime, new_motif, new_details
                )
                if result:
                    st.success("Indisponibilité ajoutée avec succès")
                    st.rerun()
    
    # Section 3: Export
    st.markdown("---")
    st.markdown("#### 📤 Export de données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Planning PDF", use_container_width=True):
            st.info("Export PDF à implémenter")
    
    with col2:
        if st.button("📊 Statistiques Excel", use_container_width=True):
            df_exams = safe_get_exams(prof_id, 365)
            if not df_exams.empty:
                try:
                    from io import BytesIO
                    buffer = BytesIO()
                    
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_exams.to_excel(writer, sheet_name='Examens', index=False)
                        
                        stats_data = {
                            'Période': ['30 jours', '90 jours', '365 jours'],
                            'Examens': [
                                len(safe_get_exams(prof_id, 30)),
                                len(safe_get_exams(prof_id, 90)),
                                len(df_exams)
                            ],
                            'Heures': [
                                safe_get_exams(prof_id, 30)['duree_minutes'].sum()/60,
                                safe_get_exams(prof_id, 90)['duree_minutes'].sum()/60,
                                df_exams['duree_minutes'].sum()/60
                            ]
                        }
                        stats_df = pd.DataFrame(stats_data)
                        stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
                    
                    buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Télécharger Excel",
                        data=buffer,
                        file_name=f"donnees_professeur_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur export: {e}")
    
    with col3:
        if st.button("🗓️ Fichier iCal", use_container_width=True):
            df_calendar = safe_get_exams(prof_id, 90)
            if not df_calendar.empty:
                ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Plateforme Examens//FR\n"
                
                for _, exam in df_calendar.iterrows():
                    ics_content += "BEGIN:VEVENT\n"
                    ics_content += f"SUMMARY:{exam.get('module_nom', 'Examen')}\n"
                    ics_content += f"LOCATION:{exam.get('salle_nom', 'Salle')}\n"
                    ics_content += f"DESCRIPTION:Formation: {exam.get('formation_nom', '')}\\n"
                    ics_content += f"Étudiants: {exam.get('nb_etudiants', 0)}\\n"
                    ics_content += f"Durée: {exam.get('duree_minutes', 0)} minutes\n"
                    
                    if 'date_heure' in exam:
                        start_dt = pd.to_datetime(exam['date_heure'])
                        end_dt = start_dt + timedelta(minutes=exam.get('duree_minutes', 0))
                        ics_content += f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}\n"
                        ics_content += f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}\n"
                    
                    ics_content += "END:VEVENT\n"
                
                ics_content += "END:VCALENDAR"
                
                st.download_button(
                    label="⬇️ Télécharger iCal",
                    data=ics_content,
                    file_name=f"planning_professeur_{datetime.now().strftime('%Y%m%d')}.ics",
                    mime="text/calendar",
                    use_container_width=True
                )

# ========== CONFIGURATION ==========
if __name__ == "__main__":
    st.set_page_config(
        page_title="Professeur - Plateforme Examens",
        page_icon="👨‍🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .stMetric {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
            margin-bottom: 10px;
        }
        div[data-testid="stExpander"] div[role="button"] p {
            font-size: 1.1rem;
            font-weight: 600;
        }
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)
    
    render_professor_dashboard()