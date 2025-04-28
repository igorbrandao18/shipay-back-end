import pytest
import asyncio
import time
from datetime import datetime, timedelta
from app.services.scheduler import SchedulerService
from app.models.schemas import ScheduleEventRequest
import statistics

@pytest.mark.asyncio
async def test_scheduler_performance():
    service = SchedulerService()
    latencies = []
    requests_per_second = 1000
    duration_seconds = 10
    total_requests = requests_per_second * duration_seconds
    
    async def make_request():
        start_time = time.time()
        await service.schedule_event(
            ScheduleEventRequest(
                content={"video_id": "test", "format": "mp4"},
                scheduled_time=datetime.now() + timedelta(hours=1)
            )
        )
        latency = time.time() - start_time
        return latency
    
    # Executa os testes
    start_time = time.time()
    tasks = []
    for _ in range(total_requests):
        task = asyncio.create_task(make_request())
        tasks.append(task)
        await asyncio.sleep(1/requests_per_second)  # Controla a taxa de requisições
    
    # Coleta os resultados
    results = await asyncio.gather(*tasks)
    latencies.extend(results)
    total_time = time.time() - start_time
    
    # Calcula estatísticas
    p99_latency = statistics.quantiles(latencies, n=100)[98]
    actual_rps = total_requests / total_time
    
    # Imprime resultados
    print(f"\nResultados do teste de performance:")
    print(f"Total de requisições: {total_requests}")
    print(f"Tempo total: {total_time:.2f} segundos")
    print(f"Requisições por segundo: {actual_rps:.2f}")
    print(f"Latência P99: {p99_latency*1000:.2f} ms")
    
    # Verifica se atende aos requisitos
    assert actual_rps >= 1000, f"Taxa de requisições abaixo do esperado: {actual_rps:.2f} rps"
    assert p99_latency <= 0.03, f"Latência P99 acima do esperado: {p99_latency*1000:.2f} ms"

@pytest.mark.asyncio
async def test_concurrent_processing():
    service = SchedulerService()
    num_events = 1000
    
    # Cria eventos
    events = []
    for i in range(num_events):
        events.append({
            "event_id": f"test_{i}",
            "content": {"video_id": f"video_{i}", "format": "mp4"},
            "scheduled_time": datetime.now().isoformat(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "processed_at": None
        })
    
    # Armazena eventos no Redis
    for event in events:
        await service._store_event(
            event["event_id"],
            event["content"],
            datetime.fromisoformat(event["scheduled_time"])
        )
    
    # Processa eventos concorrentemente
    start_time = time.time()
    await service._process_pending_events()
    processing_time = time.time() - start_time
    
    print(f"\nResultados do teste de processamento concorrente:")
    print(f"Total de eventos: {num_events}")
    print(f"Tempo de processamento: {processing_time:.2f} segundos")
    print(f"Eventos por segundo: {num_events/processing_time:.2f}")
    
    # Verifica se o processamento foi eficiente
    assert processing_time < 1.0, f"Tempo de processamento muito alto: {processing_time:.2f} segundos" 