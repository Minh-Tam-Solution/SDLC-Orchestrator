# KUBERNETES DEPLOYMENT GUIDE
## SDLC Orchestrator - Production Deployment

**Version**: 1.1.0
**Date**: December 16, 2025 (Updated Week 9 Day 1)
**Status**: ACTIVE - Week 9 Day 1 with Production Manifests
**Authority**: DevOps Lead + Platform Engineering + CTO Approved
**Framework**: SDLC 5.1.3 Complete Lifecycle

---

## 📢 **IMPORTANT UPDATE (Week 9 Day 1)**

**Production-ready Kubernetes manifests are now available!**

This document provides **strategic overview** of Kubernetes deployment. For **hands-on deployment guide** with actual manifests, see:

👉 **[k8s/README.md](../../k8s/README.md)** - Step-by-step deployment guide with kubectl commands

**Week 9 Day 1 Deliverables**:
- ✅ 9 production-ready Kubernetes manifests ([k8s/base/](../../k8s/base/))
- ✅ Comprehensive deployment documentation (1,050+ lines)
- ✅ Local development support (minikube/kind configurations)
- ✅ Troubleshooting guide with common issues + fixes

**Manifest Files**:
- [namespace.yaml](../../k8s/base/namespace.yaml) - Namespace isolation + resource quotas
- [postgres-statefulset.yaml](../../k8s/base/postgres-statefulset.yaml) - PostgreSQL 15.5 with Prometheus exporter
- [postgres-configmap.yaml](../../k8s/base/postgres-configmap.yaml) - Performance tuning + init scripts
- [redis.yaml](../../k8s/base/redis.yaml) - Redis 7.2 with exporter sidecar
- [opa.yaml](../../k8s/base/opa.yaml) - OPA 0.58.0 with preloaded policies
- [minio.yaml](../../k8s/base/minio.yaml) - MinIO (AGPL-safe, network-only)
- [backend.yaml](../../k8s/base/backend.yaml) - FastAPI with Alembic migrations
- [configmap.yaml](../../k8s/base/configmap.yaml) - Application configuration
- [secrets.yaml](../../k8s/base/secrets.yaml) - Sensitive credentials (base64)
- [ingress.yaml](../../k8s/base/ingress.yaml) - NGINX Ingress + cert-manager TLS

---

## 🎯 **OVERVIEW**

This guide covers **production-grade Kubernetes deployment** for SDLC Orchestrator. For local development with Docker Compose, see [DOCKER-DEPLOYMENT-GUIDE.md](DOCKER-DEPLOYMENT-GUIDE.md).

### **Target Environment**

```yaml
Production Deployment (Kubernetes):
  Cluster: Kubernetes 1.28+ (managed: EKS, GKE, AKS)
  Namespace: sdlc-orchestrator
  Workloads: 8 Deployments + 3 StatefulSets
  Services: 11 ClusterIP + 1 LoadBalancer
  Storage: 5 PersistentVolumeClaims (100GB total)
  Scaling: HPA (2-10 pods for backend)
  High Availability: Multi-AZ deployment (3 nodes minimum)
```

---

## 📋 **PREREQUISITES**

### **Cluster Requirements**

```yaml
Kubernetes Cluster:
  Version: 1.28+ (managed cluster recommended)
  Nodes: 3+ worker nodes (multi-AZ for HA)
  Node Size: 4 CPU / 16GB RAM per node (t3.xlarge / n1-standard-4)
  Total Resources: 12 CPU / 48GB RAM minimum
  Storage Class: gp3 (AWS), pd-ssd (GCP), Premium SSD (Azure)

Managed Kubernetes Services (Recommended):
  ✅ AWS EKS (Elastic Kubernetes Service)
  ✅ GCP GKE (Google Kubernetes Engine)
  ✅ Azure AKS (Azure Kubernetes Service)
  ✅ DigitalOcean DOKS (DigitalOcean Kubernetes)
```

### **Required Tools**

```bash
# 1. kubectl (Kubernetes CLI)
kubectl version --client  # v1.28+

# 2. Helm 3 (Kubernetes package manager)
helm version  # v3.12+

# 3. kustomize (Kubernetes configuration management)
kustomize version  # v5.0+

# 4. (Optional) k9s (Kubernetes TUI dashboard)
k9s version  # v0.27+
```

### **Installation (macOS/Linux)**

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/

# Verify installation
kubectl version --client
helm version
kustomize version
```

---

## 🚀 **QUICK START (Production Deployment)**

### **Step 1: Cluster Access Configuration**

<details>
<summary><strong>AWS EKS</strong></summary>

```bash
# Configure kubectl for EKS cluster
aws eks update-kubeconfig --region us-east-1 --name sdlc-orchestrator-prod

