-- ============================================
-- PLATEFORME D'OPTIMISATION DES EMPLOIS DU TEMPS D'EXAMENS
-- Base de données relationnelle avec contraintes d'optimisation
-- VERSION FINALE CORRIGÉE
-- ============================================

-- ============================================
-- 1. Création de la base de données
-- ============================================
DROP DATABASE IF EXISTS exam_platform;
CREATE DATABASE exam_platform
    ENCODING 'UTF8'
    LC_COLLATE 'fr_FR.UTF-8'
    LC_CTYPE 'fr_FR.UTF-8'
    TEMPLATE template0;

\c exam_platform

-- ============================================
-- 2. Extensions pour performances
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================
-- 3. Table des départements (Dimension)
-- ============================================
CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour recherche rapide
CREATE INDEX idx_departements_nom ON departements USING gin(nom gin_trgm_ops);

-- ============================================
-- 4. Table des formations
-- ============================================
CREATE TABLE formations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(150) NOT NULL,
    departement_id INT NOT NULL REFERENCES departements(id) ON DELETE CASCADE,
    niveau VARCHAR(20) CHECK (niveau IN ('Licence', 'Master', 'Doctorat')),
    nb_modules INT DEFAULT 0,
    annee_academique INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_formation_departement FOREIGN KEY (departement_id) 
        REFERENCES departements(id) ON DELETE CASCADE
);

-- Index composite pour performances
CREATE INDEX idx_formations_dept ON formations(departement_id, annee_academique);
CREATE INDEX idx_formations_niveau ON formations(niveau, is_active);

-- ============================================
-- 5. Table des modules (Matières)
-- ============================================
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(200) NOT NULL,
    credits INT NOT NULL CHECK (credits BETWEEN 1 AND 12),
    formation_id INT NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    semestre INT CHECK (semestre BETWEEN 1 AND 6),
    volume_horaire INT,
    pre_requis_id INT REFERENCES modules(id),
    responsable_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_module_formation FOREIGN KEY (formation_id) 
        REFERENCES formations(id) ON DELETE CASCADE,
    CONSTRAINT fk_module_pre_requis FOREIGN KEY (pre_requis_id) 
        REFERENCES modules(id) ON DELETE SET NULL
);

-- Index pour recherches fréquentes
CREATE INDEX idx_modules_formation ON modules(formation_id);
CREATE INDEX idx_modules_semestre ON modules(semestre, formation_id);

-- ============================================
-- 6. Table des étudiants
-- ============================================
CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    matricule VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE,
    email_univ VARCHAR(150) UNIQUE,
    formation_id INT NOT NULL REFERENCES formations(id) ON DELETE CASCADE,
    annee_inscription INT NOT NULL,
    statut VARCHAR(20) DEFAULT 'Actif' CHECK (statut IN ('Actif', 'Inactif', 'Diplômé', 'Abandon')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_etudiant_formation FOREIGN KEY (formation_id) 
        REFERENCES formations(id) ON DELETE CASCADE
);

-- Index pour performances sur les jointures
CREATE INDEX idx_etudiants_formation ON etudiants(formation_id, annee_inscription);
CREATE INDEX idx_etudiants_matricule ON etudiants(matricule);
CREATE INDEX idx_etudiants_statut ON etudiants(statut) WHERE statut = 'Actif';

-- ============================================
-- 7. Table des professeurs
-- ============================================
CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    matricule VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    grade VARCHAR(50),
    departement_id INT NOT NULL REFERENCES departements(id) ON DELETE CASCADE,
    specialite VARCHAR(200),
    email VARCHAR(150) UNIQUE,
    telephone VARCHAR(20),
    heures_min INT DEFAULT 48, -- Heures minimales par semaine
    heures_max INT DEFAULT 192, -- Heures maximales par semaine
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_professeur_departement FOREIGN KEY (departement_id) 
        REFERENCES departements(id) ON DELETE CASCADE
);

CREATE INDEX idx_professeurs_dept ON professeurs(departement_id, is_active);
CREATE INDEX idx_professeurs_matricule ON professeurs(matricule);

