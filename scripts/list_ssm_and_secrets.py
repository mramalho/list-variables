#!/usr/bin/env python3
"""Lista metadata de SSM Parameter Store e Secrets Manager (sem valores secretos).

Uso com UV (na raiz do repositório):

    uv sync
    uv run python scripts/list_ssm_and_secrets.py --help
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

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


def format_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat(timespec="seconds")
    return str(dt)


def truncate(text: str | None, max_len: int = 80) -> str:
    if not text:
        return ""
    s = text.replace("\n", " ").replace("\t", " ")
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def list_ssm_parameters(ssm_client, prefix: str | None) -> tuple[list[str], list[list[object]]]:
    paginator = ssm_client.get_paginator("describe_parameters")
    paginate_kwargs: dict = {}
    if prefix:
        paginate_kwargs["ParameterFilters"] = [
            {"Key": "Name", "Option": "BeginsWith", "Values": [prefix]},
        ]
    rows: list[list[object]] = []
    headers = ["Name", "Type", "Tier", "Version", "LastModifiedDate"]
    for page in paginator.paginate(**paginate_kwargs):
        for p in page.get("Parameters", []):
            rows.append(
                [
                    p.get("Name", ""),
                    p.get("Type", ""),
                    p.get("Tier", ""),
                    p.get("Version", ""),
                    format_dt(p.get("LastModifiedDate")),
                ]
            )
    return headers, rows


def list_secrets(sm_client) -> tuple[list[str], list[list[object]]]:
    paginator = sm_client.get_paginator("list_secrets")
    rows: list[list[object]] = []
    headers = ["Name", "ARN", "Description", "LastChangedDate", "RotationEnabled"]
    for page in paginator.paginate():
        for s in page.get("SecretList", []):
            rows.append(
                [
                    s.get("Name", ""),
                    s.get("ARN", ""),
                    truncate(s.get("Description")),
                    format_dt(s.get("LastChangedDate")),
                    s.get("RotationEnabled", ""),
                ]
            )
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
            "Lista metadata de SSM Parameter Store e AWS Secrets Manager "
            "(sem GetParameter/GetSecretValue; não exibe valores)."
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
            headers, rows = list_ssm_parameters(ssm, args.ssm_prefix)
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
            headers, rows = list_secrets(sm)
            print_output(headers, rows, args.output)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            print(f"Erro Secrets Manager (list_secrets): {code} — {e}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
