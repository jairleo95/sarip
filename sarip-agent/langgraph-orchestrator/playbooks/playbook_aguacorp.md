# Playbook: Cortes y Reconexiones AguaCorp

## Descripción
Este documento describe el standard operating procedure (SOP) cuando un cliente reporta que realizó el pago de su recibo de agua (AguaCorp) pero el servicio no se ha restablecido o figura en mora.

## Failure Modes Conocidos
1. **TIMEOUT_BUSINESS:** El pago se descontó correctamente en nuestro banco, hicimos la petición REST hacia AguaCorp, pero su API devolvió un HTTP 504 Gateway Timeout o tardó más de 30 segundos.
2. **REJECTED_ALREADY_PAID:** El cliente pagó la deuda dos veces por accidente (app bancaria y presencial). El Core Bancario lo envía, pero AguaCorp responde HTTP 409 o Error Code 811.

## Acciones Recomendadas
* **Si es TIMEOUT_BUSINESS:** Se debe crear una incidencia interna y retener los fondos. Si al día siguiente (D+1) en la conciliación AguaCorp reporta no tener el pago, aplicar acción `REJECT_AND_REVERSE_DEBIT` devolviendo el saldo al cliente.
* **Si es REJECTED_ALREADY_PAID:** Confirmar el código HTTP 409 en los traces. Acción: `REJECT_AND_REVERSE_DEBIT` inmediatamente.