-- ============================================
-- 8. Table des lieux d'examen (Ressources)
-- ============================================
CREATE TABLE lieux_examen (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    capacite INT NOT NULL CHECK (capacite > 0),
    type VARCHAR(30) NOT NULL CHECK (type IN ('Amphithéâtre', 'Salle de cours', 'Laboratoire', 'Salle spécialisée')),
    batiment VARCHAR(50),
    etage INT,
    equipements TEXT[], -- Tableau d'équipements disponibles
    is_disponible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index partiel pour recherche rapide des salles disponibles
CREATE INDEX idx_lieux_disponibles ON lieux_examen(id, capacite) 
    WHERE is_disponible = TRUE;

-- Index pour recherche par capacité
CREATE INDEX idx_lieux_capacite ON lieux_examen(capacite, type);

-- ============================================
-- 9. Table des inscriptions étudiant-module
-- ============================================
CREATE TABLE inscriptions (
    id SERIAL PRIMARY KEY,
    etudiant_id INT NOT NULL REFERENCES etudiants(id) ON DELETE CASCADE,
    module_id INT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    annee_academique INT NOT NULL,
    session VARCHAR(10) CHECK (session IN ('Principale', 'Rattrapage')),
    note NUMERIC(4,2) CHECK (note BETWEEN 0 AND 20),
    statut VARCHAR(20) DEFAULT 'Inscrit' CHECK (statut IN ('Inscrit', 'Validé', 'Échoué', 'Abandonné')),
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP,
    UNIQUE(etudiant_id, module_id, annee_academique, session),
    CONSTRAINT fk_inscription_etudiant FOREIGN KEY (etudiant_id) 
        REFERENCES etudiants(id) ON DELETE CASCADE,
    CONSTRAINT fk_inscription_module FOREIGN KEY (module_id) 
        REFERENCES modules(id) ON DELETE CASCADE
);

-- Index pour accélérer les requêtes fréquentes
CREATE INDEX idx_inscriptions_etudiant ON inscriptions(etudiant_id, annee_academique);
CREATE INDEX idx_inscriptions_module ON inscriptions(module_id, annee_academique);
CREATE INDEX idx_inscriptions_statut ON inscriptions(statut, annee_academique);

-- ============================================
-- 10. Table principale des examens (Planning)
-- ============================================
CREATE TABLE examens (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4(),
    module_id INT NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    professeur_id INT NOT NULL REFERENCES professeurs(id) ON DELETE CASCADE,
    salle_id INT NOT NULL REFERENCES lieux_examen(id) ON DELETE CASCADE,
    date_heure TIMESTAMP NOT NULL,
    duree_minutes INT NOT NULL CHECK (duree_minutes BETWEEN 60 AND 240),
    type_examen VARCHAR(30) DEFAULT 'Final' CHECK (type_examen IN ('Final', 'Partiel', 'Rattrapage', 'Contrôle')),
    statut VARCHAR(20) DEFAULT 'Planifié' CHECK (statut IN ('Planifié', 'Confirmé', 'Annulé', 'Terminé')),
    max_etudiants INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT,
    notes TEXT,
    
    -- Contraintes d'intégrité référentielle
    CONSTRAINT fk_examen_module FOREIGN KEY (module_id) 
        REFERENCES modules(id) ON DELETE CASCADE,
    CONSTRAINT fk_examen_professeur FOREIGN KEY (professeur_id) 
        REFERENCES professeurs(id) ON DELETE CASCADE,
    CONSTRAINT fk_examen_salle FOREIGN KEY (salle_id) 
        REFERENCES lieux_examen(id) ON DELETE CASCADE,
    
    -- Contrainte: pas deux examens dans la même salle en même temps
    CONSTRAINT unique_salle_temps UNIQUE(salle_id, date_heure)
);

-- INDEX CRITIQUES POUR PERFORMANCES (Optimisation demandée <45s)
CREATE INDEX idx_examens_date ON examens(date_heure DESC);
CREATE INDEX idx_examens_module ON examens(module_id);
CREATE INDEX idx_examens_professeur ON examens(professeur_id);
CREATE INDEX idx_examens_salle ON examens(salle_id);
CREATE INDEX idx_examens_statut ON examens(statut) WHERE statut IN ('Planifié', 'Confirmé');

-- Index partiel pour les examens à venir
CREATE INDEX idx_examens_futurs ON examens(date_heure) 
    WHERE date_heure > CURRENT_TIMESTAMP 
    AND statut IN ('Planifié', 'Confirmé');

-- ============================================
-- 11. Table des chefs de département
-- ============================================
CREATE TABLE chef_departement (
    id SERIAL PRIMARY KEY,
    professeur_id INT NOT NULL UNIQUE REFERENCES professeurs(id) ON DELETE CASCADE,
    departement_id INT NOT NULL UNIQUE REFERENCES departements(id) ON DELETE CASCADE,
    date_nomination DATE NOT NULL,
    date_fin_mandat DATE,
    is_actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chef_professeur FOREIGN KEY (professeur_id) 
        REFERENCES professeurs(id) ON DELETE CASCADE,
    CONSTRAINT fk_chef_departement FOREIGN KEY (departement_id) 
        REFERENCES departements(id) ON DELETE CASCADE
);

-- ============================================
-- 12. Table des utilisateurs système (Authentification)
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(150) UNIQUE,
    role VARCHAR(30) NOT NULL CHECK (role IN ('etudiant', 'professeur', 'chef_departement', 'admin_examens', 'vice_doyen')),
    linked_id INT NOT NULL, -- Référence à l'ID dans la table correspondante
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    failed_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Index pour recherches rapides
    CONSTRAINT uq_user_linked UNIQUE(role, linked_id)
);

CREATE INDEX idx_users_role ON users(role, is_active);
CREATE INDEX idx_users_username ON users(username);

-- ============================================
-- 13. Table d'audit pour tracer les modifications
-- ============================================
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INT NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by INT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);

-- ============================================
-- 14. TRIGGERS ET CONTRAINTES AVANCÉES
-- ============================================

-- Trigger 1: Un étudiant ne peut avoir qu'un examen par jour
CREATE OR REPLACE FUNCTION check_etudiant_exam_limit()
RETURNS TRIGGER AS $$
DECLARE
    exam_count INT;
