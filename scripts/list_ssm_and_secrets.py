#!/usr/bin/env python3
"""Lista SSM Parameter Store e Secrets Manager com colunas Name e Value (GetParameters / GetSecretValue).

Uso com UV (na raiz do repositório):

    uv sync
    uv run python scripts/list_ssm_and_secrets.py --help
"""

from __future__ import annotations

import argparse
import base64
import sys

import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate


def build_session(profile: str | None, region: str | None) -> boto3.Session:
    kwargs: dict[str, str] = {}
    if profile:
        kwargs["profile_name"] = profile
    if region:
        kwargs["region_name"] = region
    return boto3.Session(**kwargs)


def truncate(text: str | None, max_len: int = 80) -> str:
    if not text:
        return ""
    s = text.replace("\n", " ").replace("\t", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def sanitize_tsv_cell(text: str) -> str:
    return text.replace("\t", " ").replace("\r", " ").replace("\n", " ")


_GET_PARAMETERS_BATCH = 10


def batch_get_ssm_parameter_values(ssm_client, names: list[str]) -> dict[str, str]:
    """Nome -> valor bruto (SecureString vem descriptografado com WithDecryption)."""
    values: dict[str, str] = {}
    for i in range(0, len(names), _GET_PARAMETERS_BATCH):
        chunk = [n for n in names[i : i + _GET_PARAMETERS_BATCH] if n]
        if not chunk:
            continue
        try:
            resp = ssm_client.get_parameters(Names=chunk, WithDecryption=True)
        except ClientError as e:
            print(f"Aviso: get_parameters falhou para um lote: {e}", file=sys.stderr)
            for n in chunk:
                values.setdefault(n, "")
            continue
        for p in resp.get("Parameters", []):
            values[p["Name"]] = p.get("Value", "")
        for inv in resp.get("InvalidParameters", []):
            values.setdefault(inv, "")
    return values


def list_ssm_parameters(
    ssm_client,
    prefix: str | None,
    *,
    include_values: bool,
    output_fmt: str,
) -> tuple[list[str], list[list[object]]]:
    paginator = ssm_client.get_paginator("describe_parameters")
    paginate_kwargs: dict = {}
    if prefix:
        paginate_kwargs["ParameterFilters"] = [
            {"Key": "Name", "Option": "BeginsWith", "Values": [prefix]},
        ]
    names_ordered: list[str] = []
    for page in paginator.paginate(**paginate_kwargs):
        for p in page.get("Parameters", []):
            names_ordered.append(p.get("Name", ""))

    headers = ["Name", "Value"]
    value_map: dict[str, str] = {}
    if include_values and names_ordered:
        value_map = batch_get_ssm_parameter_values(ssm_client, names_ordered)

    value_max_table = 200
    rows: list[list[object]] = []
    for name in names_ordered:
        raw = value_map.get(name, "") if include_values else ""
        if output_fmt == "tsv":
            cell = sanitize_tsv_cell(raw)
        else:
            cell = truncate(raw, max_len=value_max_table) if raw else ""
        rows.append([name, cell])

    return headers, rows


def _payload_from_get_secret_value(resp: dict) -> str:
    s = resp.get("SecretString")
    if s is not None:
        return s
    blob = resp.get("SecretBinary")
    if blob is None:
        return ""
    if isinstance(blob, bytes):
        return base64.b64encode(blob).decode("ascii")
    return str(blob)


def fetch_secret_value(sm_client, secret_id: str) -> str:
    try:
        resp = sm_client.get_secret_value(SecretId=secret_id)
    except ClientError as e:
        print(f"Aviso: get_secret_value falhou para «{secret_id}»: {e}", file=sys.stderr)
        return ""
    return _payload_from_get_secret_value(resp)


def list_secrets(
    sm_client,
    *,
    include_deleted: bool = False,
    include_values: bool = True,
    output_fmt: str = "table",
) -> tuple[list[str], list[list[object]]]:
    paginator = sm_client.get_paginator("list_secrets")
    names_ordered: list[str] = []
    paginate_kw: dict = {}
    if include_deleted:
        paginate_kw["IncludeDeletedSecrets"] = True
    for page in paginator.paginate(**paginate_kw):
        for s in page.get("SecretList", []):
            name = s.get("Name") or ""
            if name:
                names_ordered.append(name)

    headers = ["Name", "Value"]
    value_max_table = 200
    rows: list[list[object]] = []
    for name in names_ordered:
        raw = fetch_secret_value(sm_client, name) if include_values else ""
        if output_fmt == "tsv":
            cell = sanitize_tsv_cell(raw)
        else:
            cell = truncate(raw, max_len=value_max_table) if raw else ""
        rows.append([name, cell])

    return headers, rows


def print_output(headers: list[str], rows: list[list[object]], output_fmt: str) -> None:
    if output_fmt == "tsv":
        print("\t".join(headers))
        for row in rows:
            print("\t".join(str(c) for c in row))
    else:
        print(tabulate(rows, headers=headers, tablefmt="simple"))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lista parâmetros SSM e secrets AWS em colunas Name e Value "
            "(GetParameters / GetSecretValue)."
        )
    )
    parser.add_argument("--profile", help="Profile AWS (~/.aws/config)")
    parser.add_argument("--region", help="Região única (default: cadeia boto3/env/config)")
    parser.add_argument(
        "--what",
        choices=("both", "ssm", "secrets"),
        default="both",
        help="Recurso a listar (default: both)",
    )
    parser.add_argument(
        "--ssm-prefix",
        metavar="PREFIX",
        help="Filtro SSM: Name begins-with (ex.: /meu-app/)",
    )
    parser.add_argument(
        "--no-ssm-values",
        action="store_true",
        help="Não preenche Value (colunas continuam Name e Value); não usa ssm:GetParameters",
    )
    parser.add_argument(
        "--secrets-include-deleted",
        action="store_true",
        help="Inclui secrets marcados para exclusão (últimos ~30 dias); só afeta --what secrets ou both",
    )
    parser.add_argument(
        "--no-secret-values",
        action="store_true",
        help="Não preenche Value dos secrets (sem GetSecretValue); colunas continuam Name e Value",
    )
    parser.add_argument(
        "--output",
        choices=("table", "tsv"),
        default="table",
        help="Formato de saída (default: table)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    session = build_session(args.profile, args.region)
    exit_code = 0
    printed_ssm = False

    if args.what in ("both", "ssm"):
        print("=== SSM Parameter Store ===", file=sys.stderr)
        try:
            ssm = session.client("ssm")
            headers, rows = list_ssm_parameters(
                ssm,
                args.ssm_prefix,
                include_values=not args.no_ssm_values,
                output_fmt=args.output,
            )
            print_output(headers, rows, args.output)
            printed_ssm = True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            print(f"Erro SSM (describe_parameters): {code} — {e}", file=sys.stderr)
            exit_code = 1

    if args.what in ("both", "secrets"):
        if args.what == "both" and printed_ssm:
            print(file=sys.stdout)
        print("=== Secrets Manager ===", file=sys.stderr)
        try:
            sm = session.client("secretsmanager")
            region = getattr(sm.meta, "region_name", None) or "(região indefinida)"
            headers, rows = list_secrets(
                sm,
                include_deleted=args.secrets_include_deleted,
                include_values=not args.no_secret_values,
                output_fmt=args.output,
            )
            if not rows:
                print(
                    f"Aviso: nenhum secret listado na região «{region}». "
                    "Secrets Manager é regional — confira --region e AWS_REGION / profile. "
                    "Políticas IAM com condição por tag também podem retornar lista vazia. "
                    "Se os secrets foram agendados para remoção, tente --secrets-include-deleted.",
                    file=sys.stderr,
                )
            else:
                print(f"(região {region}, {len(rows)} secret(s))", file=sys.stderr)
            print_output(headers, rows, args.output)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            print(f"Erro Secrets Manager: {code} — {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