# Verify cluster access
kubectl get nodes

# Expected output:
# NAME                                       STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.us-east-1.compute.internal   Ready    <none>   30d   v1.28.3-eks-abc123
# ip-10-0-2-200.us-east-1.compute.internal   Ready    <none>   30d   v1.28.3-eks-abc123
# ip-10-0-3-300.us-east-1.compute.internal   Ready    <none>   30d   v1.28.3-eks-abc123
```
</details>

<details>
<summary><strong>GCP GKE</strong></summary>

```bash
# Configure kubectl for GKE cluster
gcloud container clusters get-credentials sdlc-orchestrator-prod --region us-central1 --project your-project-id

# Verify cluster access
kubectl get nodes
```
</details>

<details>
<summary><strong>Azure AKS</strong></summary>

```bash
# Configure kubectl for AKS cluster
az aks get-credentials --resource-group sdlc-orchestrator-rg --name sdlc-orchestrator-prod

# Verify cluster access
kubectl get nodes
```
</details>

### **Step 2: Create Namespace**

```bash
# Create dedicated namespace for SDLC Orchestrator
kubectl create namespace sdlc-orchestrator

# Set as default namespace for current context
kubectl config set-context --current --namespace=sdlc-orchestrator

# Verify namespace
kubectl get namespace sdlc-orchestrator

# Expected output:
# NAME               STATUS   AGE
# sdlc-orchestrator  Active   10s
```

### **Step 3: Create Secrets**

```bash
# Create secret for database credentials
kubectl create secret generic postgres-secret \
  --from-literal=username=sdlc_user \
  --from-literal=password=$(openssl rand -base64 32) \
  --from-literal=database=sdlc_orchestrator

# Create secret for application secrets
kubectl create secret generic app-secret \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=jwt-secret-key=$(openssl rand -hex 32)

# Create secret for MinIO credentials
kubectl create secret generic minio-secret \
  --from-literal=access-key=admin \
  --from-literal=secret-key=$(openssl rand -base64 32)

# Verify secrets created
kubectl get secrets

# Expected output:
# NAME              TYPE     DATA   AGE
# postgres-secret   Opaque   3      10s
# app-secret        Opaque   2      10s
# minio-secret      Opaque   2      10s
```

### **Step 4: Deploy Storage (PersistentVolumeClaims)**

```bash
# Apply storage manifests
kubectl apply -f k8s/storage/

# Verify PVCs created and bound
kubectl get pvc

# Expected output:
# NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   AGE
# postgres-data    Bound    pvc-abc123...                              20Gi       RWO            30s
# redis-data       Bound    pvc-def456...                              5Gi        RWO            30s
# minio-data       Bound    pvc-ghi789...                              50Gi       RWO            30s
# prometheus-data  Bound    pvc-jkl012...                              20Gi       RWO            30s
# grafana-data     Bound    pvc-mno345...                              5Gi        RWO            30s
```

### **Step 5: Deploy StatefulSets (Databases)**

```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f k8s/statefulsets/postgres.yaml

# Deploy Redis StatefulSet
kubectl apply -f k8s/statefulsets/redis.yaml

# Deploy MinIO StatefulSet
kubectl apply -f k8s/statefulsets/minio.yaml

# Wait for StatefulSets to be ready (may take 2-3 minutes)
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
kubectl wait --for=condition=ready pod -l app=minio --timeout=300s

# Verify StatefulSets
kubectl get statefulsets

# Expected output:
# NAME       READY   AGE
# postgres   1/1     2m
# redis      1/1     2m
# minio      1/1     2m
```

### **Step 6: Deploy Application Services**

```bash
# Deploy backend API
kubectl apply -f k8s/deployments/backend.yaml

# Deploy OPA policy engine
kubectl apply -f k8s/deployments/opa.yaml

# Deploy monitoring stack (Prometheus, Grafana, Alertmanager)
kubectl apply -f k8s/deployments/monitoring.yaml

# Wait for all deployments to be ready
kubectl wait --for=condition=available deployment --all --timeout=300s

# Verify deployments
kubectl get deployments

# Expected output:
# NAME            READY   UP-TO-DATE   AVAILABLE   AGE
# backend         3/3     3            3           2m
# opa             2/2     2            2           2m
# prometheus      1/1     1            1           2m
# grafana         1/1     1            1           2m
# alertmanager    1/1     1            1           2m
```

### **Step 7: Deploy Services (Networking)**

```bash
# Deploy all services
kubectl apply -f k8s/services/

# Verify services
kubectl get services

