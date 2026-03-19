from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AuditLog(BaseModel):
    agent: str = Field(description="Nombre del agente que ejecutó la acción")
    action: str = Field(description="Acción realizada")
    timestamp: Optional[str] = Field(default=None, description="Fecha y hora de la acción")

class TicketState(BaseModel):
    """
    Representa el estado global (Case File) que viaja a través del LangGraph.
    Utilizando Pydantic garantizamos tipado estricto y validación automática.
    """
    # Contexto Inicial
    ticket_id: str = Field(default="", description="ID del caso/ticket")
    description: str = Field(default="", description="Descripción del reporte generado por el usuario")
    operations: List[str] = Field(default_factory=list, description="IDs financieros a investigar extraídos")
    
    # Datos enriquecidos por el Evidence Collector
    db_context: Dict[str, Any] = Field(default_factory=dict, description="Estados finales extraídos de la BD Core")
    trace_context: List[Dict[str, Any]] = Field(default_factory=list, description="Logs consolidados útiles")
    reconciliation_context: Dict[str, Any] = Field(default_factory=dict, description="Diferencias SFTP / Batch")
    
    # Síntesis Cognitiva (Clasificador y RCA Reporter)
    failure_mode: str = Field(default="", description="Patrón de falla estandarizado (ej: TIMEOUT_BUSINESS)")
    recommended_action: str = Field(default="", description="Acción sugerida por el Playbook")
    timeline: List[str] = Field(default_factory=list, description="Historia cronológica de los eventos")
    confidence_score: float = Field(default=0.0, description="Puntuación de 0.0 a 1.0 de confianza de la IA")
    requires_human_approval: bool = Field(default=False, description="Flag de seguridad para escalar a humanos")
    reviewer_feedback: Optional[str] = Field(default=None, description="Retroalimentación del Agente Evaluador tras un rechazo")
    revision_count: int = Field(default=0, description="Contador de veces que el dictamen ha sido reevaluado")
    is_valid: bool = Field(default=False, description="Bandera booleana de aprobación de la IA Supervisora")
    
    # Orquestación y Trazabilidad LangGraph
    next_agent: str = Field(default="", description="Anotación interna para enrutamiento (Edges)")
    investigation_complete: bool = Field(default=False, description="Flag de sistema resuelto")
    audit_trail: List[AuditLog] = Field(default_factory=list, description="Huella de pasos para auditoría")
