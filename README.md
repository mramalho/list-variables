# Inventário SSM e Secrets Manager (CLI)

Script em Python que lista **apenas metadata** do **AWS Systems Manager Parameter Store** e do **AWS Secrets Manager** em formato de tabela ou TSV. Os valores dos parâmetros e dos secrets **não** são lidos nem exibidos.

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
| `--output` | `table` (default) ou `tsv`. |

## Saída

- **stderr**: linhas `=== SSM Parameter Store ===` e `=== Secrets Manager ===`, além de mensagens de erro.
- **stdout**: a tabela ou o TSV. Em `--what both`, há uma linha em branco entre o bloco do SSM e o dos secrets no stdout.

## Permissões IAM (referência)

Operações usadas pelo script:

- Parameter Store: `ssm:DescribeParameters`
- Secrets Manager: `secretsmanager:ListSecrets`

Restrinja com políticas conforme o princípio do menor privilégio.

## Segurança

O script chama apenas `DescribeParameters` e `ListSecrets`. **Não** usa `GetParameter`, `GetParameters`, `GetSecretValue` nem descriptografia — portanto **não imprime valores** de parâmetros ou secrets na CLI.

## Dependências e lockfile

- **`pyproject.toml`**: dependências declaradas pelo projeto.
- **`uv.lock`**: versões travadas para uso com **`uv sync`** (instalação reproduzível com UV).
- **`requirements.txt`**: export gerado a partir do lock/projeto, para **`pip install -r`** ou **`uv pip sync`**.

Para **regenerar** o `requirements.txt` depois de alterar dependências no pyproject (requer UV):

```bash
uv lock
uv export --format requirements-txt -o requirements.txt --no-dev
```
