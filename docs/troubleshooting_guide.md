# Guia de Troubleshooting

## 1. Problemas Comuns

### 1.1 Conexão com Banco de Dados

#### Sintomas
- Erro 500 ao acessar endpoints
- Logs mostrando "Connection refused" ou "Connection timeout"
- Aplicação não inicia

#### Solução
```bash
# Verificar status do PostgreSQL
kubectl exec -it postgres-0 -n shipay-backend -- pg_isready

# Verificar logs do PostgreSQL
kubectl logs -f postgres-0 -n shipay-backend

# Verificar conexão
kubectl exec -it postgres-0 -n shipay-backend -- \
    psql -U postgres -c "SELECT 1;"

# Verificar configurações
kubectl get configmap app-config -n shipay-backend -o yaml
```

### 1.2 Problemas com Redis

#### Sintomas
- Erros de cache
- Lentidão nas respostas
- Timeouts em operações

#### Solução
```bash
# Verificar status do Redis
kubectl exec -it redis-0 -n shipay-backend -- redis-cli ping

# Verificar memória
kubectl exec -it redis-0 -n shipay-backend -- redis-cli info memory

# Verificar conexões
kubectl exec -it redis-0 -n shipay-backend -- redis-cli info clients

# Limpar cache
kubectl exec -it redis-0 -n shipay-backend -- redis-cli FLUSHALL
```

### 1.3 Problemas com Kafka

#### Sintomas
- Eventos não processados
- Consumidores parados
- Erros de conexão

#### Solução
```bash
# Verificar status do Kafka
kubectl exec -it kafka-0 -n shipay-backend -- \
    kafka-topics --list --bootstrap-server localhost:9092

# Verificar consumidores
kubectl exec -it kafka-0 -n shipay-backend -- \
    kafka-consumer-groups --list --bootstrap-server localhost:9092

# Verificar lag
kubectl exec -it kafka-0 -n shipay-backend -- \
    kafka-consumer-groups --describe --group shipay-backend --bootstrap-server localhost:9092
```

## 2. Problemas de Performance

### 2.1 Alta Latência

#### Sintomas
- Respostas lentas
- Timeouts frequentes
- CPU alta

#### Solução
```bash
# Verificar métricas
kubectl exec -it shipay-backend-0 -n shipay-backend -- \
    curl localhost:8000/metrics

# Verificar recursos
kubectl top pods -n shipay-backend

# Verificar logs
kubectl logs -f deployment/shipay-backend -n shipay-backend

# Aumentar recursos
kubectl patch deployment shipay-backend -n shipay-backend \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"shipay-backend","resources":{"limits":{"cpu":"2000m","memory":"4Gi"}}}]}}}}'
```

### 2.2 Alto Uso de Memória

#### Sintomas
- OOM (Out of Memory) kills
- Pods reiniciando
- Performance degradada

#### Solução
```bash
# Verificar uso de memória
kubectl top pods -n shipay-backend

# Verificar limites
kubectl describe pod shipay-backend-0 -n shipay-backend

# Ajustar limites
kubectl patch deployment shipay-backend -n shipay-backend \
    -p '{"spec":{"template":{"spec":{"containers":[{"name":"shipay-backend","resources":{"limits":{"memory":"4Gi"},"requests":{"memory":"2Gi"}}}]}}}}'
```

## 3. Problemas de Rede

### 3.1 Conexões Recusadas

#### Sintomas
- Erros de conexão
- Serviços inacessíveis
- Timeouts

#### Solução
```bash
# Verificar serviços
kubectl get svc -n shipay-backend

# Verificar endpoints
kubectl get endpoints -n shipay-backend

# Verificar DNS
kubectl exec -it shipay-backend-0 -n shipay-backend -- nslookup postgres

# Verificar conectividade
kubectl exec -it shipay-backend-0 -n shipay-backend -- \
    curl -v http://postgres:5432
```

### 3.2 Problemas com Ingress

#### Sintomas
- Domínio inacessível
- Erros 502/503
- SSL inválido

#### Solução
```bash
# Verificar ingress
kubectl get ingress -n shipay-backend

# Verificar certificados
kubectl get certificate -n shipay-backend

# Verificar logs do nginx
kubectl logs -f deployment/nginx-ingress-controller -n ingress-nginx
```

## 4. Problemas de Segurança

### 4.1 Problemas com JWT

#### Sintomas
- Erros 401/403
- Tokens inválidos
- Sessões expiradas

#### Solução
```bash
# Verificar secrets
kubectl get secret app-secrets -n shipay-backend -o yaml

# Verificar logs
kubectl logs -f deployment/shipay-backend -n shipay-backend | grep "JWT"

# Rotacionar chave
kubectl create secret generic app-secrets \
    --namespace shipay-backend \
    --from-literal=JWT_SECRET_KEY=new-secret-key \
    --dry-run=client -o yaml | kubectl apply -f -
```

### 4.2 Problemas com Rate Limiting

#### Sintomas
- Erros 429
- Acesso bloqueado
- IPs banidos

#### Solução
```bash
# Verificar configurações
kubectl get configmap app-config -n shipay-backend -o yaml

# Verificar logs
kubectl logs -f deployment/shipay-backend -n shipay-backend | grep "rate limit"

# Ajustar limites
kubectl patch configmap app-config -n shipay-backend \
    -p '{"data":{"RATE_LIMIT_REQUESTS":"200","RATE_LIMIT_PERIOD":"60"}}'
```

## 5. Problemas de Deploy

