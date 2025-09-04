"""
Tests unitarios para el conector de base de datos
Siguiendo el patrón AAA (Arrange, Act, Assert) orientado a TDD
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from modules.database_connector import DatabaseConnector, ValidationRecord, ExecutionRecord
from models.models import Product


class TestDatabaseConnector:
    """Tests para la clase DatabaseConnector siguiendo TDD"""

    def test_init_with_valid_credentials(self, mock_supabase_client):
        """Test: Inicialización exitosa con credenciales válidas"""
        # Arrange
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                
                # Act
                connector = DatabaseConnector()
                
                # Assert
                assert connector.client is not None

    def test_create_validation_record(self, mock_supabase_client):
        """Test: Creación exitosa de registro de validación"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": 123}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        validation_record = ValidationRecord(
            id=0,
            article_id="test-123",
            validation_date=datetime.now(),
            status="Ok",
            issues=[],
            metadata={"test": True}
        )
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                result_id = connector.create_validation_record(validation_record)
                
                # Assert
                assert result_id == 123
                mock_supabase_client.table.assert_called_with("validation_records")

    def test_create_execution_record(self, mock_supabase_client):
        """Test: Creación exitosa de registro de ejecución"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": 456}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        execution_record = ExecutionRecord(
            id=0,
            start_time=datetime.now(),
            end_time=None,
            status="Not complete",
            records_status="Not started",
            issues_summary={},
            total_records=10,
            valid_records=0,
            invalid_records=0
        )
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                result_id = connector.create_execution_record(execution_record)
                
                # Assert
                assert result_id == 456
                mock_supabase_client.table.assert_called_with("executions")

    def test_update_execution_record(self, mock_supabase_client):
        """Test: Actualización exitosa de registro de ejecución"""
        # Arrange
        updates = {
            "status": "Done",
            "end_time": datetime.now().isoformat()
        }
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                connector.update_execution_record(123, updates)
                
                # Assert
                mock_table = mock_supabase_client.table.return_value
                mock_table.update.assert_called_once()
                mock_table.update.return_value.eq.assert_called_once_with("id", 123)

    def test_get_validation_records_by_article(self, mock_supabase_client):
        """Test: Obtención de registros de validación por artículo"""
        # Arrange
        mock_data = [
            {
                "id": 1,
                "article_id": "test-123",
                "validation_date": datetime.now().isoformat(),
                "status": "Ok",
                "issues": "[]",
                "metadata": '{"test": true}'
            }
        ]
        mock_response = Mock()
        mock_response.data = mock_data
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                records = connector.get_validation_records_by_article("test-123")
                
                # Assert
                assert len(records) == 1
                assert records[0].article_id == "test-123"
                assert records[0].status == "Ok"
                assert records[0].issues == []

    def test_get_execution_by_id(self, mock_supabase_client):
        """Test: Obtención de ejecución por ID"""
        # Arrange
        mock_data = [
            {
                "id": 456,
                "start_time": datetime.now().isoformat(),
                # plus 30 seconds
                "end_time": (datetime.now() + timedelta(seconds=30)).isoformat(),
                "status": "Done",
                "records_status": "Ok",
                "issues_summary": "{}",
                "total_records": 10,
                "valid_records": 8,
                "invalid_records": 2
            }
        ]
        mock_response = Mock()
        mock_response.data = mock_data
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                execution = connector.get_execution_by_id(456)
                
                # Assert
                assert execution is not None
                assert execution.id == 456
                assert execution.status == "Done"
                assert execution.total_records == 10
                assert execution.valid_records == 8
                assert execution.invalid_records == 2

    def test_get_execution_by_id_not_found(self, mock_supabase_client):
        """Test: Obtención de ejecución que no existe"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                execution = connector.get_execution_by_id(999)
                
                # Assert
                assert execution is None

    def test_create_validation_record_with_issues(self, mock_supabase_client):
        """Test: Creación de registro de validación con issues"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": 789}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        validation_record = ValidationRecord(
            id=0,
            article_id="test-456",
            validation_date=datetime.now(),
            status="issues",
            issues=["Nombre vacío", "Precio inválido"],
            metadata={"confidence_score": 0.7}
        )
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                result_id = connector.create_validation_record(validation_record)
                
                # Assert
                assert result_id == 789
                mock_table = mock_supabase_client.table.return_value
                mock_insert = mock_table.insert.return_value
                mock_insert.execute.assert_called_once()

    def test_create_execution_record_with_issues_summary(self, mock_supabase_client):
        """Test: Creación de registro de ejecución con resumen de issues"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": 101}]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
        
        execution_record = ExecutionRecord(
            id=0,
            start_time=datetime.now(),
            end_time=None,
            status="In Progress",
            records_status="issues",
            issues_summary={
                "test-123": ["Issue 1", "Issue 2"],
                "test-456": ["Issue 3"]
            },
            total_records=5,
            valid_records=2,
            invalid_records=3
        )
        
        with patch('modules.database_connector.create_client', return_value=mock_supabase_client):
            with patch.dict('os.environ', {
                'SUPABASE_URL': 'https://test.supabase.co',
                'SUPABASE_KEY': 'test-key'
            }):
                connector = DatabaseConnector()
                
                # Act
                result_id = connector.create_execution_record(execution_record)
                
                # Assert
                assert result_id == 101


