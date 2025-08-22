#!/usr/bin/env python3
"""
🔐 Script de vérification de sécurité
Vérifie que la clé OpenAI n'est pas exposée publiquement
"""

import os
import re
import sys

def check_for_exposed_keys():
    """Vérifie que les clés API ne sont pas hardcodées dans le code"""
    
    # Patterns à rechercher
    key_patterns = [
        r'sk-[a-zA-Z0-9]{48}',  # Clé OpenAI standard
        r'OPENAI_API_KEY\s*=\s*["\'][^"\']+["\']',  # Variable hardcodée
        r'openai\.api_key\s*=\s*["\'][^"\']+["\']',  # Assignment direct
    ]
    
    # Fichiers à vérifier
    files_to_check = [
        'flask_gpt5_integration_final.py',
        'gpt5_responses_final_with_helper.py',
        'gpt5_text_extractor_helper.py',
        'README.md',
        'render.yaml'
    ]
    
    issues_found = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in key_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        issues_found.append({
                            'file': file_path,
                            'pattern': pattern,
                            'matches': matches
                        })
    
    return issues_found

def check_gitignore():
    """Vérifie que .gitignore protège les fichiers sensibles"""
    
    required_entries = ['.env', '*.key', '.env.local', '.env.production']
    missing_entries = []
    
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            
        for entry in required_entries:
            if entry not in gitignore_content:
                missing_entries.append(entry)
    else:
        missing_entries = required_entries
    
    return missing_entries

def main():
    """Script principal de vérification"""
    
    print("🔐 VÉRIFICATION DE SÉCURITÉ GPT-5 API")
    print("=" * 50)
    
    # Vérifier les clés exposées
    print("\n1. 🔍 Vérification des clés exposées...")
    exposed_keys = check_for_exposed_keys()
    
    if exposed_keys:
        print("❌ PROBLÈMES DÉTECTÉS:")
        for issue in exposed_keys:
            print(f"   📁 Fichier: {issue['file']}")
            print(f"   🔑 Matches: {issue['matches']}")
        sys.exit(1)
    else:
        print("✅ Aucune clé exposée détectée")
    
    # Vérifier .gitignore
    print("\n2. 🛡️ Vérification de .gitignore...")
    missing_gitignore = check_gitignore()
    
    if missing_gitignore:
        print("⚠️ Entrées manquantes dans .gitignore:")
        for entry in missing_gitignore:
            print(f"   - {entry}")
    else:
        print("✅ .gitignore correctement configuré")
    
    # Vérifier les variables d'environnement
    print("\n3. 🌍 Vérification des variables d'environnement...")
    
    if os.getenv("OPENAI_API_KEY"):
        if os.getenv("OPENAI_API_KEY").startswith("sk-"):
            print("✅ OPENAI_API_KEY détectée et valide")
        else:
            print("⚠️ OPENAI_API_KEY détectée mais format invalide")
    else:
        print("⚠️ OPENAI_API_KEY non détectée (normal en production)")
    
    # Résumé
    print("\n🎯 RÉSUMÉ DE SÉCURITÉ")
    print("=" * 30)
    
    if not exposed_keys and not missing_gitignore:
        print("✅ SÉCURITÉ OK - Prêt pour le déploiement")
        print("\n🚀 Instructions pour Render:")
        print("1. Connecter votre repo GitHub à Render")
        print("2. Configurer OPENAI_API_KEY dans Environment Variables")
        print("3. Déployer - render.yaml sera utilisé automatiquement")
        return 0
    else:
        print("❌ PROBLÈMES DE SÉCURITÉ DÉTECTÉS")
        print("🔧 Corrigez les problèmes avant le déploiement")
        return 1

if __name__ == "__main__":
    sys.exit(main())