### 5.1 Rollback Falhou

#### Sintomas
- Deploy com erro
- Aplicação não inicia
- Rollback não funciona

#### Solução
```bash
# Verificar histórico
kubectl rollout history deployment/shipay-backend -n shipay-backend

# Forçar rollback
kubectl rollout undo deployment/shipay-backend -n shipay-backend --to-revision=1

# Verificar status
kubectl rollout status deployment/shipay-backend -n shipay-backend
```

### 5.2 Problemas com Imagens

#### Sintomas
- Erro ao puxar imagem
- Imagem não encontrada
- Versão incorreta

#### Solução
```bash
# Verificar imagens
kubectl describe pod shipay-backend-0 -n shipay-backend | grep Image

# Verificar registry
kubectl get secret docker-registry -n shipay-backend

# Forçar pull
kubectl set image deployment/shipay-backend \
    shipay-backend=shipay/backend:latest \
    -n shipay-backend
```

## 6. Problemas com Logs

### 6.1 Logs Não Aparecem

#### Sintomas
- Logs vazios
- Falta de informações
- Erros não registrados

#### Solução
```bash
# Verificar nível de log
kubectl get configmap app-config -n shipay-backend -o yaml | grep LOG_LEVEL

# Ajustar nível
kubectl patch configmap app-config -n shipay-backend \
    -p '{"data":{"LOG_LEVEL":"DEBUG"}}'

# Verificar elasticsearch
kubectl exec -it elasticsearch-0 -n logging -- \
    curl -X GET "localhost:9200/_cat/indices?v"
```

### 6.2 Logs Muito Verbosos

#### Sintomas
- Muitos logs
- Performance afetada
- Storage cheio

#### Solução
```bash
# Ajustar nível
kubectl patch configmap app-config -n shipay-backend \
    -p '{"data":{"LOG_LEVEL":"INFO"}}'

# Limpar logs antigos
kubectl exec -it elasticsearch-0 -n logging -- \
    curl -X DELETE "localhost:9200/logs-*"
```

## 7. Problemas com Monitoramento

### 7.1 Métricas Não Aparecem

#### Sintomas
- Grafana sem dados
- Alertas não funcionam
- Métricas ausentes

#### Solução
```bash
# Verificar Prometheus
kubectl exec -it prometheus-0 -n monitoring -- \
    curl localhost:9090/-/healthy

# Verificar targets
kubectl exec -it prometheus-0 -n monitoring -- \
    curl localhost:9090/api/v1/targets

# Verificar service monitor
kubectl get servicemonitor -n shipay-backend
```

### 7.2 Alertas Falsos

#### Sintomas
- Muitos alertas
- Alertas incorretos
- Ruído excessivo

#### Solução
```bash
# Verificar regras
kubectl get prometheusrules -n monitoring

# Ajustar thresholds
kubectl patch prometheusrules shipay-backend -n monitoring \
    -p '{"spec":{"groups":[{"name":"shipay-backend","rules":[{"alert":"HighLatency","expr":"histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1","for":"5m"}]}]}}'
```

## 8. Problemas com Backup

### 8.1 Backup Falhou

#### Sintomas
- Erro ao fazer backup
- Arquivo corrompido
- Espaço insuficiente

#### Solução
```bash
# Verificar espaço
kubectl exec -it postgres-0 -n shipay-backend -- df -h

# Tentar backup manual
kubectl exec -it postgres-0 -n shipay-backend -- \
    pg_dump -U postgres shipay_db > backup.sql

# Verificar integridade
kubectl exec -it postgres-0 -n shipay-backend -- \
    pg_restore -l backup.sql
```

### 8.2 Restore Falhou

#### Sintomas
- Erro ao restaurar
- Dados inconsistentes
- Permissões incorretas

#### Solução
```bash
# Verificar backup
kubectl exec -it postgres-0 -n shipay-backend -- \
    pg_restore -l backup.sql

# Tentar restore
kubectl exec -it postgres-0 -n shipay-backend -- \
    pg_restore -U postgres -d shipay_db backup.sql

# Verificar dados
kubectl exec -it postgres-0 -n shipay-backend -- \
    psql -U postgres -d shipay_db -c "SELECT COUNT(*) FROM users;"
```

## 9. Problemas com CI/CD

### 9.1 Pipeline Falhou

#### Sintomas
- Build quebrado
- Testes falhando
- Deploy não inicia

#### Solução
```bash
# Verificar logs do pipeline
kubectl logs -f job/pipeline-$(date +%Y%m%d) -n shipay-backend

# Verificar status
kubectl get pods -n shipay-backend -l job-name=pipeline-$(date +%Y%m%d)

# Rerun pipeline
kubectl create job --from=cronjob/pipeline pipeline-$(date +%Y%m%d)-rerun -n shipay-backend
```

### 9.2 Problemas com Testes

#### Sintomas
- Testes falhando
- Falsos positivos
- Timeouts

#### Solução
```bash
# Verificar logs dos testes
kubectl logs -f job/test-$(date +%Y%m%d) -n shipay-backend

# Executar testes localmente
kubectl exec -it shipay-backend-0 -n shipay-backend -- pytest

# Ajustar timeouts
kubectl patch configmap app-config -n shipay-backend \
    -p '{"data":{"TEST_TIMEOUT":"300"}}'
```

## 10. Suporte

Para suporte técnico ou dúvidas sobre troubleshooting:

- Email: suporte@shipay.com
- Slack: #backend-support
- Documentação: https://docs.shipay.com 