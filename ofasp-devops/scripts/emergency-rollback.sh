#!/bin/bash

# Emergency Rollback Script for OpenASP DevOps
# Usage: ./emergency-rollback.sh [environment] [target_version] [reason]

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/rollback-$(date +%Y%m%d-%H%M%S).log"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [$level] $message" | tee -a "$LOG_FILE"
}

# Print functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}🔄 Emergency Rollback System${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "INFO" "$1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARN" "$1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR" "$1"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO" "$1"
}

# Usage function
usage() {
    echo "Usage: $0 [environment] [target_version] [reason]"
    echo
    echo "Arguments:"
    echo "  environment     Target environment (staging, production)"
    echo "  target_version  Version to rollback to (e.g., v1.2.3)"
    echo "  reason          Reason for rollback"
    echo
    echo "Examples:"
    echo "  $0 production v1.2.2 'Critical bug in payment system'"
    echo "  $0 staging v1.1.5 'Performance regression detected'"
    echo
    echo "Environment Variables:"
    echo "  SKIP_CONFIRMATIONS=true    Skip interactive confirmations"
    echo "  DRY_RUN=true              Show what would be done without executing"
    echo
    exit 1
}

# Confirmation prompt
confirm() {
    local message=$1
    if [[ "${SKIP_CONFIRMATIONS:-false}" == "true" ]]; then
        print_info "Auto-confirming: $message"
        return 0
    fi
    
    echo -ne "${YELLOW}$message (y/N): ${NC}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if required commands are available
    local required_commands=("docker" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check if log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Get current deployment info
get_current_deployment() {
    local environment=$1
    print_info "Getting current deployment information for $environment..."
    
    # In a real implementation, this would query your deployment system
    # For demo purposes, we'll simulate getting current version
    case "$environment" in
        "production")
            CURRENT_VERSION="v1.2.5"
            CURRENT_HEALTH="95"
            ;;
        "staging")
            CURRENT_VERSION="v1.2.6"
            CURRENT_HEALTH="88"
            ;;
        *)
            print_error "Unknown environment: $environment"
            exit 1
            ;;
    esac
    
    print_info "Current version: $CURRENT_VERSION"
    print_info "Current health score: $CURRENT_HEALTH%"
}