class TestValidationRecord:
    """Tests para la clase ValidationRecord siguiendo TDD"""

    def test_validation_record_creation(self):
        """Test: Creación de ValidationRecord"""
        # Arrange
        article_id = "test-123"
        validation_date = datetime.now()
        status = "Ok"
        issues = []
        metadata = {"confidence_score": 0.95}
        
        # Act
        record = ValidationRecord(
            id=1,
            article_id=article_id,
            validation_date=validation_date,
            status=status,
            issues=issues,
            metadata=metadata
        )
        
        # Assert
        assert record.id == 1
        assert record.article_id == "test-123"
        assert record.status == "Ok"
        assert len(record.issues) == 0
        assert record.metadata["confidence_score"] == 0.95

    def test_validation_record_with_issues(self):
        """Test: ValidationRecord con issues"""
        # Arrange
        issues = ["Nombre vacío", "Precio inválido"]
        metadata = {"confidence_score": 0.7, "suggestions": ["Agregar nombre"]}
        
        # Act
        record = ValidationRecord(
            id=2,
            article_id="test-456",
            validation_date=datetime.now(),
            status="issues",
            issues=issues,
            metadata=metadata
        )
        
        # Assert
        assert record.id == 2
        assert record.article_id == "test-456"
        assert record.status == "issues"
        assert len(record.issues) == 2
        assert "Nombre vacío" in record.issues
        assert record.metadata["confidence_score"] == 0.7


class TestExecutionRecord:
    """Tests para la clase ExecutionRecord siguiendo TDD"""

    def test_execution_record_creation(self):
        """Test: Creación de ExecutionRecord"""
        # Arrange
        start_time = datetime.now()
        total_records = 10
        valid_records = 0
        invalid_records = 0
        
        # Act
        record = ExecutionRecord(
            id=1,
            start_time=start_time,
            end_time=None,
            status="Not complete",
            records_status="Not started",
            issues_summary={},
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records
        )
        
        # Assert
        assert record.id == 1
        assert record.start_time == start_time
        assert record.end_time is None
        assert record.status == "Not complete"
        assert record.records_status == "Not started"
        assert record.total_records == 10
        assert record.valid_records == 0
        assert record.invalid_records == 0

    def test_execution_record_completed(self):
        """Test: ExecutionRecord completado"""
        # Arrange
        start_time = datetime.now()
        end_time = datetime.now()
        total_records = 5
        valid_records = 5
        invalid_records = 0
        
        # Act
        record = ExecutionRecord(
            id=2,
            start_time=start_time,
            end_time=end_time,
            status="Done",
            records_status="Ok",
            issues_summary={},
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records
        )
        
        # Assert
        assert record.id == 2
        assert record.start_time == start_time
        assert record.end_time == end_time
        assert record.status == "Done"
        assert record.records_status == "Ok"
        assert record.total_records == 5
        assert record.valid_records == 5
        assert record.invalid_records == 0

    def test_execution_record_with_issues(self):
        """Test: ExecutionRecord con issues"""
        # Arrange
        issues_summary = {
            "test-123": ["Issue 1"],
            "test-456": ["Issue 2", "Issue 3"]
        }
        total_records = 3
        valid_records = 1
        invalid_records = 2
        
        # Act
        record = ExecutionRecord(
            id=3,
            start_time=datetime.now(),
            end_time=None,
            status="In Progress",
            records_status="issues",
            issues_summary=issues_summary,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records
        )
        
        # Assert
        assert record.id == 3
        assert record.status == "In Progress"
        assert record.records_status == "issues"
        assert len(record.issues_summary) == 2
        assert "test-123" in record.issues_summary
        assert "test-456" in record.issues_summary
        assert len(record.issues_summary["test-456"]) == 2
