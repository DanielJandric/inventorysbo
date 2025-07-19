#!/usr/bin/env python3
"""
Script pour remplacer "prix demandé" par "valeur actuelle" et asking_price par current_value
dans tous les fichiers du projet.
"""

import os
import re
from pathlib import Path

def update_file_content(file_path: str) -> bool:
    """Met à jour le contenu d'un fichier avec les remplacements nécessaires"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remplacements pour les textes en français
        content = re.sub(r'prix demandé', 'valeur actuelle', content, flags=re.IGNORECASE)
        content = re.sub(r'Prix demandé', 'Valeur actuelle', content)
        content = re.sub(r'PRIX DEMANDÉ', 'VALEUR ACTUELLE', content)
        
        # Remplacements pour les variables Python/JavaScript
        content = re.sub(r'\basking_price\b', 'current_value', content)
        content = re.sub(r'\bASKING_PRICE\b', 'CURRENT_VALUE', content)
        
        # Remplacements spécifiques pour les commentaires SQL
        content = re.sub(r'-- Prix demandé', '-- Valeur actuelle', content)
        content = re.sub(r'COMMENT ON COLUMN.*asking_price.*IS.*Prix de vente demandé', 
                        'COMMENT ON COLUMN collection_items.current_value IS \'Valeur actuelle de l\\\'objet en CHF\'', content)
        
        # Remplacements pour les labels HTML
        content = re.sub(r'<label[^>]*>Prix demandé[^<]*</label>', 
                        '<label class="block text-sm font-semibold mb-2">Valeur actuelle (CHF)</label>', content)
        
        # Si le contenu a changé, écrire le fichier
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Erreur lors de la modification de {file_path}: {e}")
        return False

def main():
    """Fonction principale"""
    # Fichiers à modifier
    files_to_update = [
        'app.py',
        'templates/index.html',
        'static/script.js',
        'static/analytics.js',
        'static/reports.js',
        'generate_embeddings_enhanced.py',
        'pdf_optimizer.py',
        'templates/portfolio_pdf.html',
        'templates/pdf_portfolio_optimized.html',
        'create_database_schema.sql',
        'insert_sample_data.sql',
        'README.md'
    ]
    
    updated_files = []
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_file_content(file_path):
                updated_files.append(file_path)
                print(f"✅ Modifié: {file_path}")
            else:
                print(f"⏭️  Aucun changement: {file_path}")
        else:
            print(f"❌ Fichier non trouvé: {file_path}")
    
    print(f"\n📊 Résumé: {len(updated_files)} fichiers modifiés sur {len(files_to_update)}")
    
    if updated_files:
        print("\n📝 Fichiers modifiés:")
        for file in updated_files:
            print(f"  - {file}")
    
    print("\n🔧 Prochaines étapes:")
    print("1. Exécuter le script SQL: rename_asking_price_to_current_value.sql")
    print("2. Vérifier que toutes les modifications sont correctes")
    print("3. Tester l'application")
    print("4. Commiter et pousser les changements")

if __name__ == "__main__":
    main() 