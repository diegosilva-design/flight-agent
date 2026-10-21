#!/usr/bin/env python3
"""Evalúa opciones de vuelo en efectivo, puntos o mixto y las rankea por costo efectivo.

Uso:
    python scripts/evaluate.py data/runs/<carpeta>/options.json [--include-unverified]

Escribe ranking.json y report.md junto al options.json e imprime el reporte.
Requiere PyYAML (pip install pyyaml).
"""
import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def active_bonus(wallet, src, dst, today):
    best = 0.0
    for b in wallet.get("transfer_bonuses") or []:
        if b.get("from") != src or b.get("to") != dst:
            continue
        exp = b.get("expires")
        if exp:
            try:
                if dt.date.fromisoformat(str(exp)) < today:
                    continue
            except ValueError:
                pass
        best = max(best, float(b.get("bonus_pct", 0)))
    return best


def fund(points, program, currency, wallet, today):
    """Devuelve el mejor plan para financiar `points` del programa (o de una moneda directa)."""
    currencies = wallet.get("currencies", {})
    if currency:
        sources = [{"currency": currency, "ratio": 1.0}]
    else:
        prog = (wallet.get("award_programs") or {}).get(program)
        if prog:
            sources = prog.get("sources", [])
        elif program in currencies:
            sources = [{"currency": program, "ratio": 1.0}]
        else:
            sources = []
    plans = []
    for s in sources:
        info = currencies.get(s["currency"])
        if not info:
            continue
        bonus = 0.0 if s["currency"] == program else active_bonus(wallet, s["currency"], program, today)
        ratio = float(s["ratio"]) * (1 + bonus / 100)
        needed = math.ceil(points / ratio)
        plans.append({
            "currency": s["currency"],
            "points_used": needed,
            "value_usd": needed * float(info["cpp"]) / 100,
            "cpp": float(info["cpp"]),
            "bonus_pct": bonus,
            "balance": int(info.get("balance", 0)),
            "feasible": int(info.get("balance", 0)) >= needed,
            "shortfall": max(0, needed - int(info.get("balance", 0))),
        })
    if not plans:
        return None
    ok = [p for p in plans if p["feasible"]]
    return min(ok, key=lambda p: p["value_usd"]) if ok else min(plans, key=lambda p: p["shortfall"])


