# Inventário SSM e Secrets Manager (CLI)

Script em Python que lista **apenas metadata** do **AWS Systems Manager Parameter Store** e do **AWS Secrets Manager** em formato de tabela ou TSV. Os valores dos parâmetros e dos secrets **não** são lidos nem exibidos.

## Pré-requisitos

- [Python](https://www.python.org/) 3.10 ou superior
- [uv](https://docs.astral.sh/uv/) (gestão de ambiente e dependências)
- Credenciais AWS válidas na [cadeia padrão](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) (variáveis de ambiente, `~/.aws/credentials`, SSO, perfil, IAM Role na instância, etc.)

## Instalação

Na raiz do repositório:

```bash
uv sync
```

Isso cria/atualiza o ambiente virtual (`.venv/`) e instala `boto3` e `tabulate` conforme `pyproject.toml` e `uv.lock`.

## Uso

### Ajuda

```bash
uv run python scripts/list_ssm_and_secrets.py --help
```

### Exemplos

Conta e região padrão da sua configuração AWS:

```bash
uv run python scripts/list_ssm_and_secrets.py
```

Perfil e região explícitos:

```bash
uv run python scripts/list_ssm_and_secrets.py --profile minha-conta --region sa-east-1
```

Somente Secrets Manager, saída TSV (útil para `grep`, `awk`, planilhas):

```bash
uv run python scripts/list_ssm_and_secrets.py --what secrets --output tsv
```

Somente Parameter Store com prefixo no nome do parâmetro:

```bash
uv run python scripts/list_ssm_and_secrets.py --what ssm --ssm-prefix /meu-app/
```

Redirecionar só os dados (sem os títulos das seções), preservando mensagens no terminal:

```bash
uv run python scripts/list_ssm_and_secrets.py --what secrets --output tsv > secrets.tsv
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

Dependências estão em `pyproject.toml`. O arquivo `uv.lock` fixa versões para instalações reproduzíveis.

Para gerar um `requirements.txt` (integrações que só aceitam pip):

```bash
uv export --format requirements-txt -o requirements.txt
```
