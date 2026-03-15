# Playbook Genérico: Fallos de Infraestructura Core

## Descripción
Cubre cualquier escenario de pago de servicios donde la falla principal radique en componentes internos del banco o picos de latencia, no en validaciones del comercio externo.

## Failure Modes Conocidos
1. **INTERNAL_DB_LOCK:** Deadlock en la tabla de Ledger. El estado de la transacción se quedó pegado en `INITIATED` o `PENDING`.
2. **K8S_POD_OOMKILL:** El pod o microservicio que hace la orquestación saliente del pago murió por falta de memoria. El trace OpenTelemetry de Splunk va a estar incompleto y mostrará fallos de reinicio.

## Acciones Recomendadas
* **Si es INTERNAL_DB_LOCK:** La transacción nunca se materializó financieramente ni se descontó. Acción recomendada: `REJECT` sin impacto contable, el cliente debe reintentar voluntariamente.
* **Si es K8S_POD_OOMKILL:** Estado Riesgoso. Existe la posibilidad de que la llamada saliente HTTP se haya ejecutado pero no pudimos guardar la respuesta. Se DEBE mandar a `requires_human_approval = True`.