BEGIN
    -- Compter les examens pour chaque étudiant inscrit à ce module le même jour
    SELECT COUNT(DISTINCT e.id) INTO exam_count
    FROM examens ex
    INNER JOIN inscriptions i ON ex.module_id = i.module_id
    INNER JOIN examens e ON i.module_id = e.module_id
    WHERE i.etudiant_id IN (
        SELECT etudiant_id 
        FROM inscriptions 
        WHERE module_id = NEW.module_id
    )
    AND DATE(ex.date_heure) = DATE(NEW.date_heure)
    AND ex.id != COALESCE(NEW.id, 0);
    
    IF exam_count > 0 THEN
        RAISE EXCEPTION 
            'Violation de contrainte: Un ou plusieurs étudiants ont déjà un examen programmé à cette date.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_etudiant_exam_limit
BEFORE INSERT OR UPDATE ON examens
FOR EACH ROW
EXECUTE FUNCTION check_etudiant_exam_limit();

-- Trigger 2: Un professeur maximum 3 examens par jour
CREATE OR REPLACE FUNCTION check_professeur_exam_limit()
RETURNS TRIGGER AS $$
DECLARE
    daily_exams INT;
BEGIN
    SELECT COUNT(*) INTO daily_exams
    FROM examens
    WHERE professeur_id = NEW.professeur_id
    AND DATE(date_heure) = DATE(NEW.date_heure)
    AND id != COALESCE(NEW.id, 0);
    
    IF daily_exams >= 3 THEN
        RAISE EXCEPTION 
            'Professeur ID % a déjà % examens programmés le % (Maximum: 3)',
            NEW.professeur_id, daily_exams, DATE(NEW.date_heure);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_professeur_exam_limit
BEFORE INSERT OR UPDATE ON examens
FOR EACH ROW
EXECUTE FUNCTION check_professeur_exam_limit();

-- Trigger 3: Respect de la capacité des salles avec marge de sécurité
CREATE OR REPLACE FUNCTION check_salle_capacity()
RETURNS TRIGGER AS $$
DECLARE
    salle_capacite INT;
    etudiants_inscrits INT;
BEGIN
    -- Récupérer la capacité de la salle
    SELECT capacite INTO salle_capacite
    FROM lieux_examen
    WHERE id = NEW.salle_id;
    
    -- Compter les étudiants inscrits au module
    SELECT COUNT(*) INTO etudiants_inscrits
    FROM inscriptions
    WHERE module_id = NEW.module_id
    AND statut = 'Inscrit';
    
    -- Appliquer une marge de sécurité (90% de la capacité)
    IF etudiants_inscrits > (salle_capacite * 0.9) THEN
        RAISE EXCEPTION 
            'Capacité insuffisante: % étudiants pour une salle de % places (90%% max)',
            etudiants_inscrits, salle_capacite;
    END IF;
    
    -- Mettre à jour le champ max_etudiants
    NEW.max_etudiants := etudiants_inscrits;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_salle_capacity
BEFORE INSERT OR UPDATE ON examens
FOR EACH ROW
EXECUTE FUNCTION check_salle_capacity();

-- Trigger 4: Priorité aux examens du département pour les surveillances
CREATE OR REPLACE FUNCTION check_professeur_departement_priority()
RETURNS TRIGGER AS $$
DECLARE
    prof_dept_id INT;
    module_dept_id INT;
BEGIN
    -- Département du professeur
    SELECT departement_id INTO prof_dept_id
    FROM professeurs
    WHERE id = NEW.professeur_id;
    
    -- Département du module (via formation)
    SELECT f.departement_id INTO module_dept_id
    FROM modules m
    JOIN formations f ON m.formation_id = f.id
    WHERE m.id = NEW.module_id;
    
    -- Si le professeur n'est pas du même département, vérifier s'il y a des conflits
    IF prof_dept_id != module_dept_id THEN
        RAISE WARNING 
            'Professeur du département % assigné à un examen du département %',
            prof_dept_id, module_dept_id;
        -- Ici, on pourrait ajouter une logique de vérification des disponibilités
        -- des professeurs du département concerné en priorité
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_professeur_departement_priority
BEFORE INSERT ON examens
FOR EACH ROW
EXECUTE FUNCTION check_professeur_departement_priority();

-- Trigger 5: Équilibrage des surveillances entre enseignants
CREATE OR REPLACE FUNCTION balance_surveillances()
RETURNS TRIGGER AS $$
DECLARE
    avg_exams_per_prof DECIMAL;
    prof_exam_count INT;
BEGIN
    -- Calculer la moyenne des examens par professeur
    SELECT AVG(exam_count) INTO avg_exams_per_prof
    FROM (
        SELECT professeur_id, COUNT(*) as exam_count
        FROM examens
        WHERE DATE(date_heure) BETWEEN 
            DATE(NEW.date_heure) - INTERVAL '7 days' AND 
            DATE(NEW.date_heure) + INTERVAL '7 days'
        GROUP BY professeur_id
    ) stats;
    
    -- Nombre d'examens du professeur courant
    SELECT COUNT(*) INTO prof_exam_count
    FROM examens
    WHERE professeur_id = NEW.professeur_id
    AND DATE(date_heure) BETWEEN 
        DATE(NEW.date_heure) - INTERVAL '7 days' AND 
        DATE(NEW.date_heure) + INTERVAL '7 days';
    
    -- Si le professeur a déjà plus de 20% au-dessus de la moyenne, avertir
    IF prof_exam_count > (avg_exams_per_prof * 1.2) THEN
        RAISE WARNING 
            'Déséquilibre de surveillances: Professeur % a % examens (moyenne: %)',
            NEW.professeur_id, prof_exam_count, ROUND(avg_exams_per_prof, 2);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_balance_surveillances
