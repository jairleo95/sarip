# Playbook Genérico: Fallos de Infraestructura Core

## Descripción
Cubre cualquier escenario de pago de servicios donde la falla principal radique en componentes internos del banco o picos de latencia, no en validaciones del comercio externo.

6. ## Failure Modes Conocidos
7. 1. **INTERNAL_DB_LOCK:** Deadlock en la tabla de Ledger. El estado de la transacción se quedó pegado en `INITIATED` o `PENDING`.
8. 2. **K8S_POD_OOMKILL:** El pod o microservicio que hace la orquestación saliente del pago murió por falta de memoria. El trace OpenTelemetry de Splunk va a estar incompleto y mostrará fallos de reinicio.
9. 3. **INSUFFICIENT_FUNDS:** El cliente intentó pagar un servicio pero su cuenta bancaria no tenía el saldo suficiente en el momento del débito. El log mostrará la excepción "Insufficient funds in account".

## Acciones Recomendadas
* **Si es INTERNAL_DB_LOCK:** La transacción nunca se materializó financieramente ni se descontó. Acción recomendada: `REJECT` sin impacto contable, el cliente debe reintentar voluntariamente.
* **Si es K8S_POD_OOMKILL:** Estado Riesgoso. Existe la posibilidad de que la llamada saliente HTTP se haya ejecutado pero no pudimos guardar la respuesta. Se DEBE mandar a `requires_human_approval = True`.
* **Si es INSUFFICIENT_FUNDS:** El débito falló por falta de saldo. La transacción nunca descontó dinero. Acción recomendada: `REJECT_INSUFFICIENT_FUNDS`. El confidence score debe ser alto (0.99) y no requiere aprobación humana (`requires_human_approval = False`).
