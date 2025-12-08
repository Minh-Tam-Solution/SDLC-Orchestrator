#!/bin/bash
###############################################################################
# Sprint 33 Day 5 - Monitoring Alert Configuration
# Applies Prometheus alert rules + Alertmanager channels
# Estimated Time: 1 hour
###############################################################################

set -e  # Exit on error

echo "=== SPRINT 33 DAY 5 - MONITORING SETUP ==="
echo "Applying Prometheus alert rules + Alertmanager configuration"
echo

# Step 1: Copy alert rules to Prometheus container
echo "Step 1: Copying alert-rules.yml to Prometheus container..."
docker cp infrastructure/monitoring/prometheus/alert-rules.yml \
  sdlc-prometheus:/etc/prometheus/alert-rules.yml

if [ $? -eq 0 ]; then
  echo "✅ Alert rules copied successfully"
else
  echo "❌ Failed to copy alert rules"
  exit 1
fi
echo

# Step 2: Validate rules syntax
echo "Step 2: Validating alert rules syntax..."
docker exec sdlc-prometheus \
  promtool check rules /etc/prometheus/alert-rules.yml

if [ $? -eq 0 ]; then
  echo "✅ Alert rules syntax valid"
else
  echo "❌ Alert rules syntax invalid - please fix errors above"
  exit 1
fi
echo

# Step 3: Update prometheus.yml to include alert rules
echo "Step 3: Updating prometheus.yml with rule_files..."

# Check if rule_files already exists
RULE_FILES_EXISTS=$(docker exec sdlc-prometheus grep -c "^rule_files:" /etc/prometheus/prometheus.yml || echo "0")

if [ "$RULE_FILES_EXISTS" -gt 0 ]; then
  echo "⚠️  rule_files section already exists in prometheus.yml"
  echo "   Checking if alert-rules.yml is already referenced..."

  ALERT_RULES_EXISTS=$(docker exec sdlc-prometheus grep -c "alert-rules.yml" /etc/prometheus/prometheus.yml || echo "0")

  if [ "$ALERT_RULES_EXISTS" -gt 0 ]; then
    echo "✅ alert-rules.yml already referenced - skipping update"
  else
    echo "   Adding alert-rules.yml to existing rule_files section..."
    docker exec sdlc-prometheus sh -c "sed -i '/^rule_files:/a\  - /etc/prometheus/alert-rules.yml' /etc/prometheus/prometheus.yml"
    echo "✅ Added alert-rules.yml to prometheus.yml"
  fi
else
  echo "   Adding new rule_files section to prometheus.yml..."
  docker exec sdlc-prometheus sh -c "cat >> /etc/prometheus/prometheus.yml <<'EOF'

# Alert Rules (Sprint 33 Day 5)
rule_files:
  - /etc/prometheus/alert-rules.yml
EOF"
  echo "✅ Added rule_files section to prometheus.yml"
fi
echo

# Step 4: Validate prometheus.yml configuration
echo "Step 4: Validating complete Prometheus configuration..."
docker exec sdlc-prometheus \
  promtool check config /etc/prometheus/prometheus.yml

if [ $? -eq 0 ]; then
  echo "✅ Prometheus configuration valid"
else
  echo "❌ Prometheus configuration invalid - please fix errors above"
  exit 1
fi
echo

# Step 5: Restart Prometheus to load new rules
echo "Step 5: Restarting Prometheus to load alert rules..."
docker restart sdlc-prometheus
sleep 5  # Wait for Prometheus to start