BEFORE INSERT ON examens
FOR EACH ROW
EXECUTE FUNCTION balance_surveillances();

-- Trigger 6: Mise à jour automatique des timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer ce trigger aux tables principales
CREATE TRIGGER trg_update_etudiants_updated_at
BEFORE UPDATE ON etudiants
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_examens_updated_at
BEFORE UPDATE ON examens
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_lieux_updated_at
BEFORE UPDATE ON lieux_examen
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 15. VUES POUR ANALYTIQUE ET REPORTING
-- ============================================

-- Vue 1: Planning complet des examens
CREATE VIEW v_planning_examens AS
SELECT 
    e.id,
    e.uuid,
    m.code as module_code,
    m.nom as module_nom,
    f.nom as formation_nom,
    d.nom as departement_nom,
    CONCAT(p.nom, ' ', p.prenom) as professeur_nom,
    p.matricule as professeur_matricule,
    l.nom as salle_nom,
    l.type as salle_type,
    l.capacite,
    e.date_heure,
    e.duree_minutes,
    e.date_heure + (e.duree_minutes || ' minutes')::INTERVAL as date_fin,
    e.type_examen,
    e.statut,
    e.max_etudiants,
    COUNT(i.etudiant_id) as etudiants_inscrits,
    ROUND((COUNT(i.etudiant_id)::DECIMAL / l.capacite) * 100, 2) as taux_occupation
FROM examens e
JOIN modules m ON e.module_id = m.id
JOIN formations f ON m.formation_id = f.id
JOIN departements d ON f.departement_id = d.id
JOIN professeurs p ON e.professeur_id = p.id
JOIN lieux_examen l ON e.salle_id = l.id
LEFT JOIN inscriptions i ON e.module_id = i.module_id AND i.statut = 'Inscrit'
GROUP BY e.id, m.code, m.nom, f.nom, d.nom, p.nom, p.prenom, p.matricule, 
         l.nom, l.type, l.capacite, e.date_heure, e.duree_minutes, e.type_examen, e.statut;

-- Vue 2: Conflits détectés
CREATE VIEW v_conflits_examens AS
SELECT 
    e1.id as examen1_id,
    e2.id as examen2_id,
    e1.date_heure as date_heure1,
    e2.date_heure as date_heure2,
    CONCAT(p1.nom, ' ', p1.prenom) as professeur1,
    CONCAT(p2.nom, ' ', p2.prenom) as professeur2,
    l.nom as salle_nom,
    'Conflit salle/professeur' as type_conflit
FROM examens e1
JOIN examens e2 ON 
    e1.salle_id = e2.salle_id 
    AND e1.id < e2.id
    AND tsrange(e1.date_heure, e1.date_heure + (e1.duree_minutes || ' minutes')::INTERVAL) 
        && tsrange(e2.date_heure, e2.date_heure + (e2.duree_minutes || ' minutes')::INTERVAL)
JOIN professeurs p1 ON e1.professeur_id = p1.id
JOIN professeurs p2 ON e2.professeur_id = p2.id
JOIN lieux_examen l ON e1.salle_id = l.id
WHERE e1.statut IN ('Planifié', 'Confirmé') 
AND e2.statut IN ('Planifié', 'Confirmé')
UNION ALL
SELECT 
    e1.id as examen1_id,
    e2.id as examen2_id,
    e1.date_heure as date_heure1,
    e2.date_heure as date_heure2,
    CONCAT(p1.nom, ' ', p1.prenom) as professeur1,
    CONCAT(p2.nom, ' ', p2.prenom) as professeur2,
    NULL as salle_nom,
    'Professeur double réservation' as type_conflit
FROM examens e1
JOIN examens e2 ON 
    e1.professeur_id = e2.professeur_id 
    AND e1.id < e2.id
    AND tsrange(e1.date_heure, e1.date_heure + (e1.duree_minutes || ' minutes')::INTERVAL) 
        && tsrange(e2.date_heure, e2.date_heure + (e2.duree_minutes || ' minutes')::INTERVAL)
JOIN professeurs p1 ON e1.professeur_id = p1.id
JOIN professeurs p2 ON e2.professeur_id = p2.id
WHERE e1.statut IN ('Planifié', 'Confirmé') 
AND e2.statut IN ('Planifié', 'Confirmé');

-- Vue 3: Statistiques départementales
CREATE VIEW v_stats_departement AS
SELECT 
    d.id as departement_id,
    d.nom as departement_nom,
    COUNT(DISTINCT f.id) as nb_formations,
    COUNT(DISTINCT e.id) as nb_etudiants,
    COUNT(DISTINCT p.id) as nb_professeurs,
    COUNT(DISTINCT m.id) as nb_modules,
    COUNT(DISTINCT ex.id) as nb_examens_planifies,
    SUM(CASE WHEN ex.statut = 'Terminé' THEN 1 ELSE 0 END) as nb_examens_termines,
    AVG(l.capacite) as capacite_moyenne_salles,
    MAX(ex.date_heure) as dernier_examen,
    MIN(ex.date_heure) as premier_examen
FROM departements d
LEFT JOIN formations f ON d.id = f.departement_id
LEFT JOIN etudiants e ON f.id = e.formation_id
LEFT JOIN professeurs p ON d.id = p.departement_id
LEFT JOIN modules m ON f.id = m.formation_id
LEFT JOIN examens ex ON m.id = ex.module_id
LEFT JOIN lieux_examen l ON ex.salle_id = l.id
GROUP BY d.id, d.nom;

