# Regímenes fiscales de inversiones — referencia verificada

> **Verificado el 2026-11-15.** Antes de usar cualquier dato, compruébalo de nuevo en la
> fuente oficial (ver SKILL.md). Si cambia algo, actualiza la tabla y la fecha.

## 1. Residente — IRPF territorio común

| Concepto | Regla | Base legal / fuente |
|---|---|---|
| Identificación de títulos | FIFO sobre todos los valores homogéneos del titular, en cualquier entidad | Art. 37.2 LIRPF; DGT V0733-14. TEAC 2025: también en transmisiones lucrativas |
| Valores homogéneos | Mismo emisor, misma naturaleza y régimen de transmisión, mismos derechos | Art. 8 RIRPF |
| Valor de adquisición | Precio + gastos y tributos inherentes (comisiones, cánones) | Art. 35.1 LIRPF; guía CNMV fiscalidad de acciones |
| Valor de transmisión | Precio − gastos inherentes | Art. 35.2 LIRPF |
| Divisa | Convertir a EUR al tipo de cambio de la fecha de cada operación | Manual práctico AEAT |
| Recompra (cotizados) | Pérdida no computable si se adquieren homogéneos ±2 meses; se integra al transmitir los recomprados | Art. 33.5.f LIRPF; DGT V0248-18 (procedimiento en dos fases) |
| Recompra (no cotizados) | Ventana de ±1 año | Art. 33.5.g LIRPF |
| Integración | Ganancias/pérdidas por transmisión → base del ahorro | Art. 46.b LIRPF |
| Compensación cruzada | Saldo negativo de ganancias compensa hasta el 25 % del saldo positivo de RCM (y viceversa) | Art. 49 LIRPF |
| Arrastre | Saldo negativo pendiente: 4 años siguientes | Art. 49 LIRPF |
| Retención en venta de acciones | No hay; sí en reembolso de fondos (19 %) | Art. 101 LIRPF / RIRPF |

**Escala del ahorro (estatal + autonómica, uniforme en territorio común)**

| Base desde (€) | 2023–2024 | 2025 y 2026 |
|---|---|---|
| 0 | 19 % | 19 % |
| 6.000 | 21 % | 21 % |
| 50.000 | 23 % | 23 % |
| 200.000 | 27 % | 27 % |
| 300.000 | 28 % | **30 %** (Ley 7/2024) |

Cuota acumulada a 300.000 €: 71.880 €. Fuentes: Manual práctico Renta AEAT; Ley 7/2024.

## 2. Residente — territorios forales

País Vasco (Álava, Bizkaia, Gipuzkoa) y Navarra tienen **escala y reglas propias** de la
base del ahorro (p. ej. Gipuzkoa 2026: 19 %–28 %). **No soportado en el módulo.** Fuente:
normas forales del IRPF de cada Diputación / Hacienda Foral de Navarra.

## 3. No residente sin establecimiento permanente — IRNR

| Concepto | Regla | Base legal / fuente |
|---|---|---|
| Sujeción | Ganancias de valores emitidos por entidades residentes en España, entre otras | Art. 13.1.i TRLIRNR |
| Cálculo | Normas del IRPF operación por operación; **sin compensar** ganancias con pérdidas | Arts. 24 TRLIRNR; Manual No Residentes AEAT |
| Tipo | 19 % para ganancias por transmisión de elementos patrimoniales | Art. 25.1.f TRLIRNR |
| Exenciones | Residentes UE/EEE (bienes muebles, con excepciones); transmisiones en mercados secundarios oficiales españoles por residentes de países con convenio con cláusula de intercambio de información | Art. 14.1.c e i TRLIRNR |
| Convenios | Normalmente la potestad corresponde solo al Estado de residencia → exento en España | Convenio aplicable (consultar específico) |
| Declaración | Modelo 210 | AEAT |

## 4. Sociedades — Impuesto sobre Sociedades

No usa la base del ahorro ni el FIFO del IRPF: la base imponible parte del **resultado
contable** (art. 10.3 LIS) y la valoración de valores homogéneos sigue el PGC (precio
medio ponderado). Plusvalías de participaciones ≥5 % pueden aplicar la exención del
art. 21 LIS (con reducción del 5 % por gastos de gestión). Tipos: general 25 %, con
tipos reducidos para entidades de nueva creación y de reducida dimensión que **cambian
por ejercicio** (verificar art. 29 LIS vigente). **No soportado en el módulo.**

## 5. Cripto (persona física residente)

- Bienes homogéneos → FIFO (DGT 2025; V0999-18).
- Permuta cripto↔cripto o cripto→bien: ganancia/pérdida con el mayor de los valores de
  mercado (art. 37.1.h LIRPF; V1149-18).
- Recompra: no son "valores" → no aplica literalmente el 33.5.f; doctrina apunta al
  33.5.e (readquisición en el año siguiente). **Criterio no vinculante cerrado.**
- Informativa: modelo 721 (cripto en el extranjero > 50.000 €).

## 6. Obligaciones informativas útiles

- Modelo 720: bienes y derechos en el extranjero > 50.000 € por bloque.
- Modelo 721: monedas virtuales en el extranjero > 50.000 €.
