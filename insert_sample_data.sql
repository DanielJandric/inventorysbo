-- Script pour insérer des données d'exemple dans la collection BONVIN
-- À exécuter APRÈS avoir créé la table avec create_database_schema.sql

-- Insérer des exemples de voitures
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, for_sale) VALUES
('Ferrari 488 GTB', 'Voitures', 'Available', 2022, 'Excellent', 'Ferrari 488 GTB en parfait état, entretien complet, historique certifié. Couleur rouge Corsa, intérieur cuir noir.', 350000, 320000, true),
('Porsche 911 GT3 RS', 'Voitures', 'Available', 2023, 'Parfait', 'Porsche 911 GT3 RS, 525 ch, boîte PDK, pack Weissach. Couleur GT Silver Metallic.', 280000, 260000, false),
('Lamborghini Huracán', 'Voitures', 'Sold', 2021, 'Excellent', 'Lamborghini Huracán EVO RWD, 610 ch, boîte automatique. Vendu en 2023.', 0, 220000, false);

-- Insérer des exemples de montres
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, for_sale) VALUES
('Patek Philippe Nautilus 5711', 'Montres', 'Available', 2020, 'Parfait', 'Patek Philippe Nautilus 5711 en acier, cadran bleu, bracelet intégré. Référence 5711/1A-010.', 180000, 150000, true),
('Rolex Daytona 116500LN', 'Montres', 'Available', 2022, 'Excellent', 'Rolex Cosmograph Daytona en acier, cadran noir, lunette céramique. Référence 116500LN.', 45000, 38000, false),
('Audemars Piguet Royal Oak', 'Montres', 'Sold', 2019, 'Excellent', 'Audemars Piguet Royal Oak 15500ST, cadran bleu, bracelet acier. Vendu en 2022.', 0, 35000, false);

-- Insérer des exemples d'actions
INSERT INTO collection_items (name, category, status, stock_symbol, stock_quantity, stock_purchase_price, stock_exchange, current_price, description, for_sale) VALUES
('Nestlé SA', 'Actions', 'Available', 'NESN.SW', 100, 120.50, 'SWX', 125.80, 'Actions Nestlé SA, leader mondial de l''alimentation et des boissons.', false),
('Novartis AG', 'Actions', 'Available', 'NOVN.SW', 50, 85.20, 'SWX', 88.45, 'Actions Novartis AG, groupe pharmaceutique suisse.', false),
('Roche Holding AG', 'Actions', 'Available', 'ROG.SW', 75, 320.00, 'SWX', 315.20, 'Actions Roche Holding AG, leader de la santé.', false);

-- Insérer des exemples d'appartements
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, surface_m2, rental_income_chf, for_sale) VALUES
('Appartement de luxe Genève', 'Appartements / maison', 'Available', 2020, 'Excellent', 'Appartement de luxe au centre de Genève, 4.5 pièces, vue lac, parking privé.', 2800000, 2500000, 180, 12000, true),
('Villa Montreux', 'Appartements / maison', 'Available', 2018, 'Parfait', 'Villa moderne à Montreux, 6 pièces, jardin, vue montagne.', 3500000, 3200000, 250, 15000, false);

-- Insérer des exemples d'art
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, for_sale) VALUES
('Tableau contemporain', 'Art', 'Available', 2023, 'Parfait', 'Œuvre d''art contemporain, artiste suisse émergent, technique mixte sur toile.', 25000, 20000, true),
('Sculpture en bronze', 'Art', 'Available', 2021, 'Excellent', 'Sculpture en bronze, édition limitée, artiste reconnu internationalement.', 45000, 40000, false);

-- Insérer des exemples de vins
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, for_sale) VALUES
('Château Margaux 1982', 'Vins', 'Available', 1982, 'Excellent', 'Château Margaux 1982, millésime exceptionnel, conservation parfaite.', 15000, 12000, true),
('Domaine de la Romanée-Conti 1990', 'Vins', 'Available', 1990, 'Parfait', 'Domaine de la Romanée-Conti 1990, grand cru de Bourgogne.', 25000, 22000, false);

-- Insérer des exemples de bijoux
INSERT INTO collection_items (name, category, status, construction_year, condition, description, current_value, acquisition_price, for_sale) VALUES
('Diamant 5 carats', 'Bijoux', 'Available', 2022, 'Parfait', 'Diamant blanc 5 carats, pureté VVS1, couleur D, certificat GIA.', 180000, 160000, true),
('Bracelet Cartier', 'Bijoux', 'Available', 2021, 'Excellent', 'Bracelet Cartier Love en or jaune 18 carats, taille 17.', 8500, 7500, false);

-- Vérifier les données insérées
SELECT 
    category,
    COUNT(*) as nombre_items,
    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as disponibles,
    SUM(CASE WHEN status = 'Sold' THEN 1 ELSE 0 END) as vendus,
    SUM(CASE WHEN for_sale = true THEN 1 ELSE 0 END) as en_vente
FROM collection_items 
GROUP BY category 
ORDER BY category;

-- Afficher la valeur totale de la collection
SELECT 
    'Valeur totale de la collection' as description,
    SUM(COALESCE(current_value, 0)) as valeur_vente,
    SUM(COALESCE(acquisition_price, 0)) as valeur_acquisition,
    COUNT(*) as nombre_total_items
FROM collection_items 
WHERE status != 'Sold';

-- Message de confirmation
SELECT '✅ Données d''exemple insérées avec succès !' as status; 