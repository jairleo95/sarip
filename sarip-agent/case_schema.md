# Diseño del Case File (Schema Estructurado)

El "Case File" es el corazón y el único estado mutable del backend de SARIP. Contiene el ticket original dictado por el humano, e iterativamente se va rellenando con evidencias concretas, queries en crudo y deducciones obtenidas de Playbooks.

El esquema base del JSON garantiza rigor y evita alucinaciones del modelo.

## 1. JSON Schema (Estructura Base)

```json
{
  "ticket": {
    "ticket_id": "string (ex: TCK-84930)",
    "reported_issue": "string",
    "operations_to_investigate": ["string"],
    "created_at": "ISO-8601 Timestamp"
  },
  "context_rag": {
    "identified_company_id": "string (ex: AGUACORP_01)",
    "matched_playbooks": [
      {
        "title": "string",
        "doc_id": "string",
        "relevance_score": "float"
      }
    ],
    "historical_similar_cases": ["string"]
  },
  "investigation": {
    "db_ledger_status": {
      "transaction_id": "string",
      "internal_status": "string (ex: AUTHORIZED, REJECTED, CANCELLED)",
      "amount": "float",
      "currency": "string",
      "updated_at": "ISO-8601 Timestamp"
    },
    "telemetry_traces": [
      {
        "trace_id": "string",
        "span_id": "string",
        "service_name": "string",
        "http_status_code": "integer",
        "exception_class": "string",
        "stacktrace_snippet": "string"
      }
    ],
    "reconciliation_diffs": [
      {
        "file_name": "string",
        "bank_status": "string",
        "company_status": "string (ex: NOT_FOUND_IN_FILE)"
      }
    ],
    "audit_trail": [
      {
        "agent": "string",
        "action_intent": "string",
        "parameters": "dict",
        "timestamp": "ISO-8601 Timestamp"
      }
    ]
  },
  "synthesis": {
    "failure_mode": "string (Enum: HTTP_502, DB_TIMEOUT, RECON_MISMATCH, etc.)",
    "owner": "string (Enum: BANK_APP, BANK_INFRA, SERVICE_COMPANY, CLIENT)",
    "severity": "string (Enum: LOW, MEDIUM, HIGH, CRITICAL)",
    "timeline": [
      "string (ex: [10:02:11] Débito CBS exitoso - Auth id: 119)",
      "string (ex: [10:02:22] Timeout HTTP 504 de la empresa)"
    ],
    "root_cause": "string",
    "evidences": ["string (ex: LogLine 441 in AguaCorpClient.java)"],
    "recommended_action": "string (Enum: REVERSE_DEBIT, RETRY_PAYMENT, ESCALATE_L3, MANUAL_RECONCILIATION)",
    "confidence_score": "float (0.0 to 1.0)",
    "requires_human_approval": "boolean"
  }
}
```

## 2. PII Sanitization Mapping (Seguridad Transitoria)

Para evitar fugas de datos al modelo (Prompt Leaking) y cumplir con PCI DSS / ISO 27001, cada "Case File" se expone de una manera al LLM, y de otra a la base de datos interna o al humano.

### En tránsito al LLM (El prompt)

El agente verá algo como:
*"El usuario `[CLIENT_NAME_1]` reportó que se le debitaron `[AMOUNT_1]` de su cuenta `[ACCOUNT_NUMBER_1]` hacia el servicio `[COMPANY_NAME_1]`."*

### Encriptado en Memoria (El Map de Reemplazo temporal)

```json
{
  "PII_VAULT_MAP": {
    "[CLIENT_NAME_1]": "cTf...aXp=", // Cifrado simétrico
    "[AMOUNT_1]": "yZ2...8qw=",
    "[ACCOUNT_NUMBER_1]": "kL1...0pa=",
    "[COMPANY_NAME_1]": "eF2...1zx="
  }
}
```

*Se revierte al momento de generar la salida (Output) del LangGraph hacia el Front-End.*

## 3. Estados de Negocio Core (`failure_mode`)

El orquestador debe clasificar el incidente sí o sí dentro de un catálogo canónico bancario. A continuación ejemplos de `failure_mode` que el Juez debe mapear:

* **TIMEOUT_WITH_DEBIT_APPLIED:** Plataforma de banco cobró, pero la API de la empresa demoró más de >15s y se cortó la llamada. Cliente indignado pero con razón. (*Target usual: Reverse_Debit*).
* **RECONCILIATION_TRUNCATED_FILE:** Error masivo en procesamiento de madrugada (Batch D+1) porque la empresa de servicio mandó mal el formato de Trama. (*Target usual: Escalate_L3_Company*).
* **CLIENT_REJECTED_NSF:** Insuficiencia de fondos (Non-Sufficient Funds). El cliente reclama, pero los logs de contabilidad dicen que su saldo era menor a la cuota a pagar. (*Target usual: Resolve_with_Evidence*).
