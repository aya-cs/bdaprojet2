"""
Interface étudiant moderne avec fonctionnalités avancées
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from queries import ExamQueries, AnalyticsQueries
import calendar

def render_student_dashboard():
    """
    Dashboard principal pour les étudiants
    """
    # Header avec informations personnelles
    student_info = st.session_state.user
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 10px; color: white;">
                <h3>👨‍🎓 {student_info.get('nom_complet', 'Étudiant')}</h3>
                <p>📚 {student_info.get('formation', 'Formation')}</p>
                <p>🏛️ {student_info.get('departement', 'Département')} • 🎓 Promo {student_info.get('promo', '')}</p>
                <p>📋 {student_info.get('modules_inscrits', 0)} modules • 📅 {student_info.get('examens_a_venir', 0)} examens à venir</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        today = datetime.now().date()
        exams_today = len([e for e in ExamQueries.get_student_exams(
            student_info['linked_id'], today, today
        )])
        
        st.metric("📅 Examens aujourd'hui", exams_today)
    
    with col3:
        next_7_days = len(ExamQueries.get_student_exams(
            student_info['linked_id'], 
            today, 
            today + timedelta(days=7)
        ))
        st.metric("📆 7 prochains jours", next_7_days)
    
    st.markdown("---")
    
    # Onglets pour différentes vues
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Planning Personnel", 
        "🗺️ Vue Salle", 
        "📊 Statistiques", 
        "🔔 Notifications"
    ])
    
    with tab1:
        render_personal_schedule(student_info['linked_id'])
    
    with tab2:
        render_room_view(student_info['linked_id'])
    
    with tab3:
        render_student_statistics(student_info['linked_id'])
    
    with tab4:
        render_notifications(student_info['linked_id'])

def render_personal_schedule(student_id: int):
    """
    Affiche le planning personnel de l'étudiant
    """
    # Filtres de date
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Date de début", 
                                  datetime.now().date())
    with col2:
        end_date = st.date_input("Date de fin", 
                                datetime.now().date() + timedelta(days=30))
    with col3:
        view_type = st.selectbox("Type de vue", 
                                ["Timeline", "Calendrier", "Liste"])
    
    # Récupérer les examens
    exams = ExamQueries.get_student_exams(student_id, start_date, end_date)
    
    if not exams:
        st.info("🎉 Aucun examen prévu pour cette période")
        return
    
    df = pd.DataFrame(exams)
    
    if view_type == "Timeline":
        # Timeline interactive
        fig = px.timeline(
            df,
            x_start="date_heure",
            x_end="date_fin",
            y="module_nom",
            color="departement_nom",
            hover_data=["salle_nom", "professeur_nom", "taux_occupation"],
            title="📅 Planning de vos examens",
            labels={
                "date_heure": "Date et Heure",
                "module_nom": "Module",
                "departement_nom": "Département"
            }
        )
        fig.update_layout(
            height=500,
            xaxis_title="",
            yaxis_title="",
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Liste détaillée
        st.subheader("📋 Détail des examens")
        display_df = df[[
            'date_heure', 'module_nom', 'salle_nom', 
            'professeur_nom', 'duree_minutes', 'type_examen'
        ]].copy()
        display_df['date_heure'] = pd.to_datetime(display_df['date_heure']).dt.strftime('%d/%m/%Y %H:%M')
        st.dataframe(display_df, use_container_width=True)
    
    elif view_type == "Calendrier":
        # Vue calendrier
        df['jour'] = pd.to_datetime(df['date_heure']).dt.date
        df['heure'] = pd.to_datetime(df['date_heure']).dt.strftime('%H:%M')
        
        # Grouper par jour
        daily_exams = df.groupby('jour').agg({
            'module_nom': list,
            'salle_nom': list,
            'heure': list
        }).reset_index()
        
        for _, row in daily_exams.iterrows():
            with st.expander(f"📅 {row['jour'].strftime('%A %d %B %Y')}"):
                for i, module in enumerate(row['module_nom']):
                    st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 5px; border-left: 4px solid #667eea;">
                            <strong>🕒 {row['heure'][i]}</strong> • <strong>{module}</strong><br>
                            📍 {row['salle_nom'][i]}
                        </div>
                    """, unsafe_allow_html=True)
    
    else:  # Liste
        st.dataframe(df[[
            'date_heure', 'module_nom', 'salle_nom', 
            'professeur_nom', 'duree_minutes', 'type_examen', 'statut'
        ]], use_container_width=True)