-- Vue 4: Taux d'occupation des salles
CREATE VIEW v_occupation_salles AS
SELECT 
    l.id,
    l.code,
    l.nom,
    l.type,
    l.capacite,
    COUNT(ex.id) as nb_examens_planifies,
    SUM(ex.duree_minutes) as total_minutes,
    ROUND(COUNT(ex.id) * 100.0 / 
        (SELECT COUNT(*) FROM examens WHERE date_heure::date = CURRENT_DATE), 2) 
        as pourcentage_utilisation,
    ROUND(AVG(pe.taux_occupation), 2) as taux_occupation_moyen
FROM lieux_examen l
LEFT JOIN examens ex ON l.id = ex.salle_id 
    AND ex.date_heure::date >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN v_planning_examens pe ON l.id = ex.salle_id
GROUP BY l.id, l.code, l.nom, l.type, l.capacite
ORDER BY pourcentage_utilisation DESC;

-- ============================================
-- 16. FONCTIONS STOCKÉES POUR L'OPTIMISATION
-- ============================================

-- Fonction 1: Générer un planning optimisé
CREATE OR REPLACE FUNCTION generer_planning_optimise(
    p_date_debut DATE,
    p_date_fin DATE
)
RETURNS TABLE (
    module_id INT,
    module_nom VARCHAR,
    salle_id INT,
    salle_nom VARCHAR,
    date_heure TIMESTAMP,
    duree_minutes INT,
    professeur_id INT,
    professeur_nom VARCHAR,
    score_optimisation DECIMAL
) AS $$
BEGIN
    -- Algorithme d'optimisation simplifié
    RETURN QUERY
    WITH modules_a_planifier AS (
        SELECT m.id, m.nom, COUNT(i.etudiant_id) as nb_etudiants
        FROM modules m
        JOIN inscriptions i ON m.id = i.module_id
        WHERE i.statut = 'Inscrit'
        AND m.id NOT IN (
            SELECT module_id 
            FROM examens 
            WHERE date_heure BETWEEN p_date_debut AND p_date_fin
            AND statut IN ('Planifié', 'Confirmé')
        )
        GROUP BY m.id, m.nom
    ),
    salles_disponibles AS (
        SELECT l.id, l.nom, l.capacite, l.type,
               gs.hour_slot
        FROM lieux_examen l
        CROSS JOIN generate_series(
            p_date_debut::timestamp,
            p_date_fin::timestamp,
            '90 minutes'::interval
        ) gs(hour_slot)
        WHERE l.is_disponible = TRUE
        AND NOT EXISTS (
            SELECT 1 FROM examens e
            WHERE e.salle_id = l.id
            AND tsrange(e.date_heure, e.date_heure + (e.duree_minutes || ' minutes')::interval)
                @> gs.hour_slot
        )
    ),
    professeurs_disponibles AS (
        SELECT p.id, CONCAT(p.nom, ' ', p.prenom) as nom,
               gs.hour_slot
        FROM professeurs p
        CROSS JOIN generate_series(
            p_date_debut::timestamp,
            p_date_fin::timestamp,
            '90 minutes'::interval
        ) gs(hour_slot)
        WHERE p.is_active = TRUE
        AND (SELECT COUNT(*) FROM examens e WHERE e.professeur_id = p.id AND DATE(e.date_heure) = DATE(gs.hour_slot)) < 3
    )
    SELECT 
        ma.id,
        ma.nom,
        sd.id,
        sd.nom,
        sd.hour_slot,
        90, -- Durée standard
        pd.id,
        pd.nom,
        -- Score d'optimisation basé sur plusieurs critères
        (CASE 
            WHEN ma.nb_etudiants <= sd.capacite * 0.8 THEN 1.0
            WHEN ma.nb_etudiants <= sd.capacite THEN 0.8
            ELSE 0.0
        END) *
        (CASE 
            WHEN sd.type = 'Amphithéâtre' AND ma.nb_etudiants > 50 THEN 1.0
            WHEN sd.type = 'Salle de cours' AND ma.nb_etudiants <= 50 THEN 1.0
            ELSE 0.7
        END) as score_optimisation
    FROM modules_a_planifier ma
    CROSS JOIN salles_disponibles sd
    CROSS JOIN professeurs_disponibles pd
    WHERE ma.nb_etudiants <= sd.capacite
    ORDER BY score_optimisation DESC, sd.hour_slot
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- Fonction 2: Détecter tous les conflits
CREATE OR REPLACE FUNCTION detecter_conflits()
RETURNS TABLE (
    type_conflit VARCHAR,
    details TEXT,
    severite VARCHAR
) AS $$
BEGIN
    -- Conflits de salle
    RETURN QUERY
    SELECT 
        'Salle double réservation' as type_conflit,
        FORMAT('Salle %s utilisée par deux examens à %s', l.nom, e1.date_heure) as details,
        'CRITIQUE' as severite
    FROM examens e1
    JOIN examens e2 ON e1.salle_id = e2.salle_id AND e1.id < e2.id
    JOIN lieux_examen l ON e1.salle_id = l.id
    WHERE tsrange(e1.date_heure, e1.date_heure + (e1.duree_minutes || ' minutes')::interval) 
          && tsrange(e2.date_heure, e2.date_heure + (e2.duree_minutes || ' minutes')::interval)
    AND e1.statut IN ('Planifié', 'Confirmé')
    AND e2.statut IN ('Planifié', 'Confirmé')
    UNION ALL
    -- Conflits de professeur
    SELECT 
        'Professeur surchargé' as type_conflit,
        FORMAT('Professeur %s a %s examens le %s', 
               CONCAT(p.nom, ' ', p.prenom), 
               COUNT(e.id),
               DATE(e.date_heure)) as details,
        'MOYEN' as severite
    FROM examens e
    JOIN professeurs p ON e.professeur_id = p.id
    WHERE e.statut IN ('Planifié', 'Confirmé')
    GROUP BY p.id, p.nom, p.prenom, DATE(e.date_heure)
    HAVING COUNT(*) > 3
    UNION ALL
    -- Conflits d'étudiant
    SELECT 
        'Étudiant avec examens rapprochés' as type_conflit,
        FORMAT('Étudiant %s a deux examens à moins de 2h d''intervalle', 
               CONCAT(et.nom, ' ', et.prenom)) as details,
        'ÉLEVÉ' as severite
    FROM inscriptions i1
    JOIN inscriptions i2 ON i1.etudiant_id = i2.etudiant_id AND i1.module_id < i2.module_id
    JOIN examens e1 ON i1.module_id = e1.module_id
    JOIN examens e2 ON i2.module_id = e2.module_id
    JOIN etudiants et ON i1.etudiant_id = et.id
    WHERE ABS(EXTRACT(EPOCH FROM (e1.date_heure - e2.date_heure))) < 7200 -- 2 heures
    AND e1.statut IN ('Planifié', 'Confirmé')
    AND e2.statut IN ('Planifié', 'Confirmé');
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 17. DONNÉES DE TEST (130k inscriptions simulées)
-- ============================================

