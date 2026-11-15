---
name: hacienda-inversiones
description: Verificar la normativa fiscal española vigente sobre inversiones (acciones, ETF, fondos, cripto) según el tipo de inversor - residente IRPF común o foral, no residente IRNR, sociedad IS - y traducirla a escalas y reglas del módulo investing. Usar al preparar un nuevo ejercicio fiscal, añadir un régimen, revisar un cálculo o responder dudas de tributación de inversiones.
---

# Fiscalidad de inversiones en España (por tipo de inversor)

Objetivo: que cada número que calcula el módulo `investing` tenga **una regla, una fuente
oficial y una fecha de verificación**. Esta skill no sustituye a un asesor fiscal; lo
dices siempre en la conclusión.

## Regla de oro

**Nunca de memoria.** Los tipos y umbrales cambian casi cada año (p. ej. el último tramo
del ahorro pasó del 28 % al 30 % en 2025). Antes de afirmar un tipo, un plazo o una
exención, búscalo y cita la fuente. `references/regimenes.md` es un punto de partida
verificado en una fecha concreta, no la verdad actual.

Fuentes por orden de prioridad:
1. **BOE** (texto consolidado): Ley 35/2006 IRPF, RD 439/2007 RIRPF, RDLeg 5/2004
   TRLIRNR, Ley 27/2014 LIS, normas forales.
2. **AEAT**: *Manual práctico de Renta <año>* (cap. 11 ganancias y pérdidas; cap. 16
   escalas) y *Manual de Tributación de No Residentes*.
3. **DGT**: consultas vinculantes (buscador PETETE). Cita el número (`V0999-18`).
4. TEAC / Tribunal Supremo cuando haya doctrina contradictoria.
Blogs y foros solo para orientarte; nunca como fuente final.

## Paso 1 — Clasificar al inversor

Pregunta (o deduce del contexto) y fija UNA categoría:

| Pregunta | Categorías resultantes |
|---|---|
| ¿Persona física o sociedad? | Física → IRPF/IRNR · Sociedad → IS |
| ¿Residente fiscal en España? (>183 días o centro de intereses) | Residente → IRPF · No → IRNR |
| Si es residente: ¿dónde? | Territorio común · País Vasco (Álava, Bizkaia, Gipuzkoa) · Navarra |
| Si no es residente: ¿de dónde? | UE/EEE con intercambio de información · Estado con convenio · Resto |
| ¿Régimen especial? | Impatriados (art. 93 LIRPF), >65 con reinversión en renta vitalicia, etc. |

## Paso 2 — Clasificar el activo y la operación

- Acciones / ETF **cotizados** en mercado regulado (o equivalente) → recompra 2 meses.
- Valores **no cotizados** y fondos no cotizados → recompra 1 año.
- **Fondos de inversión** (IIC): traspasos entre fondos sin tributar para residentes
  (art. 94 LIRPF) → el FIFO sigue la cadena de traspasos.
- **Cripto**: bienes homogéneos con FIFO; permutas cripto↔cripto tributan
  (art. 37.1.h). La recompra de 2 meses (33.5.f) no aplica literalmente; posible 33.5.e
  (readquisición en el año siguiente). Criterio no cerrado → márcalo como incierto.
- Derechos de suscripción, acciones liberadas, splits, scrip dividends: reglas propias
  (art. 37.1.a y b). El módulo aún no los soporta → avisa.

## Paso 3 — Determinar las reglas aplicables

Para la categoría elegida, obtén y verifica:
1. **Identificación de títulos** (FIFO en IRPF; en IS manda la contabilidad).
2. **Valor de adquisición y de transmisión**: incluyen gastos y comisiones inherentes;
   conversión a EUR al tipo de cambio de cada fecha.
3. **Integración y compensación**: saldo de ganancias y pérdidas del ahorro; % de
   compensación cruzada con rendimientos del capital mobiliario; años de arrastre.
4. **Pérdidas no computables**: recompra (2 meses / 1 año), donaciones, etc.
5. **Escala o tipo**: tramos y tipos del ejercicio concreto.
6. **Exenciones**: convenio, UE/EEE, art. 21 LIS…
7. **Obligaciones formales**: modelo 100, 210, 200, 720, 721.

## Paso 4 — Traducir al módulo `investing`

| Si la regla es… | Dónde va en el código |
|---|---|
| Tramos/tipos de un ejercicio nuevo | Registro en `data/investing_tax_scale_data.xml` (o duplicar escala en la UI). Nunca en Python |
| Nuevo régimen (p. ej. foral Gipuzkoa) | Valor nuevo en `TAX_REGIMES` (`models/tax_scale.py`) + escala en datos + rama en `_compute_estimation` si cambia la compensación |
| Regla de compensación/arrastre | Función pura en `services/tax_engine.py` + test en `tests/test_tax_engine.py` |
| Regla de pérdidas no computables | `_prepare_line_vals` en `models/tax_year.py` + test en `tests/test_tax_year.py` |
| Algo que el módulo no puede calcular | Campo de entrada manual con `help=` que cite la casilla de Renta Web, o aviso en la vista |

Cada cambio lleva: test con un caso numérico comprobado a mano, comentario con la
referencia legal (artículo + fuente) y actualización de la fecha en la cabecera del XML.

## Paso 5 — Entregable

Responde con esta estructura:

1. **Perfil**: categoría de inversor y activo.
2. **Tabla de reglas**: `Concepto | Regla | Fuente (enlace) | Verificado el`.
3. **Ejemplo numérico** con el resultado esperado.
4. **Impacto en el módulo**: ficheros a tocar y tests a añadir (si aplica).
5. **Incertidumbres**: criterios no consolidados o que dependen de hechos concretos.
6. Aviso: "Estimación técnica, no asesoramiento fiscal; contrastar con un asesor y con
   el borrador oficial".

## Comprobación anual (checklist de enero)

- [ ] Escala del ahorro del nuevo ejercicio (estatal + autonómica = común) verificada.
- [ ] Tipo IRNR para ganancias por transmisión verificado.
- [ ] % de compensación cruzada y años de arrastre sin cambios.
- [ ] Escalas forales si hay clientes forales.
- [ ] Nuevo registro de escala + test que falle si falta la escala del año.
- [ ] `references/regimenes.md` actualizado con la fecha.
