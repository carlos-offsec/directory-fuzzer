#!/usr/bin/env python3
"""
DirBrute - Ferramenta de Brute Force de Diretórios
Autor: Tool Carlos Souza
"""

import argparse
import requests
import sys
import threading
import time
from queue import Queue
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import signal
import json

# Cores para output (ANSI)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'

class DirBrute:
    def __init__(self, url, wordlist_file, threads=50, timeout=10, 
                 method='GET', status_codes=None, extensions=None,
                 user_agent=None, headers=None, verify_ssl=True,
                 follow_redirects=True, rate_limit=None, verbose=False,
                 output_file=None, json_output=False, clear_screen=False):
        self.url = url.rstrip('/')
        self.wordlist_file = wordlist_file
        self.threads = threads
        self.timeout = timeout
        self.method = method.upper()
        self.status_codes = status_codes if status_codes else []
        self.extensions = extensions if extensions else []
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        self.rate_limit = rate_limit
        self.verbose = verbose
        self.output_file = output_file
        self.json_output = json_output
        self.clear_screen = clear_screen
        
        # Controle de interrupção
        self.interrupted = False
        self.interrupt_lock = threading.Lock()
        
        # Estatísticas
        self.found_paths = []
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.lock = threading.Lock()
        
        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.max_redirects = 10 if follow_redirects else 0
        
        # Headers padrão
        default_headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        
        # Rate limiting
        self.last_request_time = 0
        self.rate_lock = threading.Lock()
        
    def is_interrupted(self):
        """Verifica se foi interrompido"""
        with self.interrupt_lock:
            return self.interrupted
    
    def set_interrupted(self):
        """Marca como interrompido"""
        with self.interrupt_lock:
            self.interrupted = True
        
    def log(self, message, color=Colors.WHITE, end='\n'):
        """Log com cores"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}]{Colors.RESET} {message}", end=end, flush=True)
        
    def log_found(self, url, status_code, content_length=None, response_time=None):
        """Log de path encontrado"""
        with self.lock:
            self.found_paths.append({
                'url': url,
                'status': status_code,
                'length': content_length,
                'time': response_time,
                'timestamp': datetime.now().isoformat()
            })
            
            # Ordenar por status code
            status_color = Colors.GREEN if status_code < 300 else Colors.YELLOW if status_code < 400 else Colors.CYAN if status_code < 500 else Colors.RED
            
            # Formatação profissional
            status_icon = "✓" if status_code < 300 else "→" if status_code < 400 else "✗" if status_code < 500 else "✗"
            
            message = f"{Colors.GREEN}[+]{Colors.RESET} {Colors.BOLD}{url:<60}{Colors.RESET} {status_color}[{status_code}]{Colors.RESET}"
            if content_length:
                size_str = self.format_size(content_length)
                message += f" {Colors.CYAN}[{size_str}]{Colors.RESET}"
            if response_time:
                message += f" {Colors.DIM}[{response_time:.3f}s]{Colors.RESET}"
            print(message)
            
            # Salvar em arquivo se especificado
            if self.output_file:
                with open(self.output_file, 'a', encoding='utf-8') as f:
                    f.write(f"{url} [{status_code}]")
                    if content_length:
                        f.write(f" [{content_length} bytes]")
                    f.write("\n")
    
    def format_size(self, size):
        """Formata tamanho em formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def rate_limit_wait(self):
        """Implementa rate limiting"""
        if self.rate_limit:
            with self.rate_lock:
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                min_interval = 1.0 / self.rate_limit
                
                if time_since_last < min_interval:
                    time.sleep(min_interval - time_since_last)
                
                self.last_request_time = time.time()
    
    def check_path(self, path):
        """Verifica um path específico"""
        # Verificar se foi interrompido
        if self.is_interrupted():
            return
        
        try:
            self.rate_limit_wait()
            
            # Verificar novamente após rate limit
            if self.is_interrupted():
                return
            
            full_url = urljoin(self.url + '/', path.lstrip('/'))
            
            with self.lock:
                self.total_requests += 1
            
            # Fazer requisição
            start_time = time.time()
            try:
                if self.method == 'GET':
                    response = self.session.get(full_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                elif self.method == 'POST':
                    response = self.session.post(full_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                elif self.method == 'HEAD':
                    response = self.session.head(full_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                else:
                    response = self.session.request(self.method, full_url, timeout=self.timeout, allow_redirects=self.follow_redirects)
                
                response_time = time.time() - start_time
                status_code = response.status_code
                content_length = len(response.content) if hasattr(response, 'content') else response.headers.get('Content-Length', 0)
                try:
                    content_length = int(content_length) if content_length else 0
                except (ValueError, TypeError):
                    content_length = 0
                
                with self.lock:
                    self.successful_requests += 1
                
                # Verificar se deve reportar
                should_report = True
                
                # Filtrar por status code
                if self.status_codes:
                    should_report = status_code in self.status_codes
                else:
                    # Padrão: reportar tudo exceto 404
                    should_report = status_code != 404
                
                if should_report:
                    self.log_found(full_url, status_code, content_length, response_time)
                elif self.verbose:
                    self.log(f"{full_url} [{status_code}]", Colors.DIM)
                    
            except requests.exceptions.Timeout:
                with self.lock:
                    self.failed_requests += 1
                if self.verbose:
                    self.log(f"Timeout: {full_url}", Colors.YELLOW)
            except requests.exceptions.SSLError:
                with self.lock:
                    self.failed_requests += 1
                if self.verbose:
                    self.log(f"SSL Error: {full_url}", Colors.RED)
            except requests.exceptions.ConnectionError:
                with self.lock:
                    self.failed_requests += 1
                if self.verbose:
                    self.log(f"Connection Error: {full_url}", Colors.RED)
            except requests.exceptions.RequestException as e:
                with self.lock:
                    self.failed_requests += 1
                if self.verbose:
                    self.log(f"Error: {full_url} - {e}", Colors.RED)
                    
        except Exception as e:
            with self.lock:
                self.failed_requests += 1
            if self.verbose:
                self.log(f"Unexpected error: {e}", Colors.RED)
    
    def generate_paths(self):
        """Gera lista de paths a testar"""
        paths = []
        
        try:
            with open(self.wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if self.is_interrupted():
                        break
                    path = line.strip()
                    if not path or path.startswith('#'):
                        continue
                    
                    # Adicionar path base
                    paths.append(path)
                    
                    # Adicionar com extensões se especificado
                    if self.extensions:
                        for ext in self.extensions:
                            ext = ext.lstrip('.')
                            if not path.endswith(f".{ext}"):
                                paths.append(f"{path}.{ext}")
                                
        except FileNotFoundError:
            self.log(f"Arquivo não encontrado: {self.wordlist_file}", Colors.RED)
            sys.exit(1)
        except Exception as e:
            self.log(f"Erro ao ler wordlist: {e}", Colors.RED)
            sys.exit(1)
        
        return paths
    
    def print_banner(self):
        """Imprime banner profissional"""
        if self.clear_screen:
            os.system('clear' if os.name != 'nt' else 'cls')
        else:
            # Apenas adiciona algumas linhas em branco para separar visualmente
            print("\n" * 2)
        
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              ██████╗ ██╗██████╗ ██████╗ ██╗   ██╗████████╗███████╗
║              ██╔══██╗██║██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝
║              ██║  ██║██║██████╔╝██████╔╝██║   ██║   ██║   █████╗  
║              ██║  ██║██║██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  
║              ██████╔╝██║██║  ██║██████╔╝╚██████╔╝   ██║   ███████╗
║              ╚═════╝ ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   ╚══════╝
║                                                                   ║
║                    Professional Edition v2.1                     ║
║              Advanced Directory Brute Forcer Tool                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.RESET}
{Colors.CYAN}{'═'*67}{Colors.RESET}
{Colors.WHITE}Target:{Colors.RESET}     {Colors.BOLD}{Colors.GREEN}{self.url}{Colors.RESET}
{Colors.WHITE}Wordlist:{Colors.RESET}   {Colors.BOLD}{self.wordlist_file}{Colors.RESET}
{Colors.WHITE}Threads:{Colors.RESET}    {Colors.BOLD}{self.threads}{Colors.RESET}
{Colors.WHITE}Method:{Colors.RESET}     {Colors.BOLD}{self.method}{Colors.RESET}
{Colors.WHITE}Timeout:{Colors.RESET}    {Colors.BOLD}{self.timeout}s{Colors.RESET}
"""
        if self.status_codes:
            print(f"{Colors.WHITE}Status Codes:{Colors.RESET} {Colors.BOLD}{', '.join(map(str, self.status_codes))}{Colors.RESET}")
        if self.extensions:
            print(f"{Colors.WHITE}Extensions:{Colors.RESET} {Colors.BOLD}{', '.join(self.extensions)}{Colors.RESET}")
        if self.rate_limit:
            print(f"{Colors.WHITE}Rate Limit:{Colors.RESET} {Colors.BOLD}{self.rate_limit} req/s{Colors.RESET}")
        if not self.verify_ssl:
            print(f"{Colors.YELLOW}SSL Verification:{Colors.RESET} {Colors.BOLD}DISABLED{Colors.RESET}")
        print(f"{Colors.CYAN}{'═'*67}{Colors.RESET}\n")
    
    def print_summary(self, interrupted=False):
        """Imprime resumo detalhado"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n{Colors.CYAN}{'═'*67}{Colors.RESET}")
        if interrupted:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠  SCAN INTERROMPIDO PELO USUÁRIO{Colors.RESET}")
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✓  SCAN CONCLUÍDO{Colors.RESET}")
        print(f"{Colors.CYAN}{'═'*67}{Colors.RESET}\n")
        
        # Estatísticas gerais
        print(f"{Colors.BOLD}📊 Estatísticas Gerais:{Colors.RESET}\n")
        print(f"  {Colors.GREEN}✓ Paths Encontrados:{Colors.RESET} {Colors.BOLD}{len(self.found_paths)}{Colors.RESET}")
        print(f"  {Colors.WHITE}📡 Total de Requisições:{Colors.RESET} {Colors.BOLD}{self.total_requests}{Colors.RESET}")
        print(f"  {Colors.GREEN}✓ Sucesso:{Colors.RESET} {Colors.BOLD}{self.successful_requests}{Colors.RESET}")
        print(f"  {Colors.RED}✗ Falhas:{Colors.RESET} {Colors.BOLD}{self.failed_requests}{Colors.RESET}")
        print(f"  {Colors.CYAN}⏱  Tempo Decorrido:{Colors.RESET} {Colors.BOLD}{self.format_time(elapsed_time)}{Colors.RESET}")
        if elapsed_time > 0 and self.total_requests > 0:
            print(f"  {Colors.CYAN}⚡ Velocidade Média:{Colors.RESET} {Colors.BOLD}{self.total_requests/elapsed_time:.2f} req/s{Colors.RESET}")
        
        # Agrupar por status code
        if self.found_paths:
            print(f"\n{Colors.BOLD}📋 Paths Encontrados por Status Code:{Colors.RESET}\n")
            status_groups = {}
            for path in self.found_paths:
                status = path['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(path)
            
            # Ordenar por status code
            for status in sorted(status_groups.keys()):
                paths_list = status_groups[status]
                status_color = Colors.GREEN if status < 300 else Colors.YELLOW if status < 400 else Colors.CYAN if status < 500 else Colors.RED
                print(f"  {status_color}[{status}]{Colors.RESET} {Colors.BOLD}{len(paths_list)} path(s){Colors.RESET}")
                # Mostrar todos os resultados
                for path_info in paths_list:
                    size_str = f" [{self.format_size(path_info['length'])}]" if path_info.get('length') else ""
                    print(f"    {Colors.DIM}→{Colors.RESET} {path_info['url']}{size_str}")
        
        print(f"\n{Colors.CYAN}{'═'*67}{Colors.RESET}\n")
    
    def format_time(self, seconds):
        """Formata tempo em formato legível"""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"
    
    def save_json(self, filename):
        """Salva resultados em JSON"""
        data = {
            'target': self.url,
            'wordlist': self.wordlist_file,
            'scan_date': datetime.now().isoformat(),
            'statistics': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'found_paths': len(self.found_paths)
            },
            'found_paths': self.found_paths
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """Executa o brute force"""
        self.print_banner()
        
        # Gerar paths
        self.log("Carregando wordlist...", Colors.CYAN)
        paths = self.generate_paths()
        total_paths = len(paths)
        self.log(f"Total de paths a testar: {Colors.BOLD}{total_paths}{Colors.RESET}", Colors.CYAN)
        
        if total_paths == 0:
            self.log("Nenhum path encontrado na wordlist!", Colors.RED)
            return
        
        # Limpar arquivo de output se existir
        if self.output_file:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(f"# DirBrute Scan Results\n")
                f.write(f"# Target: {self.url}\n")
                f.write(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Wordlist: {self.wordlist_file}\n")
                f.write(f"# Total paths: {total_paths}\n\n")
        
        self.start_time = time.time()
        self.log(f"Iniciando scan com {Colors.BOLD}{self.threads}{Colors.RESET} threads...\n", Colors.GREEN)
        
        # Executar com ThreadPoolExecutor
        completed = 0
        executor = None
        try:
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {executor.submit(self.check_path, path): path for path in paths}
                
                for future in as_completed(futures):
                    if self.is_interrupted():
                        # Cancelar futures pendentes
                        for f in futures:
                            f.cancel()
                        break
                    
                    completed += 1
                    if completed % 50 == 0 or completed == total_paths:
                        progress = (completed / total_paths) * 100
                        elapsed = time.time() - self.start_time
                        speed = completed / elapsed if elapsed > 0 else 0
                        remaining = (total_paths - completed) / speed if speed > 0 else 0
                        
                        print(f"\r{Colors.CYAN}[Progress]{Colors.RESET} "
                              f"{Colors.BOLD}{completed}/{total_paths}{Colors.RESET} "
                              f"({progress:.1f}%) | "
                              f"Speed: {Colors.BOLD}{speed:.1f} req/s{Colors.RESET} | "
                              f"ETA: {Colors.BOLD}{remaining:.0f}s{Colors.RESET} | "
                              f"Found: {Colors.GREEN}{Colors.BOLD}{len(self.found_paths)}{Colors.RESET}", 
                              end='', flush=True)
        
        except KeyboardInterrupt:
            self.set_interrupted()
        
        print()  # Nova linha após progresso
        
        # Salvar JSON se solicitado
        if self.json_output and self.found_paths:
            json_file = self.output_file.replace('.txt', '.json') if self.output_file else 'results.json'
            self.save_json(json_file)
            self.log(f"Resultados salvos em JSON: {json_file}", Colors.CYAN)
        
        # Mostrar resumo
        self.print_summary(interrupted=self.is_interrupted())

# Variável global para o scanner (para signal handler)
scanner_instance = None

def signal_handler(sig, frame):
    """Handler profissional para Ctrl+C"""
    global scanner_instance
    if scanner_instance:
        scanner_instance.set_interrupted()
        print(f"\n\n{Colors.YELLOW}{Colors.BOLD}[!] Interrupção detectada... Finalizando graciosamente...{Colors.RESET}")
        print(f"{Colors.YELLOW}Aguarde enquanto finalizamos as requisições em andamento...{Colors.RESET}\n")
        # Dar tempo para threads finalizarem
        time.sleep(1)
    else:
        print(f"\n\n{Colors.YELLOW}[!] Interrompido pelo usuário{Colors.RESET}")
        sys.exit(0)

def validate_url(url):
    """Valida URL"""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        if result.scheme not in ['http', 'https']:
            return False
        return True
    except:
        return False

def main():
    global scanner_instance
    
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(
        description="DirBrute - Ferramenta Profissional de Brute Force de Diretórios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s -u http://example.com -w wordlist.txt
  %(prog)s -u http://example.com -w wordlist.txt -t 100 -T 5
  %(prog)s -u http://example.com -w wordlist.txt -s 200 301 302 -e php html
  %(prog)s -u http://example.com -w wordlist.txt -m HEAD -o results.txt
  %(prog)s -u http://example.com -w wordlist.txt --no-ssl -v
  %(prog)s -u http://example.com -w wordlist.txt --json
        """
    )
    
    parser.add_argument("-u", "--url", required=True,
                       help="URL alvo (ex: http://example.com)")
    parser.add_argument("-w", "--wordlist", required=True,
                       help="Arquivo de wordlist")
    
    parser.add_argument("-t", "--threads", type=int, default=50,
                       help="Número de threads (padrão: 50)")
    parser.add_argument("-T", "--timeout", type=int, default=10,
                       help="Timeout em segundos (padrão: 10)")
    parser.add_argument("-m", "--method", choices=['GET', 'POST', 'HEAD', 'PUT', 'DELETE'],
                       default='GET', help="Método HTTP (padrão: GET)")
    parser.add_argument("-s", "--status", type=int, nargs='+', metavar='CODE',
                       help="Status codes para reportar (padrão: todos exceto 404)")
    parser.add_argument("-e", "--extensions", nargs='+', metavar='EXT',
                       help="Extensões para adicionar aos paths (ex: php html)")
    parser.add_argument("-U", "--user-agent", default=None,
                       help="User-Agent customizado")
    parser.add_argument("-H", "--header", action='append', metavar='HEADER',
                       help="Header customizado (ex: -H 'Cookie: session=123')")
    parser.add_argument("--no-ssl", action="store_true",
                       help="Desabilitar verificação SSL")
    parser.add_argument("--no-redirects", action="store_true",
                       help="Não seguir redirects")
    parser.add_argument("-r", "--rate-limit", type=float, metavar='RATE',
                       help="Limitar taxa de requisições por segundo")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Modo verboso")
    parser.add_argument("-o", "--output", metavar='FILE',
                       help="Salvar resultados em arquivo")
    parser.add_argument("--json", action="store_true",
                       help="Salvar resultados também em formato JSON")
    parser.add_argument("--clear", action="store_true",
                       help="Limpar tela antes de iniciar (padrão: manter histórico do terminal)")
    
    args = parser.parse_args()
    
    # Validações
    if not validate_url(args.url):
        print(f"{Colors.RED}Erro: URL inválida. Use formato: http://example.com ou https://example.com{Colors.RESET}")
        sys.exit(1)
    
    if not os.path.isfile(args.wordlist):
        print(f"{Colors.RED}Erro: Arquivo de wordlist não encontrado: {args.wordlist}{Colors.RESET}")
        sys.exit(1)
    
    # Processar headers
    headers = {}
    if args.header:
        for header in args.header:
            if ':' in header:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            else:
                print(f"{Colors.YELLOW}Aviso: Header inválido ignorado: {header}{Colors.RESET}")
    
    # Criar e executar scanner
    scanner_instance = DirBrute(
        url=args.url,
        wordlist_file=args.wordlist,
        threads=args.threads,
        timeout=args.timeout,
        method=args.method,
        status_codes=args.status,
        extensions=args.extensions,
        user_agent=args.user_agent,
        headers=headers if headers else None,
        verify_ssl=not args.no_ssl,
        follow_redirects=not args.no_redirects,
        rate_limit=args.rate_limit,
        verbose=args.verbose,
        output_file=args.output,
        json_output=args.json,
        clear_screen=args.clear
    )
    
    try:
        scanner_instance.run()
    except KeyboardInterrupt:
        # Já tratado pelo signal handler
        pass
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Erro fatal: {e}{Colors.RESET}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        scanner_instance = None

if __name__ == "__main__":
    main()
