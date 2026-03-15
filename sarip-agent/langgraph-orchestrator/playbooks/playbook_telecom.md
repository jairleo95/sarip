# Playbook: Telecomunicaciones (Claro, Movistar)

## Descripción
Incidentes relacionados con pagos de líneas de telefonía fija o planes móviles postpago.

## Failure Modes Conocidos
1. **BILL_NOT_FOUND:** El cliente intenta pagar una deuda, pero la API Telecom devuelve HTTP 404 (Recibo no encontrado).
2. **RECONCILIATION_MISMATCH:** El cliente pagó, el Core lo registró `SETTLED`, la API de la empresa dio éxito (HTTP 200), pero al día siguiente Telecom manda un archivo SFTP diciendo que no recibió el pago.

## Acciones Recomendadas
* **Si es BILL_NOT_FOUND:** El UUID facturador enviado por nuestro banco podría estar corrupto o inactivo en su lado. Acción: Requiere que `requires_human_approval` sea `True`.
* **Si es RECONCILIATION_MISMATCH:** Este es el caso más crítico (queja de Indecopi inminente). El agente debe forzar un Extorno Manual o contactar a Telecom. El Confidence Score nunca debe superar el 0.8. Acción: `MANUAL_RECONCILIATION`.
