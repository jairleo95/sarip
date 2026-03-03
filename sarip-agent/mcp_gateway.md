# Diseño del Tool Gateway / MCP Server

El MCP Server (*Model Context Protocol*) actúa como un proxy seguro, determinista y auditado entre el Grafo LangGraph y los sistemas Core del banco.

Nadie más que este servicio puede acceder a la base de datos de pagos ni a los logs de la empresa. Su función principal es exponer un listado de **Tools (Funciones)** aprobadas y fuertemente tipadas a los agentes.

## 1. Arquitectura del MCP

* **Stack:** Microservicio Java (Quarkus) o Go.
* **Protocolo:** Expone APIs en formato MCP compatible (vía HTTP/SSE o stdio).
* **Seguridad In-bound:** OAUTH2 Client Credentials con Scope `sarip.agent.read`.
* **Seguridad Out-bound:** Conexión por JBDC de Lectura a réplicas PostgreSQL (`RO_User`). Tokens de solo lectura para Splunk SDK / OpenTelemetry API.
* **Rate Limits:** Previene que un agente "loopeando" mate la base de datos de producción con 10,000 queries. (Max 10 req/s por agente).

## 2. Tools (El Arsenal del Investigador)

Los LLMs recibirán las siguientes definiciones de funciones para consumir:

### Herramientas de Base de Datos (Data Investigator)

```json
{
  "name": "get_transaction_lifecycle",
  "description": "Obtiene los montos, fechas, cuentas involucradas y estados históricos (AUTHORIZED, SETTLED, etc.) de una transacción específica.",
  "parameters": {
    "type": "object",
    "properties": {
      "transaction_id": {"type": "string", "description": "ID de la operación (ej. OP-10293)"}
    },
    "required": ["transaction_id"]
  }
}
```

```json
{
  "name": "get_client_claims_history",
  "description": "Busca si el cliente asociado a esta cuenta ha tenido incidentes similares en los últimos 30 días (reincidente).",
  "parameters": {
    "type": "object",
    "properties": {
      "account_hash": {"type": "string", "description": "Hash de la cuenta bancaria (no el string crudo)"}
    },
    "required": ["account_hash"]
  }
}
```

### Herramientas de Observabilidad / Infra (Observability Agent)

```json
{
  "name": "query_application_logs",
  "description": "Ejecuta una búsqueda en Splunk u OpenSearch para encontrar excepciones de Java u OOM Kills asimilables a una operación caída.",
  "parameters": {
    "type": "object",
    "properties": {
      "trace_id": {"type": "string"},
      "time_window_start": {"type": "string", "description": "ISO 8601"},
      "time_window_end": {"type": "string", "description": "ISO 8601"}
    },
    "required": ["trace_id", "time_window_start", "time_window_end"]
  }
}
```

```json
{
  "name": "get_external_api_status",
  "description": "Revisa las métricas de latencia de Gateway del banco hacia la Empresa Comercial en los últimos X minutos.",
  "parameters": {
    "type": "object",
    "properties": {
      "company_id": {"type": "string", "description": "Identificador de facturador (AGUACORP)"},
      "minutes_back": {"type": "integer"}
    },
    "required": ["company_id", "minutes_back"]
  }
}
```

### Herramientas de Inteligencia (Supervisor & RAG)

```json
{
  "name": "search_playbook",
  "description": "Realiza una búsqueda semántica en la base vectorial para obtener pasos estructurados de soporte (SOP) ante un error dado.",
  "parameters": {
    "type": "object",
    "properties": {
      "company_id": {"type": "string"},
      "error_code_or_symptom": {"type": "string"}
    },
    "required": ["company_id", "error_code_or_symptom"]
  }
}
```

## 3. Limitaciones Previstas e Interceptores

El Framework Java del MCP validará forzosamente:

1. **Sanitization:** Validar que los `trace_id` o `transaction_id` enviados por el LLM no contengan inyecciones extrañas `OP-123; DROP TABLE...` (Input Validation clásico).
2. **Size Limits:** Las queries contra Splunk o PostgreSQL **nunca** devolverán más de 50 líneas. Resúmenes (truncados con '...') para no causar un desbordante "Context Window Limit" al agente en su prompt de respuesta.
3. **Circuit Breaker:** Si la réplica de base de datos se vuelve inestable, el MCP devolverá proactivamente al agente: `"DATABASE_CURRENTLY_DOWN. Por favor indica en el Case File que no se logró recolectar la información por caída del servicio core."` en vez de colgar la cola transaccional (Resilience4J).
