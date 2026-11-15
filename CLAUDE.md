# CLAUDE.md — odoo-investing-module

Contexto para Claude Code (VS Code / CLI). Léelo entero antes de tocar código.

## 1. Qué es este proyecto

Módulo Odoo **`investing`** para seguir una cartera de inversión (acciones, ETF, cripto) y
estimar la fiscalidad española de las ventas:

- Precios y su histórico vía `yfinance` (cron diario + botón de sincronizar).
- Compras/ventas con **FIFO obligatorio** (art. 37.2 LIRPF): `investing.buy.sell.history`.
- **Estimación del impuesto anual** por inversiones (`investing.tax.year`) con escalas
  **parametrizables** por régimen y ejercicio (`investing.tax.scale`).

Es a la vez un proyecto de aprendizaje y una base para venderlo como servicio de la
consultora: prioriza código mantenible, migrable y fiscalmente defendible.

| Parámetro | Valor |
|---|---|
| Odoo | **19.0** Community (`version` del manifest: `19.0.x.y.z`) |
| Python | 3.12+ |
| Licencia | LGPL-3 |
| Nombre técnico | `investing` → la carpeta del módulo **debe** llamarse `investing` |
| Dependencias | `base` · Python: `yfinance` (declarada en `external_dependencies`) |

## 2. Mapa del código

```
models/
  company.py           investing.company  (activo: ticker, precio, divisa como Char)
  price_history.py     investing.price.history
  portfolio.py         investing.portfolio (posición) + sell() FIFO
  buy_sell_history.py  investing.buy.sell.history (lotes de compra y ventas)
  tax_scale.py         investing.tax.scale(+.line)  escalas por régimen/año
  tax_year.py          investing.tax.year(+.line)   estimación fiscal anual
services/
  tax_engine.py        aritmética fiscal PURA (sin Odoo) → testeable aislada
  yfinance_service.py  integración externa (import protegido)
wizard/                venta desde la posición
data/investing_tax_scale_data.xml   tipos vigentes (noupdate) — revisar cada año
tests/                 test_tax_engine, test_fifo, test_tax_year
```

## 3. Reglas de dominio (no negociables)

1. **FIFO**: una venta solo consume lotes con `date <= fecha venta`, ordenados por
   `date, id`. Vender más de lo poseído ⇒ `UserError`. Cantidades con `float_compare`
   / `float_is_zero` y `QTY_DIGITS = 8` (cripto fraccionada).
2. **Los tipos impositivos NUNCA van en código**. Viven en `investing.tax.scale`. Para un
   ejercicio nuevo: duplicar la escala (el `copy()` sube el año) o añadir un registro en
   `data/investing_tax_scale_data.xml`. Antes, verificar la norma con la skill
   `hacienda-inversiones`.
3. `services/tax_engine.py` no importa Odoo. Si añades una regla fiscal, va primero ahí
   con su test unitario y después se conecta desde el modelo.
4. Fechas: Odoo guarda `Datetime` en UTC; el ejercicio fiscal se corta en hora local
   (`_get_utc_bounds`). No compares años con `date.year` sobre el valor UTC.
5. Toda cifra fiscal mostrada al usuario es **estimación orientativa**, nunca asesoramiento.
   Mantén los avisos de la vista.

### Limitaciones conocidas (documentadas a propósito, no "arreglarlas" sin plan)

- No hay comisiones ni conversión a EUR por operación (aviso `has_foreign_currency`).
- Regla de los 2 meses simplificada: difiere la pérdida en proporción a las compras
  homogéneas en ±2 meses; no reintegra la pérdida diferida al vender esas acciones.
  No distingue cotizados (2 meses) de no cotizados (1 año).
- Sin titular (`owner`) ni `company_id`/`ir.rule`: todo se calcula sobre todos los datos.
- `investing.portfolio` duplica estado (shares/purchase_price) y su `create()` fusiona
  posiciones existentes; deuda heredada.
- Regímenes soportados: IRPF territorio común y IRNR sin EP. Forales y sociedades (IS) no.

