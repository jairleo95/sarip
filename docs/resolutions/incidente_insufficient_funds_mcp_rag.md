# Resolución: Correlación de Logs (MDC) y Mejora de Búsqueda Vectorial (RAG) para LangGraph

**Fecha:** 2026-03-17
**Problema Principal:** El agente LangGraph (SARIP) no lograba diagnosticar correctamente tickets relacionados con fondos insuficientes (`INSUFFICIENT_FUNDS`), clasificándolos erróneamente por defecto (ej. `TIMEOUT_BUSINESS` o errores desconocidos).

---

## 1. Análisis de Causa Raíz (RCA Técnico)

Durante la auditoría del flujo de resolución de incidentes End-to-End, se detectaron tres puntos de falla en la cadena de visibilidad y razonamiento del Agente:

1. **Pérdida de Trazabilidad en Backend Java (Quarkus):**
   Las excepciones de negocio como "Insufficient funds" se lanzaban y registraban en Kibana, pero carecían del campo `trace_id` necesario para correlacionarlas con la transacción original.
2. **Búsqueda Ineficiente en MCP Gateway (Elasticsearch):**
   El servidor MCP (TypeScript/Python) buscaba el identificador de la transacción dentro del cuerpo del mensaje (`message: trace-xyz`) en vez de usar el campo estructurado indexado.
3. **Pérdida de Contexto en Búsqueda Vectorial (RAG):**
   El clasificador cognitivo (`agent.py`) recuperaba los logs técnicos exitosamente, pero al momento de buscar el procedimiento adecuado en los Playbooks (ChromaDB), **solo utilizaba la descripción original del usuario** como query de búsqueda, ignorando la evidencia técnica recopilada.

---

## 2. Solución Implementada (Step-by-Step)

### A. Trazabilidad en Backend (Java / JBoss Logging)
Se implementó el patrón **Mapped Diagnostic Context (MDC)** para asegurar que todos los logs generados en el ciclo de vida de un request hereden los metadatos de correlación.

*   **Implementación:** En `PaymentResource.java` y `DebtResource.java`.
*   **Fix:**
    ```java
    try {
        MDC.put("trace_id", tx.id.toString()); 
        // Lógica de negocio y persistencia
    } finally {
        MDC.remove("trace_id"); // Prevención de context leak en el Thread Pool
    }
    ```

### B. Corrección de Queries Elasticsearch (MCP Servers)
Se estandarizó la consulta en el protocolo MCP para evitar búsquedas de string match ineficientes.

*   **Implementación:** En `mcp-gateway/server.py` y `mcp_client.py`.
*   **Fix:** Se modificó la Query DSL de Elasticsearch para emparejar el campo exacto:
    ```json
    // Antes: { "match": { "message": trace_id } }
    // Después:
    { "match": { "trace_id": trace_id } }
    ```
    *Nota:* Se eliminó también la lógica estática que añadía el prefijo "trace-" asumiendo formatos legacy.

### C. Enriquecimiento del Contexto RAG (LangGraph)
Para garantizar que el modelo LLM recupere los documentos correctos del manual, el query de embeddings fue enriquecido con la telemetría.

*   **Implementación:** En `sarip-agent/langgraph-orchestrator/agent.py`.
*   **Fix:**
    ```python
    # Antes: Solo buscaba usando lo que redactó el cliente
    # rag_context = rag_instance.search_playbook(ticket_desc, n_results=1)

    # Después: Busca usando el ticket + contexto BD + trazas de error
    search_query = f"{ticket_desc} {db_str} {trace_str}"
    rag_context = rag_instance.search_playbook(search_query, n_results=2)
    ```

### D. Actualización de Base de Conocimiento
Se documentó explícitamente el "Failure Mode" en el archivo markdown indexado por ChromaDB (`playbooks/playbook_infra.md`), añadiendo la regla `INSUFFICIENT_FUNDS` y la acción recomendada `REJECT_INSUFFICIENT_FUNDS` (Sin necesidad de escalamiento humano).

---

## 3. Directrices para Futuros Desarrollos (Prompt Ancestry)

Al desarrollar nuevos features, integraciones o flujos de IA en el proyecto **SARIP**, utiliza este caso como antecedente o contexto (Prompting Context) para asegurar un diseño robusto:

1. **Diseño de Microservicios:** Nunca confíes solo en excepciones arrojadas al aire. Siempre envuelve la entrada de controladores REST o Listeners asíncronos con bloqueos `MDC.put` y `try-finally { MDC.remove() }`.
2. **Prompts e IA Agéntica:** Un Agente LLM es tan inteligente como su contexto inyectado. Cuando diseñes nodos de RAG, **concatena toda la evidencia dura (DB, Logs, JSONs)** en tu query de similitud semántica; los reportes de usuario a menudo omiten la terminología técnica necesaria para hacer *match* con un Playbook interno.
3. **Escalamiento de MCP:** Cuando conectes nuevos datalakes (ej. Splunk, Datadog) al MCP Gateway, asume *Structured Logging*. Filtra y busca basándote en tags o metadatos (`trace_id`, `service_id`), evitando depender de Regex sobre cuerpos de texto de logs.