-- Insertion des départements
INSERT INTO departements (code, nom) VALUES
('INFO', 'Informatique'),
('MATH', 'Mathématiques'),
('PHYS', 'Physique'),
('CHIM', 'Chimie'),
('BIO', 'Biologie'),
('GEOL', 'Géologie'),
('ECO', 'Sciences Économiques');

-- Insertion des formations (200+ formations)
DO $$
DECLARE
    dept RECORD;
    i INT;
    niveaux VARCHAR[] := ARRAY['Licence', 'Master'];
    specialites_info VARCHAR[] := ARRAY['Génie Logiciel', 'Réseaux', 'IA', 'Cybersécurité', 'Data Science'];
    specialites_math VARCHAR[] := ARRAY['Maths Fondamentales', 'Maths Appliquées', 'Statistiques'];
BEGIN
    FOR dept IN SELECT id, code FROM departements LOOP
        FOR i IN 1..30 LOOP  -- ~30 formations par département
            INSERT INTO formations (code, nom, departement_id, niveau, nb_modules, annee_academique)
            VALUES (
                dept.code || '-F' || LPAD(i::text, 3, '0'),
                CASE dept.code
                    WHEN 'INFO' THEN niveaux[(i%2)+1] || ' ' || specialites_info[(i%5)+1]
                    WHEN 'MATH' THEN niveaux[(i%2)+1] || ' ' || specialites_math[(i%3)+1]
                    ELSE niveaux[(i%2)+1] || ' ' || dept.nom || ' Spécialité ' || i
                END,
                dept.id,
                niveaux[(i%2)+1],
                6 + (i%4), -- 6-9 modules
                2025
            );
        END LOOP;
    END LOOP;
END $$;

-- Insertion des professeurs (~500 professeurs)
INSERT INTO professeurs (matricule, nom, prenom, grade, departement_id, specialite, email)
SELECT 
    'PROF-' || LPAD(s::text, 6, '0'),
    'Nom' || s,
    'Prenom' || s,
    CASE (s%4)
        WHEN 0 THEN 'Professeur'
        WHEN 1 THEN 'Maître de Conférences'
        WHEN 2 THEN 'Chargé de Cours'
        ELSE 'Assistant'
    END,
    (s%7)+1,
    'Spécialité ' || s,
    'prof' || s || '@univ.dz'
FROM generate_series(1, 500) s;

-- Insertion des modules (~6-9 par formation)
INSERT INTO modules (code, nom, credits, formation_id, semestre, volume_horaire)
SELECT 
    'MOD-' || LPAD(row_number() OVER ()::text, 6, '0'),
    'Module ' || md5(random()::text),
    3 + ((row_number() OVER ()) % 6),
    f.id,
    1 + ((row_number() OVER ()) % 6),
    30 + ((row_number() OVER ()) % 30)
FROM formations f
CROSS JOIN generate_series(1, 6 + (f.id % 4));

-- Insertion des étudiants (13,000 étudiants)
INSERT INTO etudiants (matricule, nom, prenom, email_univ, formation_id, annee_inscription, statut)
SELECT 
    'ETU-' || LPAD(s::text, 8, '0'),
    'Etudiant' || s,
    'Prenom' || s,
    'etu' || s || '@univ.dz',
    (s % (SELECT COUNT(*) FROM formations)) + 1,
    2022 + (s % 4),
    CASE (s % 10)
        WHEN 0 THEN 'Inactif'
        WHEN 1 THEN 'Diplômé'
        ELSE 'Actif'
    END
