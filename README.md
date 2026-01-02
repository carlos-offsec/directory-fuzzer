# DirBrute v2.1 Professional - Ferramenta Profissional de Brute Force de Diretórios

Uma ferramenta completa e profissional para realizar brute force de diretórios e arquivos em servidores web.

## 🚀 Características

- ✅ **Multi-threaded**: Execução paralela com múltiplas threads para máxima velocidade
- ✅ **Progress Bar**: Acompanhe o progresso em tempo real com ETA e velocidade
- ✅ **Múltiplos Métodos HTTP**: Suporte a GET, POST, HEAD, PUT, DELETE
- ✅ **Filtros de Status Code**: Filtre por códigos de status específicos
- ✅ **Extensões Customizadas**: Adicione extensões automaticamente aos paths
- ✅ **Rate Limiting**: Controle a taxa de requisições por segundo
- ✅ **SSL Configurável**: Opção para desabilitar verificação SSL
- ✅ **Headers Customizados**: Adicione headers HTTP personalizados
- ✅ **User-Agent Customizado**: Configure o User-Agent
- ✅ **Output em Arquivo**: Salve resultados em arquivo (TXT e JSON)
- ✅ **Modo Verboso**: Detalhes completos de todas as requisições
- ✅ **Estatísticas Completas**: Relatório detalhado ao final com agrupamento por status
- ✅ **Interface Colorida**: Output colorido e organizado com banner profissional
- ✅ **Tratamento de Erros**: Tratamento robusto de exceções
- ✅ **Interrupção Graciosa**: Ctrl+C mostra resultados e encerra normalmente
- ✅ **Validação de Entrada**: Validação automática de URL e arquivos
- ✅ **Formatação de Tamanhos**: Tamanhos de resposta formatados (KB, MB, etc.)
- ✅ **Tempo de Resposta**: Mostra tempo de resposta de cada requisição

## 📦 Instalação

### Requisitos

- Python 3.6+
- Biblioteca `requests`

### Instalação das Dependências

```bash
pip install requests
```

Ou:

```bash
pip3 install requests
```

## 🎯 Uso Básico

```bash
python dirbrute.py -u http://example.com -w wordlist.txt
```

## 📖 Opções Avançadas

### Threads e Performance

```bash
# Usar 100 threads para maior velocidade
python dirbrute.py -u http://example.com -w wordlist.txt -t 100

# Ajustar timeout (padrão: 10 segundos)
python dirbrute.py -u http://example.com -w wordlist.txt -T 5
```

### Métodos HTTP

```bash
# Usar método HEAD (mais rápido, menos informações)
python dirbrute.py -u http://example.com -w wordlist.txt -m HEAD

# Usar método POST
python dirbrute.py -u http://example.com -w wordlist.txt -m POST
```

### Filtros de Status Code

```bash
# Reportar apenas códigos 200, 301, 302
python dirbrute.py -u http://example.com -w wordlist.txt -s 200 301 302

# Reportar apenas códigos 403 (Forbidden)
python dirbrute.py -u http://example.com -w wordlist.txt -s 403
```

### Extensões

```bash
# Adicionar extensões .php e .html automaticamente
python dirbrute.py -u http://example.com -w wordlist.txt -e php html

# Testar com múltiplas extensões
python dirbrute.py -u http://example.com -w wordlist.txt -e php html js css
```

### Headers Customizados

```bash
# Adicionar cookie
python dirbrute.py -u http://example.com -w wordlist.txt -H "Cookie: session=abc123"

# Múltiplos headers
python dirbrute.py -u http://example.com -w wordlist.txt -H "Cookie: session=abc123" -H "Authorization: Bearer token123"
```

### User-Agent

```bash
# User-Agent customizado
python dirbrute.py -u http://example.com -w wordlist.txt -U "MyBot/1.0"
```

### SSL e Redirects

```bash
# Desabilitar verificação SSL (para testes em ambientes de desenvolvimento)
python dirbrute.py -u http://example.com -w wordlist.txt --no-ssl

# Não seguir redirects
python dirbrute.py -u http://example.com -w wordlist.txt --no-redirects
```

### Rate Limiting

```bash
# Limitar a 10 requisições por segundo
python dirbrute.py -u http://example.com -w wordlist.txt -r 10
```

### Modo Verboso

```bash
# Mostrar todas as requisições (incluindo 404s)
python dirbrute.py -u http://example.com -w wordlist.txt -v
```

### Salvar Resultados

```bash
# Salvar resultados em arquivo TXT
python dirbrute.py -u http://example.com -w wordlist.txt -o results.txt

# Salvar também em formato JSON
python dirbrute.py -u http://example.com -w wordlist.txt -o results.txt --json
```

## 🔥 Exemplos Completos

### Scan Básico Rápido
```bash
python dirbrute.py -u http://example.com -w wordlist.txt -t 100 -m HEAD
```

### Scan Completo com Filtros
```bash
python dirbrute.py -u http://example.com -w wordlist.txt \
  -t 50 \
  -s 200 301 302 403 \
  -e php html js \
  -o results.txt \
  -v
```

### Scan com Autenticação
```bash
python dirbrute.py -u http://example.com -w wordlist.txt \
  -H "Cookie: session=abc123" \
  -H "Authorization: Bearer token123" \
  -t 30
```

### Scan em Ambiente de Desenvolvimento
```bash
python dirbrute.py -u http://localhost:8080 -w wordlist.txt \
  --no-ssl \
  -t 100 \
  -v
```