# Check if Prometheus is healthy
PROMETHEUS_HEALTHY=$(curl -sf http://localhost:9092/-/healthy && echo "yes" || echo "no")

if [ "$PROMETHEUS_HEALTHY" = "yes" ]; then
  echo "✅ Prometheus restarted successfully"
else
  echo "❌ Prometheus health check failed after restart"
  echo "   Check logs: docker logs sdlc-prometheus --tail 50"
  exit 1
fi
echo

# Step 6: Verify alert rules loaded
echo "Step 6: Verifying alert rules loaded..."
RULES_LOADED=$(curl -s http://localhost:9092/api/v1/rules | jq '.data.groups | length')

if [ "$RULES_LOADED" -gt 0 ]; then
  echo "✅ Alert rules loaded: $RULES_LOADED rule groups"
  echo
  echo "Rule Groups:"
  curl -s http://localhost:9092/api/v1/rules | jq -r '.data.groups[].name' | sed 's/^/  - /'
  echo
else
  echo "❌ No alert rules loaded - check Prometheus logs"
  docker logs sdlc-prometheus --tail 30
  exit 1
fi
echo

# Step 7: Update Alertmanager configuration
echo "Step 7: Updating Alertmanager configuration..."

# Check if alertmanager.yml exists in repo
if [ -f "infrastructure/monitoring/prometheus/alertmanager.yml" ]; then
  docker cp infrastructure/monitoring/prometheus/alertmanager.yml \
    sdlc-alertmanager:/etc/alertmanager/alertmanager.yml

  echo "✅ Alertmanager config copied"

  # Restart Alertmanager
  echo "   Restarting Alertmanager..."
  docker restart sdlc-alertmanager
  sleep 3

  echo "✅ Alertmanager restarted"
else
  echo "⚠️  alertmanager.yml not found in infrastructure/monitoring/prometheus/"
  echo "   Skipping Alertmanager config update"
  echo "   Current config: webhook to http://127.0.0.1:5001/"
fi
echo

# Step 8: Verify alert endpoints
echo "Step 8: Verifying alert endpoints..."

# Check Prometheus targets
echo "Prometheus Targets:"
TARGETS_UP=$(curl -s http://localhost:9092/api/v1/targets | jq -r '.data.activeTargets[] | select(.health=="up") | .labels.job' | wc -l)
TARGETS_TOTAL=$(curl -s http://localhost:9092/api/v1/targets | jq '.data.activeTargets | length')
echo "  UP: $TARGETS_UP / $TARGETS_TOTAL"

if [ "$TARGETS_UP" -eq "$TARGETS_TOTAL" ]; then
  echo "✅ All Prometheus targets UP"
else
  echo "⚠️  Some targets are DOWN - check Prometheus UI: http://localhost:9092/targets"
fi
echo

# Check Alertmanager
ALERTMANAGER_HEALTHY=$(curl -sf http://localhost:9095/-/healthy && echo "yes" || echo "no")

if [ "$ALERTMANAGER_HEALTHY" = "yes" ]; then
  echo "✅ Alertmanager healthy: http://localhost:9095"
else
  echo "⚠️  Alertmanager health check failed"
fi
echo

# Step 9: Display key alert rules
echo "Step 9: Key Alert Rules Summary..."
echo
echo "Critical Alerts (will page on-call):"
curl -s http://localhost:9092/api/v1/rules | jq -r '.data.groups[].rules[] | select(.labels.severity=="critical") | "  - \(.alert): \(.annotations.summary)"' | head -5
echo
echo "Warning Alerts (will notify Slack):"
curl -s http://localhost:9092/api/v1/rules | jq -r '.data.groups[].rules[] | select(.labels.severity=="warning") | "  - \(.alert): \(.annotations.summary)"' | head -5
echo

# Step 10: Test alert firing (optional)
echo "Step 10: Test Alert Firing (Optional)..."
echo "To test alert firing, you can:"
echo "  1. Simulate high latency: ab -n 10000 -c 100 http://localhost:8300/health"
echo "  2. Check firing alerts: curl http://localhost:9092/api/v1/alerts | jq '.data.alerts[] | select(.state==\"firing\")'"
echo "  3. Check Alertmanager: http://localhost:9095/#/alerts"
echo

# Summary
echo "=== MONITORING SETUP COMPLETE ==="
echo
echo "✅ Prometheus Alert Rules: $RULES_LOADED groups loaded"
echo "✅ Prometheus Targets: $TARGETS_UP / $TARGETS_TOTAL UP"
echo "✅ Alertmanager: $([ "$ALERTMANAGER_HEALTHY" = "yes" ] && echo "Healthy" || echo "Check logs")"
echo
echo "Next Steps:"
echo "1. Configure Slack webhook in alertmanager.yml (if not done)"
echo "2. Test alert firing with load test"
echo "3. Verify Slack notification received"
echo "4. Submit G3 approval request to CTO/CPO"
echo
echo "Monitoring Dashboard URLs:"
echo "  - Prometheus: http://localhost:9092"
echo "  - Alertmanager: http://localhost:9095"
echo "  - Grafana: http://localhost:3002"
echo
echo "=== SETUP COMPLETE - Day 5 Monitoring Ready ==="
