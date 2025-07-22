# test_i18n_symplle.py
"""
Testes específicos para o sistema i18n do Symplle
Execute: python test_i18n_symplle.py
"""

import requests
import json
import sys
import os
from datetime import datetime

class SymplleI18nTester:
    """Tester específico para a implementação i18n do Symplle"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Detectar se main.py está em src/ ou raiz
        self.main_in_src = os.path.exists('src/main.py')
        if self.main_in_src:
            print("📁 Detectado: main.py em src/ - ajustando caminhos")
        else:
            print("📁 Detectado: main.py na raiz - usando caminhos padrão")
    
    def test_server_health(self):
        """Verifica se o servidor está rodando"""
        print("🔍 TESTANDO CONEXÃO COM SERVIDOR...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Servidor online: {data.get('data', {}).get('status', 'unknown')}")
                print(f"   Versão: {data.get('data', {}).get('version', 'N/A')}")
                print(f"   i18n: {'✅' if data.get('data', {}).get('i18n') else '❌'}")
                print(f"   Database: {data.get('data', {}).get('database', 'N/A')}")
                return True
            else:
                print(f"❌ Servidor respondeu com status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("   Certifique-se que o servidor está rodando: python main.py")
            return False
    
    def test_root_endpoint(self):
        """Testa endpoint raiz"""
        print("\n🔍 TESTANDO ENDPOINT RAIZ...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print("✅ Endpoint raiz funcionando")
                print(f"   Mensagem: {data.get('data', {}).get('message', data.get('message', 'N/A'))}")
                return True
            else:
                print(f"❌ Erro no endpoint raiz: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro no endpoint raiz: {e}")
            return False
    
    def test_i18n_availability(self):
        """Verifica se o sistema i18n está disponível"""
        print("\n🌍 VERIFICANDO DISPONIBILIDADE DO i18n...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/i18n/info")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Sistema i18n disponível e funcionando")
                    locale_data = data.get('data', {})
                    print(f"   Locale atual: {locale_data.get('current_locale', 'N/A')}")
                    
                    locales = locale_data.get('supported_locales', [])
                    print(f"   Locales suportados: {len(locales)}")
                    for locale in locales:
                        flag = locale.get('flag', '')
                        name = locale.get('name', locale.get('code', 'N/A'))
                        print(f"     {flag} {name}")
                    
                    return True
                else:
                    print("❌ Sistema i18n não está funcionando")
                    print(f"   Erro: {data.get('message', 'Desconhecido')}")
                    return False
            else:
                print(f"❌ Endpoint i18n não disponível: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao verificar i18n: {e}")
            return False
    
    def test_locale_changes(self):
        """Testa mudança de idiomas"""
        print("\n🔄 TESTANDO MUDANÇA DE IDIOMAS...")
        
        locales_to_test = [
            {'code': 'pt_BR', 'name': 'Português (Brasil)', 'flag': '🇧🇷'},
            {'code': 'en_US', 'name': 'English (US)', 'flag': '🇺🇸'},
            {'code': 'es_ES', 'name': 'Español (España)', 'flag': '🇪🇸'}
        ]
        
        success_count = 0
        
        for locale_info in locales_to_test:
            locale = locale_info['code']
            try:
                response = self.session.post(
                    f"{self.base_url}/api/i18n/change-locale",
                    json={'locale': locale}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        examples = data.get('data', {}).get('examples', {})
                        welcome = examples.get('welcome', 'N/A')
                        login = examples.get('login', 'N/A')
                        
                        print(f"✅ {locale_info['flag']} {locale}: Mudança bem-sucedida")
                        print(f"   Welcome: {welcome}")
                        print(f"   Login: {login}")
                        success_count += 1
                    else:
                        print(f"❌ {locale}: {data.get('message', 'Erro desconhecido')}")
                else:
                    print(f"❌ {locale}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {locale}: Erro na mudança - {e}")
        
        print(f"\n📊 Resultado: {success_count}/{len(locales_to_test)} idiomas funcionando")
        return success_count == len(locales_to_test)
    
    def test_i18n_demo(self):
        """Testa endpoint de demonstração"""
        print("\n🎭 TESTANDO DEMO i18n...")
        
        # Testar demo em diferentes idiomas
        for locale_info in [
            {'code': 'pt_BR', 'flag': '🇧🇷'},
            {'code': 'en_US', 'flag': '🇺🇸'},
            {'code': 'es_ES', 'flag': '🇪🇸'}
        ]:
            locale = locale_info['code']
            flag = locale_info['flag']
            
            # Mudar idioma primeiro
            self.session.post(
                f"{self.base_url}/api/i18n/change-locale",
                json={'locale': locale}
            )
            
            # Pegar demo
            try:
                response = self.session.get(f"{self.base_url}/api/i18n/demo")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        demo_data = data.get('data', {})
                        translations = demo_data.get('translations', {})
                        formatting = demo_data.get('formatting', {})
                        
                        print(f"\n📋 DEMO {flag} {locale}:")
                        print(f"   App: {translations.get('app_name', 'N/A')}")
                        print(f"   Welcome: {translations.get('welcome_message', 'N/A')}")
                        print(f"   Login: {translations.get('login_title', 'N/A')}")
                        print(f"   Data: {formatting.get('date_now', 'N/A')}")
                        print(f"   Moeda: {formatting.get('currency_example', 'N/A')}")
                    else:
                        print(f"❌ Demo {locale}: {data.get('message', 'Erro')}")
                else:
                    print(f"❌ Demo {locale}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Demo {locale}: {e}")
    
    def test_auth_endpoints_with_i18n(self):
        """Testa endpoints de autenticação com i18n"""
        print("\n🔐 TESTANDO AUTH COM i18n...")
        
        # Primeiro, mudar para português
        self.session.post(
            f"{self.base_url}/api/i18n/change-locale",
            json={'locale': 'pt_BR'}
        )
        
        # Teste 1: Login inválido (deve retornar erro em português)
        print("🧪 Testando login inválido...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={'email': 'invalido@test.com', 'password': 'senhaerrada'}
            )
            
            if response.status_code == 401:
                data = response.json()
                message = data.get('message', 'N/A')
                print(f"✅ Login inválido: {message}")
            else:
                print(f"⚠️  Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro no teste de login: {e}")
        
        # Teste 2: Campos obrigatórios (deve retornar erro em português)
        print("\n🧪 Testando campos obrigatórios...")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={'email': '', 'password': ''}
            )
            
            if response.status_code == 400:
                data = response.json()
                message = data.get('message', 'N/A')
                print(f"✅ Campos obrigatórios: {message}")
            else:
                print(f"⚠️  Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro no teste de campos: {e}")
        
        # Mudar para inglês e repetir teste
        print("\n🔄 Mudando para inglês...")
        self.session.post(
            f"{self.base_url}/api/i18n/change-locale",
            json={'locale': 'en_US'}
        )
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={'email': '', 'password': ''}
            )
            
            if response.status_code == 400:
                data = response.json()
                message = data.get('message', 'N/A')
                print(f"✅ Required fields (EN): {message}")
            
        except Exception as e:
            print(f"❌ Erro no teste em inglês: {e}")
    
    def test_content_language_headers(self):
        """Testa se headers Content-Language estão sendo enviados"""
        print("\n📡 TESTANDO HEADERS Content-Language...")
        
        locales = ['pt_BR', 'en_US', 'es_ES']
        
        for locale in locales:
            # Mudar idioma
            self.session.post(
                f"{self.base_url}/api/i18n/change-locale",
                json={'locale': locale}
            )
            
            # Fazer request e verificar header
            try:
                response = self.session.get(f"{self.base_url}/api/i18n/info")
                content_language = response.headers.get('Content-Language')
                
                if content_language:
                    print(f"✅ {locale}: Content-Language = {content_language}")
                else:
                    print(f"⚠️  {locale}: Header Content-Language não encontrado")
                    
            except Exception as e:
                print(f"❌ {locale}: Erro ao verificar header - {e}")
    
    def test_accept_language_detection(self):
        """Testa detecção automática via Accept-Language header"""
        print("\n🔍 TESTANDO DETECÇÃO Accept-Language...")
        
        # Criar nova sessão para testar headers
        test_session = requests.Session()
        test_session.headers.update({'Content-Type': 'application/json'})
        
        test_cases = [
            {'header': 'pt-BR,pt;q=0.9', 'expected': 'pt_BR', 'desc': 'Português'},
            {'header': 'en-US,en;q=0.9', 'expected': 'en_US', 'desc': 'Inglês'},
            {'header': 'es-ES,es;q=0.9', 'expected': 'es_ES', 'desc': 'Espanhol'},
            {'header': 'fr-FR,fr;q=0.9', 'expected': 'en_US', 'desc': 'Francês (fallback)'}
        ]
        
        for case in test_cases:
            test_session.headers['Accept-Language'] = case['header']
            
            try:
                response = test_session.get(f"{self.base_url}/api/i18n/info")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        current_locale = data.get('data', {}).get('current_locale')
                        
                        if current_locale == case['expected']:
                            print(f"✅ {case['desc']}: {case['header']} → {current_locale}")
                        else:
                            print(f"⚠️  {case['desc']}: Esperado {case['expected']}, obtido {current_locale}")
                    else:
                        print(f"❌ {case['desc']}: Resposta de erro")
                else:
                    print(f"❌ {case['desc']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {case['desc']}: {e}")
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES DO SISTEMA i18n SYMPLLE")
        print("=" * 60)
        
        tests = [
            self.test_server_health,
            self.test_root_endpoint,
            self.test_i18n_availability,
            self.test_locale_changes,
            self.test_i18n_demo,
            self.test_auth_endpoints_with_i18n,
            self.test_content_language_headers,
            self.test_accept_language_detection
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Erro no teste {test.__name__}: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 RESULTADO FINAL: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 TODOS OS TESTES PASSARAM! Sistema i18n funcionando perfeitamente!")
        elif passed >= total * 0.8:
            print("✅ Maior parte dos testes passou. Sistema funcional com pequenos ajustes.")
        elif passed >= total * 0.5:
            print("⚠️  Sistema parcialmente funcional. Verificar erros acima.")
        else:
            print("❌ Sistema com problemas. Verificar configuração e logs.")
        
        print("\n📋 RESUMO DOS RECURSOS TESTADOS:")
        print("   🔌 Conectividade com servidor")
        print("   🌍 Disponibilidade do sistema i18n")
        print("   🔄 Mudança dinâmica de idiomas")
        print("   🎭 Demonstrações de formatação")
        print("   🔐 Autenticação com mensagens localizadas")
        print("   📡 Headers Content-Language")
        print("   🔍 Detecção Accept-Language")
        
        return passed == total

def quick_test():
    """Teste rápido para verificar se básico está funcionando"""
    print("⚡ TESTE RÁPIDO")
    
    try:
        tester = SymplleI18nTester()
        
        # Teste de conexão
        if not tester.test_server_health():
            print("❌ Servidor não está respondendo")
            return False
        
        # Teste básico i18n
        if not tester.test_i18n_availability():
            print("⚠️  Sistema i18n não disponível - funcionando em modo básico")
            return True  # Não é erro fatal
        
        print("✅ Teste rápido passou! Sistema funcionando.")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste rápido: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Testa sistema i18n do Symplle')
    parser.add_argument('--quick', action='store_true', help='Executa apenas teste rápido')
    parser.add_argument('--url', default='http://localhost:5000', help='URL da API')
    
    args = parser.parse_args()
    
    if args.quick:
        success = quick_test()
    else:
        tester = SymplleI18nTester(args.url)
        success = tester.run_all_tests()
    
    # Exit code para scripts
    sys.exit(0 if success else 1)