### Scan com JSON Output
```bash
python dirbrute.py -u http://example.com -w wordlist.txt \
  -o results.txt \
  --json
```

## 📊 Output

O script fornece:

1. **Banner Profissional**: Banner ASCII art com todas as configurações do scan
2. **Progresso em Tempo Real**: 
   - Progresso percentual
   - Velocidade (req/s)
   - Tempo estimado (ETA)
   - Paths encontrados em tempo real
3. **Paths Encontrados**: Exibidos em tempo real com cores e informações:
   - URL completa
   - Código de status HTTP
   - Tamanho da resposta (formatado: KB, MB, etc.)
   - Tempo de resposta
   - Cores por tipo:
     - 🟢 Verde: Códigos 2xx (Sucesso)
     - 🟡 Amarelo: Códigos 3xx (Redirect)
     - 🔵 Ciano: Códigos 4xx (Client Error)
     - 🔴 Vermelho: Códigos 5xx (Server Error)
4. **Estatísticas Finais Detalhadas**:
   - Total de paths encontrados
   - Total de requisições
   - Requisições bem-sucedidas
   - Requisições falhadas
   - Tempo decorrido (formatado)
   - Velocidade média
   - **Agrupamento por Status Code**: Lista organizada por código de status
5. **Output em Arquivo**: 
   - Formato TXT: Lista simples de URLs e status codes
   - Formato JSON: Estrutura completa com metadados e estatísticas

## 🎨 Cores no Output

- 🟢 **Verde**: Paths encontrados e sucessos
- 🔴 **Vermelho**: Erros e falhas
- 🟡 **Amarelo**: Avisos e redirects
- 🔵 **Azul/Ciano**: Informações e estatísticas
- ⚪ **Branco**: Informações gerais

## ⚙️ Parâmetros Completos

```
required arguments:
  -u, --url             URL alvo (ex: http://example.com)
  -w, --wordlist        Arquivo de wordlist

optional arguments:
  -h, --help            Mostrar ajuda
  -t, --threads         Número de threads (padrão: 50)
  -T, --timeout         Timeout em segundos (padrão: 10)
  -m, --method          Método HTTP: GET, POST, HEAD, PUT, DELETE (padrão: GET)
  -s, --status          Status codes para reportar (padrão: todos exceto 404)
  -e, --extensions      Extensões para adicionar aos paths
  -U, --user-agent      User-Agent customizado
  -H, --header          Header customizado (pode ser usado múltiplas vezes)
  --no-ssl              Desabilitar verificação SSL
  --no-redirects        Não seguir redirects
  -r, --rate-limit      Limitar taxa de requisições por segundo
  -v, --verbose         Modo verboso
  -o, --output          Salvar resultados em arquivo
  --json                Salvar resultados também em formato JSON
  --clear               Limpar tela antes de iniciar (padrão: manter histórico)
```

## 🛑 Interrupção Graciosa (Ctrl+C)

O script foi projetado para lidar graciosamente com interrupções:

- Pressione **Ctrl+C** durante a execução
- O script finalizará as requisições em andamento
- Mostrará um resumo completo dos resultados encontrados até o momento
- Encerrará normalmente sem erros

```bash
# Durante a execução, pressione Ctrl+C
# Você verá:
# [!] Interrupção detectada... Finalizando graciosamente...
# Aguarde enquanto finalizamos as requisições em andamento...
# 
# [Resumo completo dos resultados]
```

## 📝 Formato da Wordlist

A wordlist deve conter um path por linha:

```
admin
login
dashboard
api
test
config
backup
```

Linhas começando com `#` são ignoradas (comentários).

## 🔒 Considerações de Segurança

- Use apenas em sistemas que você tem permissão para testar
- Respeite rate limits para não sobrecarregar servidores
- Use `--rate-limit` em ambientes de produção
- Esteja ciente das leis locais sobre segurança cibernética

## 🐛 Troubleshooting

### Erro de Conexão
- Verifique se a URL está correta
- Verifique conectividade de rede
- Tente aumentar o timeout com `-T`

### Muitos Timeouts
- Reduza o número de threads com `-t`
- Aumente o timeout com `-T`
- Use rate limiting com `-r`

### SSL Errors
- Use `--no-ssl` apenas em ambientes de desenvolvimento/teste
- Verifique certificados SSL do servidor

## 🔧 Melhorias na Versão 2.1

- ✅ Argumentos opcionais `-u` e `-w` para URL e wordlist
- ✅ Interrupção graciosa com Ctrl+C (mostra resultados e encerra normalmente)
- ✅ Banner profissional com ASCII art
- ✅ Formatação de tamanhos de resposta (KB, MB, GB)
- ✅ Tempo de resposta por requisição
- ✅ Agrupamento de resultados por status code
- ✅ Validação automática de URL e arquivos
- ✅ Output em formato JSON
- ✅ Melhor tratamento de erros e exceções
- ✅ Interface mais polida e profissional
- ✅ **Preserva histórico do terminal** (não limpa a tela por padrão)
- ✅ Opção `--clear` para limpar tela quando necessário

## 📄 Licença

Ferramenta para uso educacional e testes autorizados.

## 🤝 Contribuições

Melhorias e sugestões são bem-vindas!

---

**Versão**: 2.1 Professional  
**Autor**: Tool Profissional  
**Última Atualização**: 2024