def render_room_view(student_id: int):
    """
    Affiche la vue des salles avec plans
    """
    st.subheader("🗺️ Localisation de vos examens")
    
    # Récupérer les salles pour les prochains examens
    exams = ExamQueries.get_student_exams(
        student_id, 
        datetime.now().date(), 
        datetime.now().date() + timedelta(days=14)
    )
    
    if not exams:
        st.info("Aucun examen prévu dans les 14 prochains jours")
        return
    
    df = pd.DataFrame(exams)
    
    # Carte des salles
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Visualisation des bâtiments (simulée)
        st.markdown("### 🏛️ Plan des bâtiments")
        
        # Créer une visualisation simple
        fig = go.Figure()
        
        # Ajouter des marqueurs pour chaque salle
        buildings = df['batiment'].unique()
        colors = px.colors.qualitative.Set3
        
        for i, building in enumerate(buildings):
            building_exams = df[df['batiment'] == building]
            fig.add_trace(go.Scatter(
                x=[i * 10],
                y=[len(building_exams)],
                mode='markers+text',
                marker=dict(size=len(building_exams) * 5, color=colors[i % len(colors)]),
                text=[f"{building}<br>{len(building_exams)} examens"],
                textposition="bottom center",
                name=building
            ))
        
        fig.update_layout(
            title="Répartition des examens par bâtiment",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📍 Détails des salles")
        for _, exam in df.iterrows():
            with st.expander(f"{exam['salle_nom']} - {exam['date_heure'].strftime('%d/%m %H:%M')}"):
                st.markdown(f"""
                    **Module:** {exam['module_nom']}<br>
                    **Type de salle:** {exam['salle_type']}<br>
                    **Capacité:** {exam.get('capacite', 'N/A')} places<br>
                    **Occupation:** {exam.get('taux_occupation', 'N/A')}%<br>
                    **Bâtiment:** {exam['batiment']}
                """, unsafe_allow_html=True)
                
                if 'Amphi' in exam['salle_nom']:
                    st.info("💡 Les amphithéâtres sont au rez-de-chaussée du bâtiment central")
                elif 'Salle' in exam['salle_nom']:
                    st.info("💡 Vérifiez l'étage dans le nom de la salle (ex: Salle 201 = 2ème étage)")

def render_student_statistics(student_id: int):
    """
    Affiche les statistiques personnelles de l'étudiant
    """
    all_exams = ExamQueries.get_student_exams(student_id)
    
    if not all_exams:
        st.info("Aucune donnée statistique disponible")
        return
    
    df = pd.DataFrame(all_exams)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_exams = len(df)
        st.metric("📊 Total examens", total_exams)
    
    with col2:
        avg_duration = df['duree_minutes'].mean()
        st.metric("⏱️ Durée moyenne", f"{avg_duration:.0f} min")
    
    with col3:
        completed = len(df[df['statut'] == 'Terminé'])
        st.metric("✅ Terminés", completed)
    
    with col4:
        upcoming = len(df[df['date_heure'] > datetime.now()])
        st.metric("📅 À venir", upcoming)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        type_dist = df['type_examen'].value_counts()
        fig1 = px.pie(
            values=type_dist.values,
            names=type_dist.index,
            title="Répartition par type d'examen",
            hole=0.4
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        df['semaine'] = pd.to_datetime(df['date_heure']).dt.isocalendar().week
        weekly_load = df.groupby('semaine').size()
        
        fig2 = px.bar(
            x=weekly_load.index,
            y=weekly_load.values,
            title="Nombre d'examens par semaine",
            labels={'x': 'Semaine', 'y': "Nombre d'examens"}
        )
        fig2.update_layout(xaxis_tickmode='linear')
        st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("📅 Calendrier de charge")
    
    df['date'] = pd.to_datetime(df['date_heure']).dt.date
    daily_load = df.groupby('date').size().reset_index(name='count')
    
    date_range = pd.date_range(start=daily_load['date'].min(), 
                              end=daily_load['date'].max())
    daily_load = daily_load.set_index('date').reindex(date_range, fill_value=0).reset_index()
    daily_load.columns = ['date', 'count']
    
    fig3 = px.density_heatmap(
        daily_load,
        x=daily_load['date'].dt.strftime('%A'),
        y=daily_load['date'].dt.isocalendar().week,
        z='count',
        color_continuous_scale='Viridis',
        title="Charge d'examens par jour de la semaine"
    )
    st.plotly_chart(fig3, use_container_width=True)
# أضف هذا الكود في student.py بعد دالة render_student_statistics
def render_notifications(student_id: int):
    """
    Affiche les notifications et alertes pour l'étudiant
    """
    from queries import UserQueries
    
    st.subheader("🔔 Vos notifications")
    
    # الحصول على الإشعارات
    notifications = UserQueries.get_notifications(student_id, 'etudiant', 10)
    
    if not notifications:
        st.success("🎉 Aucune notification non lue pour le moment!")
        
        # Afficher les notifications déjà lues
        st.info("📋 Historique des notifications:")
        st.write("1. Changement de salle - Information")
        st.write("2. Examen Algorithmique - Rappel")
        return
    
    # Afficher les notifications non lues
    unread = [n for n in notifications if not n.get('is_lu', False)]
    read = [n for n in notifications if n.get('is_lu', False)]
    
    if unread:
        st.write(f"**📬 Non lues ({len(unread)})**")
        for notif in unread:
            with st.expander(f"{'🔴' if notif.get('priority', 1) == 3 else '🟡' if notif.get('priority', 1) == 2 else '🔵'} {notif.get('titre', 'Sans titre')}"):
                st.write(f"**Type:** {notif.get('type_notification', 'Non spécifié')}")
                st.write(f"**Contenu:** {notif.get('contenu', '')}")
                st.write(f"**Priorité:** {notif.get('priority', 1)}")
                st.write(f"**Date:** {notif.get('created_at', '')}")
                
                if st.button("Marquer comme lu", key=f"read_{notif.get('id')}"):
                    UserQueries.mark_notification_as_read(notif.get('id'))
                    st.success("✅ Notification marquée comme lue")
                    st.rerun()
    
    if read:
        st.write(f"**📖 Déjà lues ({len(read)})**")
        for notif in read:
            with st.expander(f"✅ {notif.get('titre', 'Sans titre')}"):
                st.write(f"**Contenu:** {notif.get('contenu', '')}")
                st.write(f"**Date:** {notif.get('created_at', '')}")
    
    # Bouton pour marquer toutes comme lues
    if unread:
        if st.button("📌 Marquer toutes comme lues", type="primary"):
            for notif in unread:
                if notif.get('id'):
                    UserQueries.mark_notification_as_read(notif.get('id'))
            st.success("✅ Toutes les notifications marquées comme lues")
            st.rerun()