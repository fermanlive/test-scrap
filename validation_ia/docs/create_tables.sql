-- Script para crear las tablas del sistema de validación con IA Generativa
-- Ejecutar en el SQL Editor de Supabase

-- Tabla 1: Registros de validación (logs)
-- Almacena logs individuales para cada artículo validado, la tabla esta particionada por el campo validation_date y clusterizada por article_id
CREATE TABLE IF NOT EXISTS validation_records (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL,
    validation_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('Ok', 'issues')),
    issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)PARTITION BY DATE(validation_date)
CLUSTER BY article_id;

-- Tabla 2: Ejecuciones del proceso
-- Almacena información de cada ejecución del proceso de validación , la tabla esta particionada por el campo , start_time y clusterizada por status

CREATE TABLE IF NOT EXISTS executions (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL CHECK (status IN ('Error', 'Done', 'Not complete', 'In Progress')),
    records_status TEXT NOT NULL CHECK (records_status IN ('Ok', 'issues', 'Not started', 'Processing')),
    issues_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)PARTITION BY DATE(start_time)
CLUSTER BY status;

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_validation_records_article_id ON validation_records(article_id);
CREATE INDEX IF NOT EXISTS idx_validation_records_date ON validation_records(validation_date);
CREATE INDEX IF NOT EXISTS idx_validation_records_status ON validation_records(status);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_start_time ON executions(start_time);
CREATE INDEX IF NOT EXISTS idx_executions_records_status ON executions(records_status);

-- Crear índices para JSONB (optimización de consultas en campos JSON)
CREATE INDEX IF NOT EXISTS idx_validation_records_issues_gin ON validation_records USING GIN (issues);
CREATE INDEX IF NOT EXISTS idx_validation_records_metadata_gin ON validation_records USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_executions_issues_summary_gin ON executions USING GIN (issues_summary);

-- Comentarios para documentar las tablas
COMMENT ON TABLE validation_records IS 'Logs de validación individual para cada artículo validado';
COMMENT ON TABLE executions IS 'Registro de cada ejecución del proceso de validación';

COMMENT ON COLUMN validation_records.article_id IS 'Identificador único del artículo validado';
COMMENT ON COLUMN validation_records.validation_date IS 'Fecha y hora de la validación';
COMMENT ON COLUMN validation_records.status IS 'Estado de la validación: Ok (sin problemas) o issues (con problemas)';
COMMENT ON COLUMN validation_records.issues IS 'Lista de problemas encontrados en formato JSON';
COMMENT ON COLUMN validation_records.metadata IS 'Información adicional como sugerencias, score de confianza, método de validación';

COMMENT ON COLUMN executions.start_time IS 'Cuándo comenzó el proceso de validación';
COMMENT ON COLUMN executions.end_time IS 'Cuándo finalizó el proceso (NULL si está en progreso)';
COMMENT ON COLUMN executions.status IS 'Estado del proceso: Error, Done, Not complete, In Progress';
COMMENT ON COLUMN executions.records_status IS 'Estado de los registros: Ok (todos válidos) o issues (algunos con problemas)';
COMMENT ON COLUMN executions.issues_summary IS 'Diccionario con ID del producto como clave y lista de issues como valor';
COMMENT ON COLUMN executions.total_records IS 'Total de registros procesados';
COMMENT ON COLUMN executions.valid_records IS 'Cantidad de registros válidos';
COMMENT ON COLUMN executions.invalid_records IS 'Cantidad de registros con issues';

-- Insertar datos de ejemplo para testing (opcional)
-- INSERT INTO validation_records (article_id, status, issues, metadata) VALUES 
-- ('PROD001', 'Ok', '[]', '{"confidence_score": 0.95, "validation_method": "AI_Generative"}'),
-- ('PROD002', 'issues', '["Nombre vacío", "Precio inválido"]', '{"confidence_score": 0.85, "validation_method": "AI_Generative"}');

-- INSERT INTO executions (status, records_status, total_records, valid_records, invalid_records) VALUES 
-- ('Done', 'issues', 2, 1, 1);

-- Verificar que las tablas se crearon correctamente
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name IN ('validation_records', 'executions')
ORDER BY table_name, ordinal_position;
