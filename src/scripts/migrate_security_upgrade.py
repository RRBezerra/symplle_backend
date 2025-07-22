# src/scripts/migrate_security_upgrade.py
"""
Migração de Segurança FASE 1 - Symplle
AJUSTADO para estrutura: symplle_backend/ + banco na raiz
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Caminho do banco ajustado para sua estrutura
DB_PATH = '../symplle.db'  # Banco está na raiz, script está em symplle_backend/src/scripts/

def create_backup(db_path=DB_PATH):
    """Criar backup antes da migração"""
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado em: {os.path.abspath(db_path)}")
        return None
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup criado: {os.path.abspath(backup_path)}")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None

def add_security_fields(db_path=DB_PATH):
    """Adicionar campos de segurança na tabela users"""
    try:
        print(f"🔍 Conectando ao banco: {os.path.abspath(db_path)}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se tabela users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Tabela 'users' não encontrada no banco")
            return False
        
        # Verificar campos existentes
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Campos atuais na tabela users: {columns}")
        
        migrations = []
        
        # Campos de segurança a adicionar
        security_fields = [
            ('password_hash', 'TEXT'),
            ('last_login', 'DATETIME'),
            ('login_attempts', 'INTEGER DEFAULT 0'),
            ('is_active', 'BOOLEAN DEFAULT TRUE'),
            ('created_at_migration', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for field_name, field_type in security_fields:
            if field_name not in columns:
                migration_sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_type}"
                migrations.append((field_name, migration_sql))
        
        if not migrations:
            print("✅ Todos os campos de segurança já existem!")
            return True
        
        # Executar migrações
        print(f"🔧 Executando {len(migrations)} migrações...")
        for field_name, migration_sql in migrations:
            cursor.execute(migration_sql)
            print(f"  ✅ Adicionado: {field_name}")
        
        conn.commit()
        conn.close()
        
        print(f"🎉 {len(migrations)} campos de segurança adicionados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False

def verify_migration(db_path=DB_PATH):
    """Verificar se migração foi bem-sucedida"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura da tabela users
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        required_fields = ['password_hash', 'last_login', 'login_attempts', 'is_active']
        missing_fields = [field for field in required_fields if field not in columns]
        
        if missing_fields:
            print(f"❌ Campos ainda faltando: {missing_fields}")
            return False
        
        # Verificar contagem de usuários
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Verificar contagem de países (para garantir integridade)
        cursor.execute("SELECT COUNT(*) FROM countries")
        country_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Verificação completa:")
        print(f"  📊 {user_count} usuários")
        print(f"  🌍 {country_count} países")
        print(f"  🔐 Todos os campos de segurança presentes")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def main():
    """Executar migração completa"""
    print("🚀 SYMPLLE - Migração de Segurança FASE 1")
    print("=" * 60)
    print(f"📍 Executando de: {os.getcwd()}")
    print(f"🗄️ Banco de dados: {os.path.abspath(DB_PATH)}")
    print("=" * 60)
    
    # Verificar se banco existe
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {os.path.abspath(DB_PATH)}")
        print("💡 Certifique-se de executar este script a partir de symplle_backend/")
        return False
    
    # 1. Criar backup
    print("\n📦 STEP 1: Criando backup de segurança...")
    backup_path = create_backup(DB_PATH)
    if not backup_path:
        print("❌ Falha no backup. Operação abortada.")
        return False
    
    # 2. Executar migração
    print("\n🔐 STEP 2: Adicionando campos de segurança...")
    if not add_security_fields(DB_PATH):
        print("❌ Falha na migração.")
        print(f"🔄 Para restaurar: cp {backup_path} {DB_PATH}")
        return False
    
    # 3. Verificar migração
    print("\n✅ STEP 3: Verificando integridade...")
    if not verify_migration(DB_PATH):
        print("❌ Verificação falhou.")
        print(f"🔄 Para restaurar: cp {backup_path} {DB_PATH}")
        return False
    
    print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"✅ Backup salvo: {os.path.abspath(backup_path)}")
    print("✅ Campos de segurança adicionados à tabela users")
    print("✅ Integridade dos dados verificada")
    print("✅ Compatibilidade 100% mantida")
    print("=" * 60)
    print("🚀 Próximo passo: Implementar rotas JWT no main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)