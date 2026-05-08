# Inventário SSM e Secrets Manager (CLI)

Script em Python que lista **Parameter Store** e **Secrets Manager** em colunas **`Name`** e **`Value`** (tabela ou TSV), usando `GetParameters` / **`GetSecretValue`** quando os valores são solicitados (comportamento padrão).

## Pré-requisitos

- [Python](https://www.python.org/) 3.10 ou superior
- Credenciais AWS válidas na [cadeia padrão](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) (variáveis de ambiente, `~/.aws/credentials`, SSO, perfil, IAM Role na instância, etc.)
- **UV** *ou* **pip** + **venv** (escolha um fluxo na secção seguinte)

## Instalação: UV e pip

Use **um** dos fluxos abaixo.

### 1. Criar o ambiente virtual

| Ferramenta | Comando |
|------------|---------|
| **UV** | `uv venv` |
| **pip** | `python3 -m venv .venv` |

(Isso cria a pasta **`.venv/`** na raiz do repositório. Com UV, `uv sync` também pode criar/atualizar essa venv automaticamente.)

### 2. Instalar dependências

**Opção A — projeto com `pyproject.toml` + `uv.lock` (recomendado com UV)**

| Ferramenta | Comando |
|------------|---------|
| **UV** | `uv sync` |
| **pip** | Ative a venv (`source .venv/bin/activate` no Linux/macOS; `.venv\Scripts\activate` no Windows) e rode:<br>`pip install -r requirements.txt`<br>(o `requirements.txt` espelha as versões travadas; use sempre o arquivo versionado no repositório) |

**Opção B — apenas `requirements.txt`**

| Ferramenta | Comando |
|------------|---------|
| **UV** | `uv venv` *(se ainda não existir `.venv/`)*<br>`uv pip sync requirements.txt`<br>*(alinha o ambiente ao arquivo; respeita hashes)* |
| **UV** *(instalar sem “sync”, não remove pacotes extras)* | `uv pip install -r requirements.txt` |
| **pip** *(venv **ativa**)* | `pip install -r requirements.txt` |

### 3. Executar o script

| Ferramenta | Comando base |
|------------|----------------|
| **UV** | `uv run python scripts/list_ssm_and_secrets.py …argumentos…` |
| **pip** | Com venv ativa: `python scripts/list_ssm_and_secrets.py …argumentos…`<br>Ou sem ativar: `.venv/bin/python scripts/list_ssm_and_secrets.py …argumentos…` (Linux/macOS; no Windows use `.venv\Scripts\python.exe`) |

Nos exemplos abaixo, **`COMANDO`** significa um dos dois:

- UV: `uv run python`
- pip: `python` *(com venv ativa)* ou `.venv/bin/python`

---

### Fluxos extras (só UV)

| Objetivo | Comando |
|----------|---------|
| Fixar versão do Python no projeto | `uv python pin 3.12` |
| Nova dependência no projeto | `uv add nome-do-pacote` *(atualiza `pyproject.toml` e `uv.lock`)* |
| Copiar pacotes do `requirements.txt` para o `pyproject.toml` | `uv add -r requirements.txt` |

Após `uv add`, faça commit de `pyproject.toml` e `uv.lock` e regenere o `requirements.txt` se precisar mantê-lo para pip (secção **Dependências e lockfile**).

## Uso

### Ajuda

```bash
COMANDO scripts/list_ssm_and_secrets.py --help
```

Exemplo com UV:

```bash
uv run python scripts/list_ssm_and_secrets.py --help
```

Exemplo com pip (venv ativa):

```bash
python scripts/list_ssm_and_secrets.py --help
```

### Exemplos

Conta e região padrão da configuração AWS:

```bash
COMANDO scripts/list_ssm_and_secrets.py
```

Perfil e região explícitos:

```bash
COMANDO scripts/list_ssm_and_secrets.py --profile minha-conta --region sa-east-1
```

Somente Secrets Manager, saída TSV:

```bash
COMANDO scripts/list_ssm_and_secrets.py --what secrets --output tsv
```

Somente Parameter Store com prefixo no nome:

```bash
COMANDO scripts/list_ssm_and_secrets.py --what ssm --ssm-prefix /meu-app/
```

Redirecionar só os dados (stdout), mantendo títulos e erros no terminal:

```bash
COMANDO scripts/list_ssm_and_secrets.py --what secrets --output tsv > secrets.tsv
```

## Opções da CLI

| Opção | Descrição |
|--------|-----------|
| `--profile` | Nome do profile AWS em `~/.aws/config` / credenciais. |
| `--region` | Região única. Se omitido, vale `AWS_REGION`, `AWS_DEFAULT_REGION` ou o default do profile. |
| `--what` | `both` (default), `ssm` ou `secrets`: o que listar. |
| `--ssm-prefix` | Filtro no SSM: nome do parâmetro com **BeginsWith** (ex.: `/meu-app/`). Só afeta `--what ssm` ou `both`. |
| `--no-ssm-values` | Mantém colunas **Name** e **Value**, mas **Value** fica vazio (sem `GetParameters`). |
| `--secrets-include-deleted` | Inclui secrets em processo de exclusão (~30 dias); só para `--what secrets` ou `both`. |
| `--no-secret-values` | Colunas **Name** e **Value** dos secrets, mas **Value** vazio (sem `GetSecretValue`). |
| `--output` | `table` (default) ou `tsv`. |

## Saída

- **stderr**: títulos das seções, **avisos** (ex.: nenhum secret na região), contagem quando há secrets, e erros de API.
- **stdout**: a tabela ou o TSV. Em `--what both`, há uma linha em branco entre o bloco do SSM e o dos secrets no stdout.

## Permissões IAM (referência)

Operações usadas pelo script:

- Parameter Store: `ssm:DescribeParameters`; para exibir valores (comportamento padrão): `ssm:GetParameters` com descriptografia (`SecureString`).
- Secrets Manager: `secretsmanager:ListSecrets`; para preencher **Value**: `secretsmanager:GetSecretValue` (um pedido por secret).

Restrinja com políticas conforme o princípio do menor privilégio.

## Segurança

- **SSM:** só **`Name`** e **`Value`**. Por padrão usa **`GetParameters`** com **`WithDecryption=True`**. Com **`--no-ssm-values`**, **Value** fica vazio.
- **Secrets:** só **`Name`** e **`Value`**. Por padrão usa **`GetSecretValue`** — o conteúdo aparece na saída (incluindo JSON em texto); **não** redirecione para logs públicos. Com **`--no-secret-values`**, **Value** fica vazio. Secrets **binários** aparecem como **Base64** na coluna Value.

## Dependências e lockfile

- **`pyproject.toml`**: dependências declaradas pelo projeto.
- **`uv.lock`**: versões travadas para uso com **`uv sync`** (instalação reproduzível com UV).
- **`requirements.txt`**: export gerado a partir do lock/projeto, para **`pip install -r`** ou **`uv pip sync`**.

Para **regenerar** o `requirements.txt` depois de alterar dependências no pyproject (requer UV):

```bash
uv lock
uv export --format requirements-txt -o requirements.txt --no-dev
```

## Problemas comuns

### Lista de secrets só com cabeçalhos (nenhuma linha de dados)

O Secrets Manager é **regional**: secrets criados em `sa-east-1` não aparecem ao listar em `us-east-1`. Confira no console AWS a **mesma região** que o script usa e passe **`--region`** se precisar:

```bash
COMANDO scripts/list_ssm_and_secrets.py --what secrets --region sa-east-1 --output tsv
```

Confira também **perfil/conta** (`aws sts get-caller-identity` ou `--profile`). Políticas IAM com **condição por tag** podem fazer `ListSecrets` retornar lista vazia sem erro. Para secrets **agendados para exclusão**, experimente **`--secrets-include-deleted`**.

Ao rodar de novo, veja no **stderr** a mensagem de diagnóstico (região usada e aviso se vieram 0 secrets).

### `CERTIFICATE_VERIFY_FAILED` / certificado autoassinado ao usar `pip` ou `uv`

Se aparecer erro do tipo **`SSL: CERTIFICATE_VERIFY_FAILED`** ou **`self signed certificate in certificate chain`** ao acessar `https://pypi.org/`, em geral a rede corporativa (proxy/firewall) intercepta HTTPS com um certificado da empresa que o Python não confia. O pip então **nem lista** pacotes no PyPI e mensagens como “Could not find a version that satisfies boto3” são **efeito colateral**, não ausência do pacote.

**Solução correta (recomendada):** confiar no certificado raiz (ou cadeia) fornecido pela TI — arquivo `.pem` / `.crt`.

1. Obtenha o certificado CA corporativo (portal da empresa, equipe de rede ou export do navegador na máquina gerenciada).
2. No **WSL/Ubuntu**, você pode instalar no trust store do sistema (exemplo; o caminho do `.crt` pode variar):

   ```bash
   sudo cp /caminho/para/sua-empresa-root-ca.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates
   ```

3. Ou aponte explicitamente um bundle que inclua esse CA **antes** de instalar:

   ```bash
   export SSL_CERT_FILE=/caminho/para/ca-bundle-completo.pem
   export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
   pip install -r requirements.txt
   ```

   Para **UV**, na maioria dos ambientes as mesmas variáveis (`SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`) também orientam o cliente HTTPS.

4. Alternativa por comando (pip), se tiver só o ficheiro PEM da CA:

   ```bash
   pip install --cert /caminho/para/ca-bundle-completo.pem -r requirements.txt
   ```

**Último recurso (menos seguro):** desativar verificação só para os hosts do índice — use apenas se a política da empresa permitir e em ambiente isolado:

```bash
pip install -r requirements.txt \
  --trusted-host pypi.org \
  --trusted-host files.pythonhosted.org
```

Isso **não valida** TLS para esses hosts; prefira sempre instalar o CA corporativo.

Se o `requirements.txt` tiver linhas `--hash=sha256:...` e ainda falhar por rede/SSL, primeiro resolva o SSL; depois, se precisar contornar hashes num teste pontual, só em último caso use opções como `--no-deps` / gerar um requirements sem hashes — o ideal é rede + CA corretos.
