# Guia de Deploy

## 1. Pré-requisitos

### 1.1 Infraestrutura
- Kubernetes cluster (versão 1.20 ou superior)
- Helm (versão 3.0 ou superior)
- Docker Registry
- Certificado SSL válido
- Domínio configurado

### 1.2 Recursos
- 4 vCPUs
- 8GB RAM
- 50GB SSD
- Rede com acesso à internet

## 2. Configuração do Ambiente

### 2.1 Namespace
```bash
kubectl create namespace shipay-backend
```

### 2.2 Secrets
```bash
# Criar secrets do Kubernetes
kubectl create secret generic app-secrets \
    --namespace shipay-backend \
    --from-literal=DATABASE_URL=postgresql://user:password@postgres:5432/shipay_db \
    --from-literal=JWT_SECRET_KEY=your-secret-key \
    --from-literal=REDIS_URL=redis://redis:6379/0
```

### 2.3 ConfigMaps
```bash
# Criar ConfigMaps do Kubernetes
kubectl create configmap app-config \
    --namespace shipay-backend \
    --from-file=config.yaml=./k8s/config.yaml
```

## 3. Deploy dos Serviços

### 3.1 Banco de Dados
```yaml
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: shipay-backend
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: shipay_db
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### 3.2 Redis
```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: shipay-backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
```

### 3.3 MongoDB
```yaml
# k8s/mongodb.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: shipay-backend
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:4.4
        ports:
        - containerPort: 27017
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
      volumes:
      - name: mongodb-data
        persistentVolumeClaim:
          claimName: mongodb-pvc
```

### 3.4 Kafka
```yaml
# k8s/kafka.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  namespace: shipay-backend
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:6.2.0
        ports:
        - containerPort: 9092
        env:
        - name: KAFKA_BROKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: KAFKA_ZOOKEEPER_CONNECT
          value: zookeeper:2181
        - name: KAFKA_ADVERTISED_LISTENERS
          value: PLAINTEXT://kafka:9092
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
      volumes:
      - name: kafka-data
        persistentVolumeClaim:
          claimName: kafka-pvc
```

### 3.5 Aplicação
```yaml
# k8s/app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shipay-backend
  namespace: shipay-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shipay-backend
  template:
    metadata:
      labels:
        app: shipay-backend
    spec:
      containers:
      - name: shipay-backend
        image: shipay/backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 4. Configuração de Ingress

### 4.1 Ingress Controller
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shipay-backend
  namespace: shipay-backend
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.shipay.com
    secretName: shipay-backend-tls
  rules:
  - host: api.shipay.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: shipay-backend
            port:
              number: 8000
```

## 5. Configuração de Monitoramento

### 5.1 Prometheus
```yaml
# k8s/monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: shipay-backend
  namespace: shipay-backend
spec:
  selector:
    matchLabels:
      app: shipay-backend
  endpoints:
  - port: metrics
    interval: 15s
```

### 5.2 Grafana
```yaml
# k8s/grafana.yaml
apiVersion: integreatly.org/v1alpha1
kind: GrafanaDashboard
metadata:
  name: shipay-backend
  namespace: shipay-backend
spec:
  json: |
    {
      "dashboard": {
        "title": "Shipay Backend",
        "panels": [...]
      }
    }
```

## 6. Script de Deploy

### 6.1 deploy.sh
```bash
#!/bin/bash

# Verificar pré-requisitos
kubectl version
helm version

# Criar namespace
kubectl create namespace shipay-backend

# Aplicar configurações
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml

# Deploy dos serviços
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/app.yaml

# Configurar ingress
kubectl apply -f k8s/ingress.yaml

# Configurar monitoramento
kubectl apply -f k8s/monitoring.yaml
kubectl apply -f k8s/grafana.yaml

# Verificar status
kubectl get all -n shipay-backend
```

### 6.2 Executar Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

## 7. Verificação do Deploy

### 7.1 Verificar Status
```bash
# Verificar pods
kubectl get pods -n shipay-backend

# Verificar serviços
kubectl get svc -n shipay-backend

# Verificar ingress
kubectl get ingress -n shipay-backend

# Verificar logs
kubectl logs -f deployment/shipay-backend -n shipay-backend
```

### 7.2 Testar Aplicação
```bash
# Testar health check
curl https://api.shipay.com/health

# Testar documentação
curl https://api.shipay.com/docs
```

## 8. Rollback

### 8.1 Script de Rollback
```bash
#!/bin/bash

# Reverter para versão anterior
kubectl rollout undo deployment/shipay-backend -n shipay-backend

# Verificar status
kubectl rollout status deployment/shipay-backend -n shipay-backend
```

### 8.2 Executar Rollback
```bash
chmod +x rollback.sh
./rollback.sh
```

## 9. Manutenção

### 9.1 Atualização
```bash
# Atualizar imagem
kubectl set image deployment/shipay-backend \
    shipay-backend=shipay/backend:new-version \
    -n shipay-backend

# Verificar atualização
kubectl rollout status deployment/shipay-backend -n shipay-backend
```

### 9.2 Backup
```bash
# Backup do PostgreSQL
kubectl exec -it postgres-0 -n shipay-backend -- \
    pg_dump -U postgres shipay_db > backup.sql

# Backup do MongoDB
kubectl exec -it mongodb-0 -n shipay-backend -- \
    mongodump --out=/backup
```

## 10. Suporte

Para suporte técnico ou dúvidas sobre deploy:

- Email: suporte@shipay.com
- Slack: #backend-deploy
- Documentação: https://docs.shipay.com 