## 4. Hoja de ruta acordada

1. **Estructura OCA**: repo generado con `copier copy --trust gh:oca/oca-addons-repo-template .`,
   módulo en `investing/`, `readme/` (DESCRIPTION.md, USAGE.md, CONTRIBUTORS.md),
   `wizards/`, XML IDs `<model>_view_form|list|search`, `<model>_action`, pre-commit.
2. **Motor FIFO recalculable**: `investing.transaction` + `investing.fifo.match`
   (venta↔compra, cantidad, coste EUR, valor transmisión EUR). Posición calculada, no editable.
   Titular + multi-compañía + record rules.
3. **Fiscalidad completa**: comisiones, EUR con `res.currency`, regla 2 meses exacta con
   reintegro, tipo de activo (cotizado/no cotizado/cripto), informe para Renta Web.
4. Importadores CSV de brókers, dashboard, alertas.

No mezcles fases en un mismo PR.

## 5. Convenciones (resumen OCA)

- Código, nombres y docstrings en **inglés**; textos de UI en inglés + `i18n/es.po`.
- Orden en la clase: atributos privados → `_default_*` → campos → `_compute_*` →
  constraints/onchange → CRUD → `action_*` → `_metodos_negocio`.
- `string=` solo si difiere del nombre autogenerado (pylint-odoo W8113).
- Type hints en métodos públicos y de negocio; `self.env._("...", **kw)` para traducir
  (nunca f-strings dentro de la cadena traducible).
- Constraints SQL con `models.Constraint(...)` (19.0), no `_sql_constraints`.
- Vistas: `<list>`, `invisible="expr"`, nada de `attrs`.
- Todo modelo nuevo ⇒ líneas en `security/ir.model.access.csv` (user lectura, manager CRUD).
- Sin `search()` dentro de bucles; sin `cr.commit()`; excepciones concretas, nunca
  `except Exception: pass`. En crons que iteran registros: `with self.env.cr.savepoint():`.
- Commits: `[ADD]|[IMP]|[FIX]|[REF]|[MIG] investing: descripción en inglés`.
  Ramas: `19.0-imp-investing-<tema>`.

## 6. Comandos

```bash
# Instalar/actualizar y ejecutar SOLO los tests del módulo
#  -u: actualiza el módulo · --test-tags=/investing: filtra por módulo
#  --stop-after-init: termina al acabar (útil en CI)
odoo-bin -c odoo.conf -d test_investing -u investing \
  --test-enable --test-tags=/investing --stop-after-init

# Linters que usa la OCA
pylint --load-plugins=pylint_odoo --disable=all --enable=odoolint \
  --valid-odoo-versions=19.0 investing
ruff check . && ruff format --check .
```

Si el repo aún no está en una carpeta `investing/`, crea un symlink en tu addons_path:
`ln -s /ruta/odoo-investing-module /ruta/addons/investing`.

## 7. Skills de este repo

- `/odoo-module-generator` — scaffolding y revisión de módulos/modelos con convención OCA.
- `/hacienda-inversiones` — verificar la normativa fiscal vigente según el tipo de inversor
  y traducirla a escalas/reglas del módulo.

## 8. Cómo debes trabajar aquí

1. Antes de desarrollar: ¿lo resuelve el estándar de Odoo o un módulo OCA? Dilo.
2. Si una API de Odoo 19 no te consta, compruébala en el código fuente de la rama 19.0
   antes de usarla. No inventes métodos.
3. Con alternativas técnicas, tabla con: *Impacto en tiempos de entrega · Mantenibilidad
   a largo plazo · Coste de desarrollo · Cuándo elegirla*.
4. Ningún cambio en lógica FIFO o fiscal sin test que lo cubra. Ejecuta los tests antes de
   dar algo por terminado.
5. Normativa fiscal: jamás de memoria. Usa la skill `hacienda-inversiones`, cita fuente
   oficial (BOE, AEAT, DGT) y fecha de verificación.