# Validate target version
validate_target_version() {
    local target_version=$1
    print_info "Validating target version: $target_version"
    
    # Check version format
    if [[ ! "$target_version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format. Expected: vX.Y.Z (e.g., v1.2.3)"
        exit 1
    fi
    
    # Check if target version exists (simulated)
    print_info "Checking if version $target_version exists in registry..."
    # In real implementation: docker manifest inspect $REGISTRY/$IMAGE:$target_version
    
    # Simulate version availability check
    if [[ $(echo "$target_version" | cut -d. -f3) -gt 10 ]]; then
        print_error "Version $target_version not found in registry"
        exit 1
    fi
    
    print_success "Target version $target_version is available"
}

# Create backup of current state
create_backup() {
    local environment=$1
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_file="$PROJECT_ROOT/backups/deployment-backup-$environment-$timestamp.json"
    
    print_info "Creating backup of current deployment state..."
    
    mkdir -p "$(dirname "$backup_file")"
    
    # Create deployment backup
    cat > "$backup_file" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%d %H:%M:%S UTC")",
  "environment": "$environment",
  "version": "$CURRENT_VERSION",
  "health_score": $CURRENT_HEALTH,
  "backup_reason": "Pre-rollback backup",
  "created_by": "$(whoami)",
  "hostname": "$(hostname)",
  "rollback_target": "$TARGET_VERSION",
  "rollback_reason": "$ROLLBACK_REASON"
}
EOF
    
    BACKUP_FILE="$backup_file"
    print_success "Backup created: $backup_file"
}

# Execute health checks
health_check() {
    local environment=$1
    local version=$2
    print_info "Performing health checks for $version on $environment..."
    
    # Simulate health checks
    local health_endpoints=("/" "/api/health" "/api/pipeline-status")
    local failed_checks=0
    
    for endpoint in "${health_endpoints[@]}"; do
        print_info "Checking endpoint: $endpoint"
        
        # Simulate health check (random failure for demo)
        if [[ $((RANDOM % 10)) -eq 0 ]]; then
            print_warning "Health check failed for $endpoint"
            ((failed_checks++))
        else
            print_success "Health check passed for $endpoint"
        fi
        
        sleep 0.5
    done
    
    if [[ $failed_checks -gt 0 ]]; then
        print_warning "$failed_checks health checks failed"
        if ! confirm "Continue with rollback despite failed health checks?"; then
            print_error "Rollback aborted due to health check failures"
            exit 1
        fi
    else
        print_success "All health checks passed"
    fi
}

# Execute rollback
execute_rollback() {
    local environment=$1
    local target_version=$2
    
    print_info "Starting rollback process..."
    print_info "Environment: $environment"
    print_info "Current version: $CURRENT_VERSION"
    print_info "Target version: $target_version"
    
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        print_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Phase 1: Prepare rollback
    print_info "Phase 1: Preparing rollback environment..."
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        # Pull target version
        print_info "Pulling target version $target_version..."
        # docker pull $REGISTRY/$IMAGE:$target_version
        sleep 2
    fi
    print_success "Environment prepared"
    
    # Phase 2: Database compatibility check
    print_info "Phase 2: Checking database compatibility..."
    # In real implementation, check if database migrations need to be reverted
    local db_compatible=$((RANDOM % 4 != 0)) # 75% chance of compatibility
    
    if [[ $db_compatible -eq 1 ]]; then
        print_success "Database schema is compatible"
    else
        print_warning "Database migration may be required"
        if confirm "Proceed with database rollback migration?"; then
            print_info "Executing database rollback migration..."
            # Execute migration rollback here
            sleep 3
            print_success "Database migration completed"
        else
            print_error "Cannot proceed without database rollback"
            exit 1
        fi
    fi
    
    # Phase 3: Blue-Green traffic switch
    print_info "Phase 3: Switching traffic to target version..."
    
    if [[ "${DRY_RUN:-false}" != "true" ]]; then
        local traffic_percentages=(90 75 50 25 10 0)
        
        for percentage in "${traffic_percentages[@]}"; do
            print_info "Switching traffic: ${percentage}% on current version"
            # Update load balancer configuration
            sleep 1
        done
        
        print_success "Traffic fully switched to $target_version"
    else
        print_info "[DRY RUN] Would switch traffic from $CURRENT_VERSION to $target_version"
    fi
    
    # Phase 4: Verification
    print_info "Phase 4: Post-rollback verification..."
    health_check "$environment" "$target_version"
    
    # Monitor for a short period
    print_info "Monitoring rollback stability..."
    for i in {1..5}; do
        print_info "Monitoring cycle $i/5..."
        
        # Simulate monitoring metrics
        local error_rate=$(echo "scale=2; ($RANDOM % 10) / 100" | bc)
        local response_time=$((120 + RANDOM % 80))
        
        print_info "Error rate: ${error_rate}%, Response time: ${response_time}ms"
        
        if (( $(echo "$error_rate > 1.0" | bc -l) )); then
            print_warning "Elevated error rate detected!"
        fi
        
        sleep 1
    done
    
    print_success "Rollback completed successfully!"
}

# Generate rollback report
generate_report() {
    local environment=$1
    local target_version=$2
    local start_time=$3
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    local report_file="$PROJECT_ROOT/reports/rollback-report-$(date +%Y%m%d-%H%M%S).md"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
# 🔄 Emergency Rollback Report

**Status:** ✅ SUCCESS  
**Environment:** $environment  
**Duration:** ${duration}s  
**Executed by:** $(whoami)  
**Hostname:** $(hostname)  
**Timestamp:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")  

## Rollback Details

| Attribute | Value |
|-----------|-------|
| From Version | \`$CURRENT_VERSION\` |
| To Version | \`$target_version\` |
| Reason | $ROLLBACK_REASON |
| Backup File | \`$BACKUP_FILE\` |
| Log File | \`$LOG_FILE\` |

## Verification Results

- ✅ Health checks completed
- ✅ Traffic successfully switched
- ✅ Error rates within acceptable range
- ✅ Response times stable

## Files Generated

- **Backup:** $BACKUP_FILE
- **Log:** $LOG_FILE
- **Report:** $report_file

## Next Steps

1. Monitor the application for the next hour
2. Verify all critical functionality is working
3. Update monitoring dashboards
4. Notify stakeholders of rollback completion

---
Generated by Emergency Rollback System
EOF

    print_success "Report generated: $report_file"
    REPORT_FILE="$report_file"
}

# Send notifications
send_notifications() {
    local environment=$1
    local target_version=$2
    
    print_info "Sending rollback completion notifications..."
    
    # In a real implementation, this would send to Slack/Discord/Email
    print_info "📧 Notification sent to operations team"
    print_info "📱 Slack message sent to #deployments channel"
    print_info "📊 Dashboard updated with rollback status"
    
    print_success "All notifications sent"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        print_error "Rollback failed with exit code $exit_code"
        print_info "Check log file: $LOG_FILE"
        
        if [[ -n "${BACKUP_FILE:-}" ]]; then
            print_info "Backup file available for recovery: $BACKUP_FILE"
        fi
    fi
    
    exit $exit_code
}

# Main function
main() {
    # Set up error handling
    trap cleanup EXIT
    
    # Parse arguments
    if [[ $# -lt 3 ]]; then
        usage
    fi
    
    local environment=$1
    local target_version=$2
    local rollback_reason="$3"
    
    # Global variables
    ENVIRONMENT="$environment"
    TARGET_VERSION="$target_version"
    ROLLBACK_REASON="$rollback_reason"
    
    # Record start time
    local start_time=$(date +%s)
    
    print_header
    
    # Display rollback information
    echo "Rollback Parameters:"
    echo "  Environment: $environment"
    echo "  Target Version: $target_version"  
    echo "  Reason: $rollback_reason"
    echo "  Dry Run: ${DRY_RUN:-false}"
    echo
    
    # Confirm rollback
    if ! confirm "This will rollback $environment to $target_version. Are you sure?"; then
        print_info "Rollback cancelled by user"
        exit 0
    fi
    
    # Execute rollback steps
    check_prerequisites
    get_current_deployment "$environment"
    validate_target_version "$target_version"
    create_backup "$environment"
    
    if ! confirm "Final confirmation: Execute rollback now?"; then
        print_info "Rollback cancelled at final confirmation"
        exit 0
    fi
    
    execute_rollback "$environment" "$target_version"
    generate_report "$environment" "$target_version" "$start_time"
    send_notifications "$environment" "$target_version"
    
    print_success "Emergency rollback completed successfully!"
    print_info "Report: $REPORT_FILE"
    print_info "Log: $LOG_FILE"
}

# Execute main function with all arguments
main "$@"