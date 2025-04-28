-- Criação da tabela de lançamentos de foguetes
CREATE TABLE IF NOT EXISTS rocket_launches (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    launch_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    pre_flight_status VARCHAR(50) NOT NULL,
    countdown_status VARCHAR(50) NOT NULL,
    trace_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance nas consultas
CREATE INDEX IF NOT EXISTS idx_rocket_launches_customer_id ON rocket_launches(customer_id);
CREATE INDEX IF NOT EXISTS idx_rocket_launches_launch_date ON rocket_launches(launch_date);
CREATE INDEX IF NOT EXISTS idx_rocket_launches_trace_id ON rocket_launches(trace_id);

-- Trigger para atualizar o updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_rocket_launches_updated_at
    BEFORE UPDATE ON rocket_launches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 