def fmt_dur(m):
    return f"{m // 60}h{m % 60:02d}" if m else "n/d"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("options")
    ap.add_argument("--wallet", default=str(ROOT / "config" / "wallet.yaml"))
    ap.add_argument("--prefs", default=str(ROOT / "config" / "preferences.yaml"))
    ap.add_argument("--include-unverified", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    data = json.loads(Path(args.options).read_text(encoding="utf-8"))
    wallet, prefs = load_yaml(args.wallet), load_yaml(args.prefs)
    today = dt.date.today()
    search = data.get("search", {})
    cabin = (search.get("cabin") or prefs.get("default_cabin") or "economy").lower()
    max_stops = prefs.get("max_stops", 2)
    tv = float(prefs.get("time_value_per_hour", 0))
    sp = float(prefs.get("stop_penalty", 0))
    bp = float(prefs.get("basic_economy_penalty", 0)) if prefs.get("avoid_basic_economy") else 0.0

    excluded, pool = [], []
    for o in data.get("options", []):
        reason = None
        if o.get("unverified") and not args.include_unverified:
            reason = "no verificada"
        elif (o.get("cabin") or cabin).lower() != cabin:
            reason = f"cabina distinta ({o.get('cabin')})"
        elif o.get("stops", 0) > max_stops:
            reason = f"{o['stops']} escalas (> {max_stops})"
        elif o.get("type") not in ("cash", "award", "points_and_cash"):
            reason = f"tipo desconocido ({o.get('type')})"
        (excluded if reason else pool).append((o, reason) if reason else o)

    def key_exact(o):
        # Mismo vuelo: itinerary_key explícito, o misma aerolínea + ruta + fechas.
        return o.get("itinerary_key") or (
            o.get("airline"), o.get("route"), o.get("depart_date"), o.get("return_date"))

    def key_general(o):
        # Respaldo: mismo origen/destino/fechas (cash más barato de cualquier aerolínea).
        return (o.get("origin"), o.get("destination"), o.get("depart_date"), o.get("return_date"))

    cash_exact, cash_general = {}, {}
    for o in pool:
        if o["type"] == "cash":
            for table, k in ((cash_exact, key_exact(o)), (cash_general, key_general(o))):
                if k not in table or o["cash_price"] < table[k]:
                    table[k] = o["cash_price"]

    def cash_reference(o):
        return cash_exact.get(key_exact(o), cash_general.get(key_general(o)))

    durations = [o["duration_min"] for o in pool if o.get("duration_min")]
    fastest = min(durations) if durations else 0

    results = []
    for o in pool:
        r = {k: o.get(k) for k in (
            "id", "type", "airline", "route", "origin", "destination", "depart_date",
            "return_date", "stops", "duration_min", "fare_type", "program", "source", "link")}
        notes = []
        plan = None
        if o["type"] == "cash":
            cash_out, pts_value, pts_used = float(o["cash_price"]), 0.0, 0
        else:
            cash_out = float(o.get("taxes_fees", o.get("cash", 0)))
            pts = int(o["points"])
            plan = fund(pts, o.get("program"), o.get("currency"), wallet, today)
            if plan is None:
                r.update(feasible=False)
                notes.append("sin fuente de puntos en wallet.yaml")
                pts_value, pts_used = float("inf"), 0
            else:
                pts_value, pts_used = plan["value_usd"], plan["points_used"]
                r["funding"] = plan
                if plan["bonus_pct"]:
                    notes.append(f"bono de transferencia {plan['bonus_pct']:.0f}% aplicado")
                if not plan["feasible"]:
                    notes.append(f"faltan {plan['shortfall']:,} pts de {plan['currency']}")

        time_pen = ((o.get("duration_min", fastest) - fastest) / 60) * tv if fastest else 0.0
        stop_pen = o.get("stops", 0) * sp
        basic_pen = bp if str(o.get("fare_type", "")).lower() in ("basic", "basic economy") else 0.0
        eff = cash_out + pts_value + time_pen + stop_pen + basic_pen

        ref = cash_reference(o) if o["type"] != "cash" else None
        cpp = decision = None
        if ref is not None and pts_used:
            cpp = (ref - cash_out) / pts_used * 100
            decision = "USAR PUNTOS" if cpp >= plan["cpp"] else "PAGAR CASH"
        elif o["type"] != "cash":
            notes.append("sin tarifa cash comparable para medir cpp")

        r.update(
            cash_out=round(cash_out, 2),
            points_used=pts_used,
            points_value=None if math.isinf(pts_value) else round(pts_value, 2),
            time_penalty=round(time_pen, 2),
            stop_penalty=round(stop_pen + basic_pen, 2),
            effective_cost=None if math.isinf(eff) else round(eff, 2),
            cash_reference=ref,
            realized_cpp=None if cpp is None else round(cpp, 2),
            decision=decision,
            feasible=True if o["type"] == "cash" else bool(plan and plan["feasible"]),
            notes=notes,
        )
        results.append(r)

    feasible = sorted([r for r in results if r["feasible"] and r["effective_cost"] is not None],
                      key=lambda r: r["effective_cost"])
    infeasible = [r for r in results if r not in feasible]

    def pick(rows, keyfn):
        return min(rows, key=keyfn) if rows else None

    highlights = {
        "mejor_valor_global": pick(feasible, lambda r: r["effective_cost"]),
        "menor_desembolso_cash": pick(feasible, lambda r: r["cash_out"]),
        "menos_puntos_quemados": pick([r for r in feasible if r["points_used"]], lambda r: r["points_used"]),
        "mas_rapida": pick([r for r in feasible if r["duration_min"]], lambda r: r["duration_min"]),
    }

    out_dir = Path(args.options).parent
    (out_dir / "ranking.json").write_text(
        json.dumps({"search": search, "ranking": feasible, "not_feasible": infeasible,
                    "excluded": [{"id": o.get("id"), "reason": why} for o, why in excluded],
                    "highlights": {k: (v or {}).get("id") for k, v in highlights.items()}},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    md = []
    md.append(f"# Reporte de vuelos — {search.get('origin','?')} → {search.get('destination','?')}")
    md.append(f"Fechas: {search.get('depart','?')} / {search.get('return','solo ida')} · cabina: {cabin} · "
              f"generado {today.isoformat()}\n")
    md.append("## Ranking por costo efectivo (cash + valor de puntos + penalización de tiempo/escalas)\n")
    md.append("| # | ID | Método | Ruta | Escalas | Dur | Cash | Puntos usados | cpp | Costo efectivo | Veredicto |")
    md.append("|---|----|--------|------|---------|-----|------|---------------|-----|----------------|-----------|")
    for i, r in enumerate(feasible[: args.top], 1):
        method = {"cash": "Cash", "award": "Premio", "points_and_cash": "Mixto"}[r["type"]]
        pts = f"{r['points_used']:,} {r['funding']['currency']}" if r["points_used"] else "—"
        md.append(f"| {i} | {r['id']} | {method} | {r['route']} {r['depart_date']} | {r['stops']} | "
                  f"{fmt_dur(r['duration_min'])} | ${r['cash_out']:,.0f} | {pts} | "
                  f"{r['realized_cpp'] if r['realized_cpp'] is not None else '—'} | "
                  f"${r['effective_cost']:,.0f} | {r['decision'] or '—'} |")
    md.append("\n## Destacados")
    labels = {"mejor_valor_global": "Mejor valor global", "menor_desembolso_cash": "Menor desembolso en cash",
              "menos_puntos_quemados": "Menos puntos quemados", "mas_rapida": "Más rápida"}
    for k, v in highlights.items():
        if v:
            md.append(f"- **{labels[k]}**: {v['id']} ({v['route']}, ${v['cash_out']:,.0f} cash, "
                      f"{v['points_used']:,} pts, costo efectivo ${v['effective_cost']:,.0f})")
    if infeasible:
        md.append("\n## No financiables con tu saldo actual")
        for r in infeasible:
            md.append(f"- {r['id']} ({r['route']}): {'; '.join(r['notes']) or 'sin detalle'}")
    if excluded:
        md.append("\n## Excluidas")
        for o, why in excluded:
            md.append(f"- {o.get('id')}: {why}")
    notes = [(r["id"], n) for r in feasible[: args.top] for n in r["notes"]]
    if notes:
        md.append("\n## Notas")
        for i, n in notes:
            md.append(f"- {i}: {n}")
    md.append("\n_Los precios y la disponibilidad cambian en minutos: confirma en vivo antes de reservar o "
              "transferir puntos (las transferencias son irreversibles)._")
    report = "\n".join(md)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