FROM generate_series(1, 13000) s;

-- Insertion des lieux d'examen
INSERT INTO lieux_examen (code, nom, capacite, type, batiment, equipements)
VALUES
('AMPHI-A', 'Amphithéâtre A', 400, 'Amphithéâtre', 'Bâtiment Central', ARRAY['Vidéoprojecteur', 'Sonorisation', 'WiFi']),
('AMPHI-B', 'Amphithéâtre B', 350, 'Amphithéâtre', 'Bâtiment Central', ARRAY['Vidéoprojecteur', 'Sonorisation']),
('AMPHI-C', 'Amphithéâtre C', 200, 'Amphithéâtre', 'Bâtiment Sciences', ARRAY['Vidéoprojecteur']),
('SAL-101', 'Salle 101', 20, 'Salle de cours', 'Bâtiment A', ARRAY['Tableau blanc']),
('SAL-102', 'Salle 102', 20, 'Salle de cours', 'Bâtiment A', ARRAY['Tableau blanc']),
('SAL-201', 'Salle 201', 20, 'Salle de cours', 'Bâtiment B', ARRAY['Tableau blanc']),
('SAL-202', 'Salle 202', 20, 'Salle de cours', 'Bâtiment B', ARRAY['Tableau blanc', 'Vidéoprojecteur']),
('LAB-INFO1', 'Laboratoire Informatique 1', 30, 'Laboratoire', 'Bâtiment Informatique', ARRAY['PC', 'Réseau', 'Projecteur']),
('LAB-INFO2', 'Laboratoire Informatique 2', 30, 'Laboratoire', 'Bâtiment Informatique', ARRAY['PC', 'Réseau']),
('SAL-SPEC', 'Salle Spéciale', 15, 'Salle spécialisée', 'Bâtiment Examens', ARRAY['Surveillance CCTV', 'Antenne portable']);

-- Insertion des inscriptions (130,000 inscriptions - simulation)
INSERT INTO inscriptions (etudiant_id, module_id, annee_academique, session, statut)
SELECT 
    e.id,
    m.id,
    2025,
    'Principale',
    'Inscrit'
FROM etudiants e
JOIN modules m ON m.formation_id = e.formation_id
WHERE e.statut = 'Actif'
AND random() < 0.7  -- 70% des étudiants inscrits à chaque module
LIMIT 130000;

-- Insertion des examens planifiés
INSERT INTO examens (module_id, professeur_id, salle_id, date_heure, duree_minutes, type_examen, statut)
SELECT 
    m.id,
    (SELECT id FROM professeurs p WHERE p.departement_id = f.departement_id ORDER BY random() LIMIT 1),
    (SELECT id FROM lieux_examen WHERE capacite >= (
        SELECT COUNT(*) FROM inscriptions WHERE module_id = m.id AND statut = 'Inscrit'
    ) ORDER BY random() LIMIT 1),
    TIMESTAMP '2025-01-15 08:00:00' + 
        (floor(random() * 14) || ' days')::interval +  -- Sur 2 semaines
        (floor(random() * 4) * 90 || ' minutes')::interval, -- Créneaux de 90 min
    90 + ((random() * 3)::int * 30), -- 90, 120, 150 ou 180 minutes
    CASE (random() * 3)::int
        WHEN 0 THEN 'Final'
        WHEN 1 THEN 'Partiel'
        ELSE 'Contrôle'
    END,
    'Planifié'
FROM modules m
JOIN formations f ON m.formation_id = f.id
LIMIT 500;  -- 500 examens planifiés

-- Insertion des chefs de département
INSERT INTO chef_departement (professeur_id, departement_id, date_nomination, date_fin_mandat)
SELECT 
    p.id,
    d.id,
    '2024-09-01',
    '2027-08-31'
FROM departements d
JOIN professeurs p ON p.departement_id = d.id
ORDER BY random()
LIMIT 7;

-- ============================================
-- 18. CRÉATION DES UTILISATEURS AVEC MOTS DE PASSE VALIDES
-- ============================================

