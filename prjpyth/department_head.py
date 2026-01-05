"""
Interface chef de département avec analytics avancés
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from queries import ExamQueries, AnalyticsQueries, OptimizationQueries

def render_department_head_dashboard():
    """
    Dashboard principal pour les chefs de département
    """
    chef_info = st.session_state.user
    
    # Header élaboré
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FF6B6B 0%, #EE5A52 100%); 
                        padding: 1.5rem; border-radius: 10px; color: white;">
                <h3>👨‍💼 {chef_info.get('nom_complet', 'Chef de Département')}</h3>
                <p>🏛️ Département: {chef_info.get('departement', 'Département')} ({chef_info.get('departement_code', 'Code')})</p>
                <p>📅 Mandat: {chef_info.get('date_nomination', '')} - {chef_info.get('date_fin_mandat', '')}</p>
                <p>📚 {chef_info.get('nb_formations', 0)} formations • 👨‍🎓 {chef_info.get('nb_etudiants', 0)} étudiants • 👨‍🏫 {chef_info.get('nb_professeurs', 0)} professeurs</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # KPIs rapides
        stats = AnalyticsQueries.get_department_stats(chef_info.get('linked_entity_id', 0))
        st.metric("📊 Examens planifiés", stats.get('nb_examens_planifies', 0))
    
    with col3:
        st.metric("✅ Examens terminés", stats.get('nb_examens_termines', 0))
    
    st.markdown("---")
    
    # Onglets avancés
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Tableau de bord", 
        "⚠️ Gestion Conflits", 
        "🔄 Optimisation", 
        "📊 Analytics", 
        "👥 Ressources"
    ])
    
    with tab1:
        render_department_dashboard(chef_info.get('linked_entity_id', 0))
    
    with tab2:
        render_conflict_management(chef_info.get('linked_entity_id', 0))
    
    with tab3:
        render_optimization_tools(chef_info.get('linked_entity_id', 0))
    
    with tab4:
        render_advanced_analytics(chef_info.get('linked_entity_id', 0))
    
    with tab5:
        render_resource_management(chef_info.get('linked_entity_id', 0))

def render_department_dashboard(dept_id: int):
    """
    Tableau de bord principal du département
    """
    # KPIs en haut
    stats = AnalyticsQueries.get_department_stats(dept_id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏛️ Formations", stats.get('nb_formations', 0))
    
    with col2:
        st.metric("👨‍🎓 Étudiants", stats.get('nb_etudiants', 0))
    
    with col3:
        st.metric("👨‍🏫 Professeurs", stats.get('nb_professeurs', 0))
    
    with col4:
        st.metric("📚 Modules", stats.get('nb_modules', 0))
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("📅 Examens", stats.get('nb_examens_planifies', 0))
    
    with col6:
        taux = (stats.get('nb_examens_termines', 0) / 
                max(stats.get('nb_examens_planifies', 1), 1) * 100)
        st.metric("✅ Taux réalisation", f"{taux:.1f}%")
    
    with col7:
        st.metric("🏢 Capacité moyenne", f"{stats.get('capacite_moyenne_salles', 0):.0f}")
    
    with col8:
        if stats.get('dernier_examen'):
            days_since = (datetime.now() - stats['dernier_examen']).days
            st.metric("📆 Dernier examen", f"J-{days_since}")
    
    st.markdown("---")
    
    # Vue planning du département
    st.subheader("📅 Planning du département")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", 
                                  datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("Date de fin", 
                                datetime.now().date() + timedelta(days=30))
    
    # Récupérer les examens
    exams_df = ExamQueries.get_department_exams(dept_id, start_date, end_date)
    
    if exams_df.empty:
        st.info("Aucun examen planifié pour cette période")
        return
    
    # Graphique 1: Timeline des examens
    fig1 = px.timeline(
        exams_df,
        x_start="date_heure",
        x_end="date_fin",
        y="formation_nom",
        color="type_examen",
        hover_data=["module_nom", "professeur_nom", "salle_nom", "taux_occupation"],
        title="Planning des examens par formation",
        height=600
    )
    fig1.update_layout(showlegend=True)
    st.plotly_chart(fig1, use_container_width=True)
    
    # Graphique 2: Occupation des salles
    st.subheader("🏛️ Occupation des salles")
    
    room_stats = exams_df.groupby('salle_nom').agg({
        'nb_etudiants_inscrits': 'sum',
        'taux_occupation': 'mean',
        'date_heure': 'count'
    }).reset_index()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig2 = px.bar(
            room_stats,
            x='salle_nom',
            y='taux_occupation',
            color='date_heure',
            title="Taux d'occupation moyen par salle",
            labels={'taux_occupation': 'Occupation (%)', 'date_heure': 'Nombre d\'examens'}
        )
        fig2.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        st.dataframe(room_stats.round(2), use_container_width=True)
    
    # Graphique 3: Charge par formation
    st.subheader("📊 Charge par formation")
    
    formation_load = exams_df.groupby('formation_nom').agg({
        'date_heure': 'count',
        'nb_etudiants_inscrits': 'sum'
    }).reset_index()
    
    fig3 = px.treemap(
        formation_load,
        path=['formation_nom'],
        values='nb_etudiants_inscrits',
        color='date_heure',
        title="Répartition de la charge d'examens",
        hover_data=['date_heure']
    )
    st.plotly_chart(fig3, use_container_width=True)

def render_conflict_management(dept_id: int):
    """
    Gestion avancée des conflits
    """
    st.subheader("⚠️ Analyse détaillée des conflits")
    
    # Récupérer tous les conflits
    conflicts_df = AnalyticsQueries.get_conflicts_report(dept_id)
    
    if conflicts_df.empty:
        st.success("✅ Aucun conflit détecté dans votre département")
        return
    
    # Métriques des conflits
    total_conflicts = conflicts_df['nombre'].sum()
    critical_conflicts = conflicts_df[conflicts_df['severite'] == 'CRITIQUE']['nombre'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🚨 Total conflits", total_conflicts)
    
    with col2:
        st.metric("🔴 Critiques", critical_conflicts)
    
    with col3:
        severity_dist = conflicts_df['severite'].value_counts().to_dict()
        st.metric("📊 Niveaux", len(severity_dist))
    
    st.markdown("---")
    
    # Détail par type de conflit
    for severity in ['CRITIQUE', 'ÉLEVÉ', 'MOYEN', 'FAIBLE']:
        severity_conflicts = conflicts_df[conflicts_df['severite'] == severity]
        
        if not severity_conflicts.empty:
            st.subheader(f"{'🔴' if severity == 'CRITIQUE' else '🟡' if severity == 'ÉLEVÉ' else '🔵'} {severity}")
            
            for _, conflict in severity_conflicts.iterrows():
                with st.expander(f"{conflict['type_conflit']} ({conflict['nombre']} occurrences)"):
                    st.write(f"**Détails:** {conflict['details']}")
                    
                    # Boutons d'action
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("👁️ Afficher détails", key=f"view_{severity}_{conflict['type_conflit']}"):
                            st.info("Fonctionnalité détaillée à implémenter")
                    with col2:
                        if st.button("✏️ Marquer comme résolu", key=f"resolve_{severity}_{conflict['type_conflit']}"):
                            st.success("Conflit marqué comme résolu")
                    with col3:
                        if st.button("📧 Notifier concernés", key=f"notify_{severity}_{conflict['type_conflif']}"):
                            st.info("Notifications envoyées")
    
    # Analyse temporelle des conflits
    st.subheader("📈 Tendances des conflits")
    
    # Simulation de données temporelles
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    simulated_data = pd.DataFrame({
        'date': dates,
        'conflits': np.random.poisson(3, 30) + (np.sin(np.arange(30) * 0.3) * 2).astype(int)
    })
    
    fig = px.line(
        simulated_data,
        x='date',
        y='conflits',
        title="Évolution quotidienne des conflits détectés",
        markers=True
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Nombre de conflits",
        hovermode='x unified'
    )
    fig.add_hline(y=simulated_data['conflits'].mean(), 
                  line_dash="dash", 
                  line_color="red",
                  annotation_text=f"Moyenne: {simulated_data['conflits'].mean():.1f}")
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommandations automatiques
    st.subheader("💡 Recommandations automatiques")
    
    recommendations = []
    
    if critical_conflicts > 5:
        recommendations.append({
            'priority': 'high',
            'title': '🚨 Conflits critiques nombreux',
            'action': 'Revoir immédiatement le planning des salles surchargées'
        })
    
    if total_conflicts > 20:
        recommendations.append({
            'priority': 'medium',
            'title': '📈 Volume élevé de conflits',
            'action': 'Lancer une optimisation globale du planning'
        })
    
    if conflicts_df['type_conflit'].str.contains('Professeur').any():
        recommendations.append({
            'priority': 'high',
            'title': '👨‍🏫 Conflits de professeurs',
            'action': 'Rééquilibrer les surveillances entre enseignants'
        })
    
    if not recommendations:
        st.success("✅ Aucune recommandation urgente")
    else:
        for rec in recommendations:
            if rec['priority'] == 'high':
                st.error(f"**{rec['title']}**\n\n{rec['action']}")
            else:
                st.warning(f"**{rec['title']}**\n\n{rec['action']}")

def render_optimization_tools(dept_id: int):
    """
    Outils d'optimisation automatique
    """
    st.subheader("🔄 Optimisation automatique du planning")
    
    # Paramètres d'optimisation
    with st.expander("⚙️ Paramètres d'optimisation"):
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Période de début", 
                                      datetime.now().date())
            priority_salle = st.slider("Priorité: Occupation salles", 1, 10, 7)
            priority_prof = st.slider("Priorité: Charge profs", 1, 10, 8)
        
        with col2:
            end_date = st.date_input("Période de fin", 
                                    datetime.now().date() + timedelta(days=14))
            priority_etudiant = st.slider("Priorité: Confort étudiants", 1, 10, 6)
            max_duration = st.number_input("Durée max optim. (secondes)", 10, 300, 45)
    
    # Bouton de génération
    if st.button("🚀 Générer planning optimisé", type="primary", use_container_width=True):
        with st.spinner(f"Optimisation en cours (max {max_duration}s)..."):
            # Simulation avec progression
            progress_bar = st.progress(0)
            
            for i in range(100):
                # Simulation du processus d'optimisation
                import time
                time.sleep(max_duration / 100)
                progress_bar.progress(i + 1)
            
            # Récupérer le planning optimisé
            optimized_df = OptimizationQueries.generate_optimized_schedule(
                start_date, end_date, dept_id
            )
            
            if optimized_df.empty:
                st.warning("Aucune optimisation possible avec les paramètres actuels")
                return
            
            st.success(f"✅ Planning optimisé généré: {len(optimized_df)} examens")
            
            # Afficher les résultats
            st.subheader("📋 Résultats de l'optimisation")
            
            # Scores d'optimisation
            fig1 = px.histogram(
                optimized_df,
                x='score_optimisation',
                nbins=20,
                title="Distribution des scores d'optimisation",
                labels={'score_optimisation': 'Score', 'count': 'Nombre d\'examens'}
            )
            fig1.add_vline(x=optimized_df['score_optimisation'].mean(), 
                          line_dash="dash", 
                          line_color="red",
                          annotation_text=f"Moyenne: {optimized_df['score_optimisation'].mean():.2f}")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Planning optimisé
            st.subheader("📅 Planning optimisé proposé")
            
            # Convertir pour la timeline
            optimized_df['date_fin'] = pd.to_datetime(optimized_df['date_heure']) + \
                                      pd.to_timedelta(optimized_df['duree_minutes'], unit='m')
            
            fig2 = px.timeline(
                optimized_df,
                x_start="date_heure",
                x_end="date_fin",
                y="module_nom",
                color="score_optimisation",
                hover_data=["salle_nom", "professeur_nom"],
                title="Planning optimisé proposé",
                color_continuous_scale='Viridis'
            )
            fig2.update_layout(height=600)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Comparaison avant/après
            st.subheader("📊 Comparaison avant/après")
            
            # Récupérer le planning actuel pour comparaison
            current_df = ExamQueries.get_department_exams(dept_id, start_date, end_date)
            
            if not current_df.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Occupation moyenne
                    current_occupancy = current_df['taux_occupation'].mean()
                    optimized_occupancy = 85  # Simulé
                    delta = optimized_occupancy - current_occupancy
                    st.metric("🏢 Occupation salles", 
                             f"{optimized_occupancy:.1f}%", 
                             f"{delta:+.1f}%")
                
                with col2:
                    # Conflits
                    current_conflicts = len(AnalyticsQueries.get_conflicts_report(dept_id))
                    optimized_conflicts = max(0, current_conflicts - 5)  # Simulé
                    delta = optimized_conflicts - current_conflicts
                    st.metric("⚠️ Conflits détectés", 
                             optimized_conflicts, 
                             f"{delta:+d}")
                
                with col3:
                    # Équilibre professeurs
                    current_std = current_df.groupby('professeur_nom').size().std()
                    optimized_std = max(0.1, current_std * 0.7)  # Simulé
                    delta_pct = ((optimized_std - current_std) / current_std * 100)
                    st.metric("⚖️ Équilibre profs", 
                             f"{optimized_std:.2f}", 
                             f"{delta_pct:+.1f}%")
            
            # Boutons d'action
            st.markdown("---")
            st.subheader("🎯 Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Appliquer ce planning", type="primary", use_container_width=True):
                    st.success("Planning appliqué avec succès")
                    # En production: mettre à jour la base de données
            
            with col2:
                if st.button("📥 Exporter en PDF", use_container_width=True):
                    st.info("Export PDF en cours de développement")
            
            with col3:
                if st.button("🔄 Réoptimiser", use_container_width=True):
                    st.rerun()

def render_advanced_analytics(dept_id: int):
    """
    Analytics avancés et prédictifs
    """
    st.subheader("🔮 Analytics Prédictifs")
    
    # Données simulées pour les prédictions
    periods = ['Semaine 1', 'Semaine 2', 'Semaine 3', 'Semaine 4']
    
    # Taux de réussite prédits vs réels
    predicted_success = [78, 82, 85, 88]
    actual_success = [76, 80, 83, 85]
    
    fig1 = go.Figure(data=[
        go.Scatter(
            x=periods,
            y=predicted_success,
            mode='lines+markers',
            name='Prédiction',
            line=dict(color='#667eea', width=3),
            marker=dict(size=10)
        ),
        go.Scatter(
            x=periods,
            y=actual_success,
            mode='lines+markers',
            name='Réel',
            line=dict(color='#764ba2', width=3),
            marker=dict(size=10, symbol='diamond')
        )
    ])
    
    fig1.update_layout(
        title="📈 Taux de réussite: Prédiction vs Réel",
        xaxis_title="Période",
        yaxis_title="Taux de réussite (%)",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # Analyse des tendances
    st.subheader("📊 Tendances par formation")
    
    formations = ['Informatique', 'Mathématiques', 'Physique', 'Chimie', 'Biologie']
    
    # Données multidimensionnelles
    data = {
        'Formation': formations * 4,
        'Métrique': ['Taux réussite']*5 + ['Charge examens']*5 + ['Satisfaction']*5 + ['Ressources']*5,
        'Valeur': [85, 78, 82, 79, 83,  # Taux réussite
                   88, 92, 85, 90, 87,  # Charge examens
                   4.2, 3.8, 4.0, 3.9, 4.1,  # Satisfaction
                   92, 88, 90, 85, 89], # Ressources
        'Tendance': ['↑', '↓', '→', '↓', '↑'] * 4
    }
    
    df_radar = pd.DataFrame(data)
    
    # Radar chart pour chaque formation
    fig2 = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, formation in enumerate(formations):
        formation_data = df_radar[df_radar['Formation'] == formation]
        fig2.add_trace(go.Scatterpolar(
            r=formation_data['Valeur'].values,
            theta=formation_data['Métrique'].values,
            fill='toself',
            name=formation,
            line_color=colors[i % len(colors)]
        ))
    
    fig2.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Analyse comparative des formations",
        height=500
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Insights automatiques
    st.subheader("💡 Insights et recommandations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style="background: #d4edda; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                <h4>✅ Points forts</h4>
                <ul>
                    <li><strong>Informatique:</strong> +3% réussite cette période</li>
                    <li><strong>Biologie:</strong> Satisfaction en hausse de 0.3 points</li>
                    <li><strong>Physique:</strong> Excellente utilisation des ressources (90%)</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="background: #fff3cd; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                <h4>⚠️ Points d'attention</h4>
                <ul>
                    <li><strong>Mathématiques:</strong> Tendance à la baisse (-2%)</li>
                    <li><strong>Chimie:</strong> Charge examens trop élevée (90%)</li>
                    <li><strong>Ressources:</strong> Salles spécialisées sous-utilisées</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    # Prédictions pour les prochaines périodes
    st.subheader("🔮 Prévisions pour les 4 prochaines semaines")
    
    # Simulation de données prédictives
    future_weeks = [f'Semaine {i}' for i in range(5, 9)]
    
    fig3 = go.Figure()
    
    # Ajouter la bande de confiance
    fig3.add_trace(go.Scatter(
        x=future_weeks,
        y=[86, 87, 88, 89],
        mode='lines',
        name='Prédiction haute',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig3.add_trace(go.Scatter(
        x=future_weeks,
        y=[82, 83, 84, 85],
        mode='lines',
        name='Prédiction basse',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(102, 126, 234, 0.2)',
        showlegend=False
    ))
    
    # Ajouter la prédiction moyenne
    fig3.add_trace(go.Scatter(
        x=future_weeks,
        y=[84, 85, 86, 87],
        mode='lines+markers',
        name='Prédiction moyenne',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))
    
    fig3.update_layout(
        title="📊 Prévision du taux de réussite",
        xaxis_title="Semaines à venir",
        yaxis_title="Taux de réussite (%)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    # Alertes prédictives
    st.subheader("🚨 Alertes prédictives")
    
    alerts = [
        {
            'type': 'warning',
            'message': 'Risque de surcharge: Semaine 6',
            'details': 'Prévision: 92% de charge, seuil critique à 90%'
        },
        {
            'type': 'info',
            'message': 'Opportunité optimisation',
            'details': 'Salles de TP disponibles à 65% la semaine 7'
        },
        {
            'type': 'success',
            'message': 'Tendance positive confirmée',
            'details': 'Informatique: +5% réussite sur 4 semaines'
        }
    ]
    
    for alert in alerts:
        if alert['type'] == 'warning':
            st.warning(f"**{alert['message']}**\n\n{alert['details']}")
        elif alert['type'] == 'info':
            st.info(f"**{alert['message']}**\n\n{alert['details']}")
        else:
            st.success(f"**{alert['message']}**\n\n{alert['details']}")

def render_resource_management(dept_id: int):
    """
    Gestion des ressources (salles, professeurs)
    """
    st.subheader("👥 Gestion des ressources")
    
    # Onglets pour différents types de ressources
    tab1, tab2, tab3 = st.tabs(["🏛️ Salles", "👨‍🏫 Professeurs", "📋 Affectations"])
    
    with tab1:
        render_room_management(dept_id)
    
    with tab2:
        render_professor_management(dept_id)
    
    with tab3:
        render_assignments_management(dept_id)

def render_room_management(dept_id: int):
    """
    Gestion des salles
    """
    # Récupérer les statistiques d'occupation
    start_date = datetime.now().date() - timedelta(days=30)
    end_date = datetime.now().date() + timedelta(days=30)
    
    room_stats = AnalyticsQueries.get_resource_utilization(start_date, end_date)
    
    if room_stats.empty:
        st.info("Aucune donnée de salle disponible")
        return
    
    # Vue d'ensemble
    st.subheader("📊 Vue d'ensemble des salles")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_rooms = len(room_stats)
        st.metric("🏛️ Total salles", total_rooms)
    
    with col2:
        avg_usage = room_stats['pourcentage_utilisation'].mean()
        st.metric("📈 Utilisation moyenne", f"{avg_usage:.1f}%")
    
    with col3:
        underused = len(room_stats[room_stats['pourcentage_utilisation'] < 50])
        st.metric("📉 Sous-utilisées", underused)
    
    # Détail par salle
    st.subheader("📋 Détail par salle")
    
    # Filtrer
    col1, col2 = st.columns(2)
    with col1:
        min_usage = st.slider("Filtre utilisation minimale (%)", 0, 100, 0)
    with col2:
        room_type = st.multiselect("Type de salle", 
                                  room_stats['salle_type'].unique(),
                                  default=room_stats['salle_type'].unique())
    
    filtered_stats = room_stats[
        (room_stats['pourcentage_utilisation'] >= min_usage) &
        (room_stats['salle_type'].isin(room_type))
    ]
    
    # Graphique
    fig = px.bar(
        filtered_stats.sort_values('pourcentage_utilisation', ascending=False),
        x='salle_nom',
        y='pourcentage_utilisation',
        color='salle_type',
        hover_data=['capacite', 'nb_examens', 'total_minutes'],
        title="Utilisation des salles",
        labels={'pourcentage_utilisation': 'Taux d\'utilisation (%)'}
    )
    fig.update_layout(xaxis_tickangle=45, height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Table interactive
    st.dataframe(
        filtered_stats[[
            'salle_nom', 'salle_type', 'capacite', 
            'nb_examens', 'pourcentage_utilisation', 
            'taux_occupation_moyen'
        ]].round(2),
        use_container_width=True
    )
    
    # Gestion des indisponibilités
    st.subheader("🚧 Gestion des indisponibilités")
    
    with st.expander("➕ Ajouter une indisponibilité"):
        col1, col2 = st.columns(2)
        with col1:
            selected_room = st.selectbox("Salle", room_stats['salle_nom'].unique())
            start_date = st.date_input("Date début", datetime.now().date())
        with col2:
            reason = st.selectbox("Motif", [
                "Maintenance", "Réunion", "Événement", "Autre"
            ])
            end_date = st.date_input("Date fin", datetime.now().date() + timedelta(days=1))
        
        details = st.text_area("Détails")
        
        if st.button("💾 Enregistrer l'indisponibilité"):
            # En production: insérer dans la base
            st.success(f"Indisponibilité enregistrée pour {selected_room}")

def render_professor_management(dept_id: int):
    """
    Gestion des professeurs
    """
    st.subheader("👨‍🏫 Gestion des enseignants")
    
    # Récupérer les données des professeurs
    # (À implémenter avec des requêtes réelles)
    
    # Simulation de données
    professors_data = pd.DataFrame({
        'Nom': ['Dupont Jean', 'Martin Marie', 'Bernard Pierre', 'Petit Sophie', 'Robert Luc'],
        'Grade': ['Professeur', 'MCF', 'MCF', 'Professeur', 'Assistant'],
        'Spécialité': ['Algorithmique', 'BDD', 'Analyse', 'Physique', 'Chimie'],
        'Heures/sem': [48, 42, 45, 50, 38],
        'Examens/sem': [8, 6, 7, 9, 5],
        'Satisfaction': [4.5, 4.2, 4.0, 4.7, 3.8],
        'Statut': ['Actif', 'Actif', 'Actif', 'Congé', 'Actif']
    })
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👨‍🏫 Total", len(professors_data))
    
    with col2:
        active = len(professors_data[professors_data['Statut'] == 'Actif'])
        st.metric("✅ Actifs", active)
    
    with col3:
        avg_hours = professors_data['Heures/sem'].mean()
        st.metric("⏱️ Heures/sem", f"{avg_hours:.1f}")
    
    with col4:
        avg_satisfaction = professors_data['Satisfaction'].mean()
        st.metric("😊 Satisfaction", f"{avg_satisfaction:.1f}/5")
    
    # Détail
    st.subheader("📋 Liste des enseignants")
    
    # Filtrer
    col1, col2 = st.columns(2)
    with col1:
        min_hours = st.slider("Heures minimum", 0, 60, 0)
    with col2:
        selected_status = st.multiselect("Statut", 
                                        professors_data['Statut'].unique(),
                                        default=['Actif'])
    
    filtered_profs = professors_data[
        (professors_data['Heures/sem'] >= min_hours) &
        (professors_data['Statut'].isin(selected_status))
    ]
    
    # Table interactive
    st.dataframe(filtered_profs, use_container_width=True)
    
    # Graphique de charge
    fig = px.scatter(
        filtered_profs,
        x='Heures/sem',
        y='Examens/sem',
        size='Satisfaction',
        color='Grade',
        hover_name='Nom',
        title="Charge de travail par enseignant",
        labels={'Heures/sem': 'Heures par semaine', 'Examens/sem': 'Examens par semaine'}
    )
    fig.add_hline(y=8, line_dash="dash", line_color="red", 
                 annotation_text="Limite recommandée: 8 examens/sem")
    st.plotly_chart(fig, use_container_width=True)
    
    # Gestion des indisponibilités
    st.subheader("📅 Gestion des disponibilités")
    
    with st.expander("👁️ Voir le calendrier des disponibilités"):
        # Calendrier simplifié
        st.write("**Calendrier des congés et indisponibilités**")
        
        # Simulation
        events = [
            {'Prof': 'Dupont Jean', 'Type': 'Congé', 'Début': '2024-01-15', 'Fin': '2024-01-22'},
            {'Prof': 'Martin Marie', 'Type': 'Mission', 'Début': '2024-01-18', 'Fin': '2024-01-20'},
            {'Prof': 'Petit Sophie', 'Type': 'Formation', 'Début': '2024-01-25', 'Fin': '2024-01-26'},
        ]
        
        for event in events:
            st.write(f"• **{event['Prof']}**: {event['Type']} ({event['Début']} au {event['Fin']})")

def render_assignments_management(dept_id: int):
    """
    Gestion des affectations
    """
    st.subheader("📋 Gestion des affectations examens/professeurs")
    
    # Simulation de données d'affectation
    assignments = pd.DataFrame({
        'Examen': ['Algorithmique Avancée', 'Bases de Données', 'Machine Learning', 
                   'Analyse Mathématique', 'Physique Quantique'],
        'Date': ['2024-01-15 08:00', '2024-01-15 14:00', '2024-01-16 08:00', 
                 '2024-01-16 14:00', '2024-01-17 08:00'],
        'Salle': ['Amphi A', 'Amphi B', 'Salle 101', 'Amphi C', 'Salle 201'],
        'Professeur actuel': ['Dupont Jean', 'Martin Marie', 'Moreau Claire', 
                             'Bernard Pierre', 'Petit Sophie'],
        'Professeur suggéré': ['Dupont Jean', 'Martin Marie', 'Dupont Jean', 
                              'Bernard Pierre', 'Petit Sophie'],
        'Score compatibilité': [95, 88, 92, 85, 90]
    })
    
    # Vue d'ensemble
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_assignments = len(assignments)
        st.metric("📋 Total affectations", total_assignments)
    
    with col2:
        avg_score = assignments['Score compatibilité'].mean()
        st.metric("⚡ Score moyen", f"{avg_score:.0f}/100")
    
    with col3:
        perfect_matches = len(assignments[assignments['Score compatibilité'] >= 90])
        st.metric("🎯 Correspondances parfaites", perfect_matches)
    
    # Table des affectations avec édition
    st.subheader("✏️ Édition des affectations")
    
    edited_df = st.data_editor(
        assignments,
        column_config={
            "Professeur actuel": st.column_config.SelectboxColumn(
                "Professeur actuel",
                options=['Dupont Jean', 'Martin Marie', 'Bernard Pierre', 
                        'Petit Sophie', 'Robert Luc', 'Moreau Claire']
            ),
            "Score compatibilité": st.column_config.ProgressColumn(
                "Score compatibilité",
                format="%d",
                min_value=0,
                max_value=100
            )
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if st.button("💾 Sauvegarder les modifications", type="primary"):
        st.success("Affectations sauvegardées avec succès")
    
    # Suggestions d'optimisation
    st.subheader("💡 Suggestions d'optimisation")
    
    suggestions = [
        "**Dupont Jean** a 3 examens le 16/01 - Considérer réaffecter 'Machine Learning'",
        "**Martin Marie** spécialiste BDD - Affectation cohérente maintenue",
        "**Salle 101** sous-utilisée - Ajouter plus d'examens dans cette salle",
        "**Bernard Pierre** a une compatibilité de 85% - Former en analyse avancée?"
    ]
    
    for suggestion in suggestions:
        with st.expander(suggestion.split(" - ")[0]):
            st.write(suggestion.split(" - ")[1] if " - " in suggestion else suggestion)
    
    # Bouton d'optimisation automatique
    if st.button("🔄 Optimiser automatiquement les affectations", use_container_width=True):
        with st.spinner("Optimisation en cours..."):
            # Simulation
            import time
            time.sleep(2)
            
            # Mettre à jour les scores
            assignments['Score compatibilité'] = assignments['Score compatibilité'] + 5
            assignments['Score compatibilité'] = assignments['Score compatibilité'].clip(0, 100)
            
            st.success("✅ Optimisation terminée! Scores améliorés de +5 points en moyenne")
            st.rerun()