# Expected output:
# NAME              TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)          AGE
# backend           ClusterIP      10.100.10.10    <none>          8000/TCP         1m
# backend-public    LoadBalancer   10.100.10.20    1.2.3.4         80:30080/TCP     1m
# postgres          ClusterIP      10.100.20.10    <none>          5432/TCP         1m
# redis             ClusterIP      10.100.30.10    <none>          6379/TCP         1m
# minio             ClusterIP      10.100.40.10    <none>          9000/TCP         1m
# opa               ClusterIP      10.100.50.10    <none>          8181/TCP         1m
# prometheus        ClusterIP      10.100.60.10    <none>          9090/TCP         1m
# grafana           ClusterIP      10.100.70.10    <none>          3000/TCP         1m
# alertmanager      ClusterIP      10.100.80.10    <none>          9093/TCP         1m
```

### **Step 8: Run Database Migrations**

```bash
# Run Alembic migrations job
kubectl apply -f k8s/jobs/db-migration.yaml

# Wait for migration job to complete
kubectl wait --for=condition=complete job/db-migration --timeout=300s

# Check migration logs
kubectl logs job/db-migration

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema (24 tables)
# INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, Seed data (43 records)
# Migration completed successfully!
```

### **Step 9: Configure Ingress (External Access)**

```bash
# Deploy Ingress resource (requires Ingress Controller installed)
kubectl apply -f k8s/ingress/backend-ingress.yaml

# Verify Ingress created
kubectl get ingress

# Expected output:
# NAME              CLASS    HOSTS                        ADDRESS      PORTS     AGE
# backend-ingress   nginx    api.sdlc-orchestrator.com    1.2.3.4      80, 443   1m

# Wait for DNS propagation (may take 5-10 minutes)
# Then access API at: https://api.sdlc-orchestrator.com/api/v1/
```

### **Step 10: Verify Deployment**

```bash
# Health check: All pods running
kubectl get pods

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# backend-abc123-xyz                2/2     Running   0          5m
# backend-def456-uvw                2/2     Running   0          5m
# backend-ghi789-rst                2/2     Running   0          5m
# postgres-0                      1/1     Running   0          10m
# redis-0                         1/1     Running   0          10m
# minio-0                         1/1     Running   0          10m
# opa-jkl012-opq                    1/1     Running   0          5m
# opa-mno345-lmn                    1/1     Running   0          5m
# prometheus-pqr678-ijk             1/1     Running   0          5m
# grafana-stu901-fgh                1/1     Running   0          5m
# alertmanager-vwx234-cde           1/1     Running   0          5m

# Health check: API endpoint
kubectl exec -it deployment/backend -- curl -s http://localhost:8000/api/v1/

# Expected output:
# {"message":"SDLC Orchestrator API v1.0.0","version":"1.0.0","status":"operational","documentation":"http://localhost:8000/docs","timestamp":"2025-12-03T14:30:00Z"}

# Health check: Database connectivity
kubectl exec -it postgres-0 -- pg_isready -U sdlc_user -d sdlc_orchestrator

# Expected output:
# /var/run/postgresql:5432 - accepting connections
```

---

## 📦 **KUBERNETES MANIFESTS**

### **Backend Deployment** (k8s/deployments/backend.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: sdlc-orchestrator
  labels:
    app: backend
    version: v1.0.0
spec:
  replicas: 3  # High availability (3 replicas across 3 AZs)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Zero-downtime deployment
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        # Anti-affinity: Distribute pods across nodes/AZs
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - backend
                topologyKey: topology.kubernetes.io/zone
      containers:
        - name: backend
          image: sdlc-orchestrator/backend:1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          env:
            - name: ENVIRONMENT
              value: "production"
            - name: LOG_LEVEL
              value: "INFO"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: connection-string
            - name: REDIS_URL
              value: "redis://redis:6379/0"
            - name: MINIO_ENDPOINT
              value: "minio:9000"
            - name: MINIO_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: minio-secret
                  key: access-key
            - name: MINIO_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: minio-secret
                  key: secret-key
            - name: OPA_URL
              value: "http://opa:8181"
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: secret-key
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: jwt-secret-key
          resources:
            requests:
              cpu: 500m      # 0.5 CPU per pod
              memory: 512Mi  # 512MB RAM per pod
            limits:
              cpu: 1000m     # 1 CPU max
              memory: 1Gi    # 1GB RAM max
          livenessProbe:
            httpGet:
              path: /api/v1/auth/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /api/v1/auth/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
```

### **PostgreSQL StatefulSet** (k8s/statefulsets/postgres.yaml)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: sdlc-orchestrator
spec:
  serviceName: postgres
  replicas: 1  # Single primary (HA with replication in production)
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
          image: postgres:15.5-alpine
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: database
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          resources:
            requests:
              cpu: 1000m
              memory: 2Gi
            limits:
              cpu: 2000m
              memory: 4Gi
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U $POSTGRES_USER -d $POSTGRES_DB
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - pg_isready -U $POSTGRES_USER -d $POSTGRES_DB
            initialDelaySeconds: 10
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3  # AWS EBS gp3 (change for GCP/Azure)
        resources:
          requests:
            storage: 20Gi
