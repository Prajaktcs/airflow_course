## Installation instructions

## Airflow

### Statsd exporter

- Already installed with airflow helm
- Command to port forward
  `kubectl port-forward airflow-statsd-769b757665-hsns2 9102:9102 -n airflow`

### 1 node Elasticsearch with Kibana (If you want)

- `kubectl create -f https://download.elastic.co/downloads/eck/2.16.0/crds.yaml`
- `kubectl apply -f https://download.elastic.co/downloads/eck/2.16.0/operator.yaml`
- `kubectl apply -f kubernetes/elastic-stack.yaml`

### Prometheus and Graphana

- `helm repo add prometheus-community https://prometheus-community.github.io/helm-charts`
- `helm repo add grafana https://grafana.github.io/helm-charts`
- `helm repo update`

- `helm upgrade --install prometheus prometheus-community/prometheus -f prometheus.yaml --namespace monitoring`
- `helm upgrade --install grafana grafana/grafana -f grafana.yaml --namespace monitoring`
- `kubectl expose service grafana --type=NodePort --target-port=3000 --name=grafana-ext`
- `kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" | base64 -D | pbcopy`

Prometheus url

- http://prometheus-server.monitoring.svc.cluster.local

### kube-state-metrics

- `helm repo add bitnami https://charts.bitnami.com/bitnami`
- `helm repo update`
- `helm install my-kube-state-metrics bitnami/kube-state-metrics --namespace kube-system --create-namespace`