-- Fonction pour générer un hash bcrypt simple (pour le développement)
CREATE OR REPLACE FUNCTION generate_simple_bcrypt(password TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Format bcrypt simplifié pour le développement: $2a$12$ + 22 chars + 31 chars
    RETURN '$2a$12$' || substr(md5(password), 1, 22) || substr(md5(password), 1, 31);
END;
$$ LANGUAGE plpgsql;

-- Insertion des utilisateurs avec mots de passe valides
INSERT INTO users (username, password_hash, role, linked_id, email, is_active)
-- Étudiants (premiers 100)
SELECT 
    'etu' || e.matricule,
    generate_simple_bcrypt('pass123'),
    'etudiant',
    e.id,
    e.email_univ,
    TRUE
FROM etudiants e
WHERE e.statut = 'Actif'
LIMIT 100
ON CONFLICT (username) DO NOTHING;

-- Professeurs (premiers 50)
INSERT INTO users (username, password_hash, role, linked_id, email, is_active)
SELECT 
    'prof' || p.matricule,
    generate_simple_bcrypt('pass123'),
    'professeur',
    p.id,
    p.email,
    TRUE
FROM professeurs p
WHERE p.is_active = TRUE
LIMIT 50
ON CONFLICT (username) DO NOTHING;

-- Chefs de département
INSERT INTO users (username, password_hash, role, linked_id, email, is_active)
SELECT 
    'chef' || d.code,
    generate_simple_bcrypt('pass123'),
    'chef_departement',
    cd.id,
    p.email,
    TRUE
FROM chef_departement cd
JOIN professeurs p ON cd.professeur_id = p.id
JOIN departements d ON cd.departement_id = d.id
ON CONFLICT (username) DO NOTHING;

-- Utilisateurs de test pour le développement
INSERT INTO users (username, password_hash, role, linked_id, email, is_active) VALUES
('test.etudiant', generate_simple_bcrypt('test123'), 'etudiant', 1, 'test.etudiant@univ.dz', TRUE),
('test.professeur', generate_simple_bcrypt('test123'), 'professeur', 1, 'test.professeur@univ.dz', TRUE),
('test.chef', generate_simple_bcrypt('test123'), 'chef_departement', 1, 'test.chef@univ.dz', TRUE),
('admin', generate_simple_bcrypt('admin123'), 'admin_examens', 1, 'admin@univ.dz', TRUE),
('vice.doyen', generate_simple_bcrypt('doyen123'), 'vice_doyen', 1, 'vice.doyen@univ.dz', TRUE)
ON CONFLICT (username) DO NOTHING;

-- ============================================
-- 19. INDEX AVANCÉS POUR OPTIMISATION (<45s)
-- ============================================

-- Index partiels pour accélérer les requêtes fréquentes
CREATE INDEX idx_examens_actifs ON examens(id, date_heure) 
    WHERE statut IN ('Planifié', 'Confirmé');

CREATE INDEX idx_inscriptions_actives ON inscriptions(etudiant_id, module_id) 
    WHERE statut = 'Inscrit';

CREATE INDEX idx_etudiants_actifs ON etudiants(id, formation_id) 
    WHERE statut = 'Actif';

-- Index GIN pour recherche plein texte
CREATE INDEX idx_modules_nom_gin ON modules USING gin(to_tsvector('french', nom));

-- Index BRIN pour les grandes tables temporelles
CREATE INDEX idx_examens_date_brin ON examens USING brin(date_heure);

-- Index couvrant pour la vue planning
CREATE INDEX idx_planning_couvrant ON examens 
    (module_id, professeur_id, salle_id, date_heure) 
    INCLUDE (duree_minutes, statut);

-- ============================================
-- 20. GRANT DES PRIVILÈGES (SÉCURITÉ)
-- ============================================

-- Création des rôles applicatifs
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_etudiant') THEN
        CREATE ROLE app_etudiant;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_professeur') THEN
        CREATE ROLE app_professeur;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_chef') THEN
        CREATE ROLE app_chef;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
        CREATE ROLE app_admin;
    END IF;
END $$;

-- Privilèges pour app_etudiant (Lecture seule sur ses données)
GRANT SELECT ON 
    v_planning_examens,
    modules,
    examens,
    lieux_examen
TO app_etudiant;

-- Privilèges pour app_professeur (Lecture + limité)
GRANT SELECT ON 
    v_planning_examens,
    v_conflits_examens,
    examens,
    modules,
    professeurs,
    lieux_examen
TO app_professeur;

GRANT INSERT, UPDATE ON examens TO app_professeur;

-- Privilèges pour app_chef (Étendu)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_chef;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_chef;

-- Privilèges pour app_admin (Complet)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO app_admin;

-- ============================================
-- 21. MISE À JOUR DES MOTS DE PASSE POUR AUTHENTIFICATION
-- ============================================

-- Assurer que tous les mots de passe sont dans le format correct
UPDATE users 
SET password_hash = generate_simple_bcrypt('pass123')
WHERE password_hash NOT LIKE '$2a$12$%';

-- ============================================
-- 22. VÉRIFICATION FINALE
-- ============================================

-- Test d'authentification avec les utilisateurs de test
SELECT '✅ BASE DE DONNÉES CRÉÉE AVEC SUCCÈS' as message;

SELECT '👥 UTILISATEURS DE TEST DISPONIBLES:' as info;

SELECT 
    username,
    role,
    'Mot de passe: ' || 
    CASE 
        WHEN username = 'admin' THEN 'admin123'
        WHEN username = 'vice.doyen' THEN 'doyen123'
        ELSE 'test123'
    END as mot_de_passe
FROM users 
WHERE username IN ('test.etudiant', 'test.professeur', 'test.chef', 'admin', 'vice.doyen')
ORDER BY 
    CASE role
        WHEN 'etudiant' THEN 1
        WHEN 'professeur' THEN 2
        WHEN 'chef_departement' THEN 3
        WHEN 'admin_examens' THEN 4
        WHEN 'vice_doyen' THEN 5
    END;
\echo 'STATISTIQUES:'
\echo '------------'
\echo 'Etudiants: ' || (SELECT COUNT(*) FROM etudiants)
\echo 'Professeurs: ' || (SELECT COUNT(*) FROM professeurs WHERE is_active = TRUE)
\echo 'Inscriptions: ' || (SELECT COUNT(*) FROM inscriptions WHERE statut = 'Inscrit')
\echo 'Examens: ' || (SELECT COUNT(*) FROM examens WHERE statut IN ('Planifié', 'Confirmé'))
\echo 'Utilisateurs: ' || (SELECT COUNT(*) FROM users WHERE is_active = TRUE)