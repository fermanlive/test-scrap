import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel
import json

class ValidationRecord(BaseModel):
    id: int
    article_id: str
    validation_date: datetime
    status: str  # "Ok", "issues"
    issues: List[str]
    metadata: Dict[str, Any]

class ExecutionRecord(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # "Error", "Done", "Not complete"
    records_status: str  # "Ok", "issues"
    issues_summary: Dict[str, List[str]]  # key: article_id, value: list of issues
    total_records: int
    valid_records: int
    invalid_records: int

class DatabaseConnector:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Asegura que las tablas necesarias existan en la base de datos"""
        # Esta función debería crear las tablas si no existen
        # En Supabase, las tablas se crean manualmente desde el dashboard
        pass
    
    def create_validation_record(self, record: ValidationRecord) -> int:
        """Crea un nuevo registro de validación"""
        data = {
            "article_id": record.article_id,
            "validation_date": record.validation_date.isoformat(),
            "status": record.status,
            "issues": json.dumps(record.issues),
            "metadata": json.dumps(record.metadata)
        }
        
        result = self.client.table("validation_records").insert(data).execute()
        return result.data[0]["id"] if result.data else None
    
    def create_execution_record(self, record: ExecutionRecord) -> int:
        """Crea un nuevo registro de ejecución"""
        data = {
            "start_time": record.start_time.isoformat(),
            "end_time": record.end_time.isoformat() if record.end_time else None,
            "status": record.status,
            "records_status": record.records_status,
            "issues_summary": json.dumps(record.issues_summary),
            "total_records": record.total_records,
            "valid_records": record.valid_records,
            "invalid_records": record.invalid_records
        }
        
        result = self.client.table("executions").insert(data).execute()
        return result.data[0]["id"] if result.data else None
    
    def update_execution_record(self, execution_id: int, updates: Dict[str, Any]):
        """Actualiza un registro de ejecución existente"""
        self.client.table("executions").update(updates).eq("id", execution_id).execute()
    
    def get_validation_records_by_article(self, article_id: str) -> List[ValidationRecord]:
        """Obtiene todos los registros de validación para un artículo específico"""
        result = self.client.table("validation_records").select("*").eq("article_id", article_id).execute()
        
        records = []
        for row in result.data:
            record = ValidationRecord(
                id=row["id"],
                article_id=row["article_id"],
                validation_date=datetime.fromisoformat(row["validation_date"]),
                status=row["status"],
                issues=json.loads(row["issues"]),
                metadata=json.loads(row["metadata"])
            )
            records.append(record)
        
        return records
    
    def get_execution_by_id(self, execution_id: int) -> Optional[ExecutionRecord]:
        """Obtiene un registro de ejecución por ID"""
        result = self.client.table("executions").select("*").eq("id", execution_id).execute()
        
        if not result.data:
            return None
        
        row = result.data[0]
        return ExecutionRecord(
            id=row["id"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            status=row["status"],
            records_status=row["records_status"],
            issues_summary=json.loads(row["issues_summary"]),
            total_records=row["total_records"],
            valid_records=row["valid_records"],
            invalid_records=row["invalid_records"]
        )