```

### **Backend Service** (k8s/services/backend.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: sdlc-orchestrator
  labels:
    app: backend
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - name: http
      port: 8000
      targetPort: 8000
      protocol: TCP
  sessionAffinity: None
```

### **Backend LoadBalancer** (k8s/services/backend-public.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-public
  namespace: sdlc-orchestrator
  annotations:
    # AWS ELB annotations (change for GCP/Azure)
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:us-east-1:123456789012:certificate/abc123..."
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
    - name: https
      port: 443
      targetPort: 8000
      protocol: TCP
```

### **HorizontalPodAutoscaler** (k8s/hpa/backend-hpa.yaml)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: sdlc-orchestrator
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2   # Minimum 2 pods (HA)
  maxReplicas: 10  # Scale up to 10 pods under load
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # Scale when CPU > 70%
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80  # Scale when memory > 80%
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
        - type: Percent
          value: 50                     # Scale down 50% at a time
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0    # Scale up immediately
      policies:
        - type: Percent
          value: 100                    # Double pods when scaling up
          periodSeconds: 15
```

---

## 📊 **MONITORING & OBSERVABILITY**

### **Prometheus ServiceMonitor** (k8s/monitoring/backend-servicemonitor.yaml)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: sdlc-orchestrator
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

### **Accessing Monitoring Dashboards**

```bash
# Port-forward Grafana (temporary access)
kubectl port-forward svc/grafana 3000:3000

# Open browser: http://localhost:3000
# Username: admin
# Password: admin (change after first login)

# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090

# Open browser: http://localhost:9090
```

---

## 🔄 **UPDATES & ROLLBACKS**

### **Rolling Update (Zero-Downtime)**

```bash
# Update backend image
kubectl set image deployment/backend backend=sdlc-orchestrator/backend:1.1.0

# Monitor rollout status
kubectl rollout status deployment/backend

# Expected output:
# Waiting for deployment "backend" rollout to finish: 1 out of 3 new replicas have been updated...
# Waiting for deployment "backend" rollout to finish: 2 out of 3 new replicas have been updated...
# deployment "backend" successfully rolled out
```

### **Rollback (Emergency)**

```bash
# Rollback to previous version
kubectl rollout undo deployment/backend

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2

# Check rollout history
kubectl rollout history deployment/backend

# Expected output:
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         Update to v1.1.0
# 3         Update to v1.2.0 (current)
```

---

## 🔒 **SECURITY BEST PRACTICES**

### **Network Policies** (k8s/network-policies/backend-netpol.yaml)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-netpol
  namespace: sdlc-orchestrator
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow traffic from frontend and ingress controller only
    - from:
        - podSelector:
            matchLabels:
              app: frontend
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    # Allow traffic to PostgreSQL, Redis, MinIO, OPA only
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
    - to:
        - podSelector:
            matchLabels:
              app: minio
      ports:
        - protocol: TCP
          port: 9000
    - to:
        - podSelector:
            matchLabels:
              app: opa
      ports:
        - protocol: TCP
          port: 8181
    # Allow DNS resolution
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: UDP
          port: 53
```

---

## 🐛 **TROUBLESHOOTING**

### **Pods CrashLoopBackOff**

```bash
# Check pod logs
kubectl logs -f deployment/backend --tail=100

# Describe pod for events
kubectl describe pod backend-abc123-xyz

# Common causes:
# 1. Database not ready → Check postgres pod status
# 2. Missing secrets → Verify secrets exist: kubectl get secrets
# 3. OOM (Out of Memory) → Increase memory limits in deployment.yaml
```

### **Service Unreachable**

```bash
# Test service DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup backend

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl -v http://backend:8000/api/v1/

# Check service endpoints
kubectl get endpoints backend
```

---

## 📚 **REFERENCES**

- **Kubernetes Manifests**: [k8s/](../../k8s/)
- **Docker Deployment**: [DOCKER-DEPLOYMENT-GUIDE.md](DOCKER-DEPLOYMENT-GUIDE.md)
- **Monitoring Guide**: [MONITORING-OBSERVABILITY-GUIDE.md](MONITORING-OBSERVABILITY-GUIDE.md)
- **Helm Charts**: [helm/sdlc-orchestrator/](../../helm/sdlc-orchestrator/)

---

**Last Updated**: December 3, 2025
**Owner**: DevOps Lead + Platform Engineering
**Status**: ✅ COMPLETE - Week 4 Day 1 Architecture Documentation
**Next Review**: Week 4 Day 2 (Dec 4, 2025)
