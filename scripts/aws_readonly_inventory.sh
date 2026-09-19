#!/usr/bin/env bash
# Read-only AWS metadata inventory for the audit skill (full mode, step 2).
#
# Guard: every AWS call goes through aws_ro(), which allows ONLY the exact service and operation pairs listed in
# ALLOWED_OPS below (metadata reads used by this inventory) and additionally refuses secret-returning operations and
# --with-decryption. Anything else, including other describe-*/list-*/get-* operations, is refused; add a pair to
# ALLOWED_OPS deliberately after checking what it returns. Output is metadata only.
#
# Usage:
#   aws_readonly_inventory.sh --profile <name> --region <region> --out <dir> [--regions r1,r2]
#   aws_readonly_inventory.sh --self-test        # tests the guard; makes NO aws calls and needs no aws CLI
set -uo pipefail

ALLOWED_OPS=(
  "sts get-caller-identity"
  "ecs list-clusters" "ecs list-services" "ecs describe-services"
  "rds describe-db-instances" "rds describe-db-clusters"
  "ec2 describe-security-groups"
  "elbv2 describe-load-balancers"
  "wafv2 list-web-acls"
  "cloudwatch describe-alarms"
  "cloudtrail describe-trails"
  "backup list-backup-plans"
  "secretsmanager list-secrets"
  "s3api list-buckets" "s3api get-public-access-block" "s3api get-bucket-policy-status"
  "s3api get-bucket-versioning" "s3api get-bucket-encryption"
)
# Operations that return secrets, credentials, tokens, code or content: refused even if someone adds them above.
DENY_RE='^(get-secret-value|get-parameter|get-parameters|get-parameters-by-path|get-object|get-object-torrent|get-authorization-token|get-login-password|get-session-token|get-federation-token|get-credentials-for-identity|get-open-id-token|get-function|get-function-configuration|get-layer-version|get-password-data|get-console-output|get-console-screenshot|get-key-policy|get-public-key|get-rest-api|get-export|get-sdk|get-authorizer-token|get-login-profile|get-access-key-last-used|list-access-keys|describe-task-definition|get-bucket-policy|get-bucket-acl)$'

# aws_guard <service> <operation> [args...]: returns 0 if allowed, 97 not allowlisted, 98 denied content, 99 decryption flag
aws_guard() {
  local svc="${1:-}" op="${2:-}" pair found=1 a
  for pair in "${ALLOWED_OPS[@]}"; do [ "$pair" = "$svc $op" ] && found=0; done
  if [ "$found" -ne 0 ]; then echo "REFUSED (not in the allowlist): aws $svc $op" >&2; return 97; fi
  if [[ "$op" =~ $DENY_RE ]]; then echo "REFUSED (may return secrets or content): aws $svc $op" >&2; return 98; fi
  for a in "$@"; do
    if [ "$a" = "--with-decryption" ]; then echo "REFUSED (--with-decryption): aws $svc $op" >&2; return 99; fi
  done
  return 0
}

self_test() {
  local fails=0 expect rc
  t() { expect="$1"; shift; aws_guard "$@" 2>/dev/null; rc=$?; if [ "$rc" -ne "$expect" ]; then echo "FAIL: expected $expect got $rc for: $*"; fails=$((fails+1)); else echo "ok ($rc): $*"; fi; }
  t 0  sts get-caller-identity
  t 0  rds describe-db-instances --region x
  t 0  s3api get-bucket-versioning --bucket b
  t 97 ec2 delete-security-group --group-id g
  t 97 rds modify-db-instance --db-instance-identifier d
  t 97 ecs describe-task-definition --task-definition t         # returns environment values
  t 97 lambda get-function-configuration --function-name f      # returns environment values
  t 97 s3api get-bucket-policy --bucket b                       # returns policy content
  t 97 secretsmanager get-secret-value --secret-id s
  t 97 ssm get-parameter --name n
  t 97 s3api get-object --bucket b --key k
  t 97 ecr get-authorization-token
  t 97 iam list-access-keys
  t 97 ssm describe-parameters                                  # not allowlisted
  t 99 rds describe-db-instances --with-decryption
  # a denied operation must stay refused even if it were ever added to ALLOWED_OPS
  ALLOWED_OPS+=("s3api get-object"); t 98 s3api get-object --bucket b --key k
  if [ "$fails" -eq 0 ]; then echo "guard self-test passed"; return 0; fi
  echo "$fails guard self-test failure(s)"; return 1
}

if [ "${1:-}" = "--self-test" ]; then self_test; exit $?; fi
# Do nothing when sourced (so the guard can be inspected without running the inventory).
[ "${BASH_SOURCE[0]}" = "$0" ] || return 0 2>/dev/null || true

PROFILE=""; REGION=""; OUT=""; EXTRA_REGIONS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --regions) EXTRA_REGIONS="$2"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PROFILE" ] && [ -n "$REGION" ] && [ -n "$OUT" ] || { echo "need --profile, --region and --out (or --self-test)" >&2; exit 2; }
command -v aws >/dev/null || { echo "aws CLI not found: cloud evidence is Not Verified" >&2; exit 2; }
mkdir -p "$OUT"

# aws_ro <service> <operation> [args...]
aws_ro() {
  aws_guard "$@" || return $?
  aws --profile "$PROFILE" --output json --no-cli-pager "$@"
}

inventory_region() {
  local r="$1" d="$OUT/$1"; mkdir -p "$d"
  aws_r() { aws_ro "$1" "$2" --region "$r" "${@:3}"; }
  # ECS: names, counts, deployment safety (describe-services returns no environment values)
  aws_r ecs list-clusters > "$d/ecs-clusters.json" 2>/dev/null || echo '{"error":"ecs list-clusters failed"}' > "$d/ecs-clusters.json"
  for c in $(python3 -c 'import json,sys;[print(a.split("/")[-1]) for a in json.load(open(sys.argv[1])).get("clusterArns",[])]' "$d/ecs-clusters.json" 2>/dev/null); do
    aws_r ecs list-services --cluster "$c" > "$d/ecs-services-$c.json" 2>/dev/null
    svcs=$(python3 -c 'import json,sys;print(" ".join(a.split("/")[-1] for a in json.load(open(sys.argv[1])).get("serviceArns",[])))' "$d/ecs-services-$c.json" 2>/dev/null)
    [ -n "$svcs" ] && aws_r ecs describe-services --cluster "$c" --services $svcs \
      --query 'services[].{name:serviceName,desired:desiredCount,running:runningCount,taskDefinition:taskDefinition,circuitBreaker:deploymentConfiguration.deploymentCircuitBreaker,launchType:launchType}' \
      > "$d/ecs-describe-$c.json" 2>/dev/null
  done
  # RDS: exposure, backups, protection
  aws_r rds describe-db-instances --query 'DBInstances[].{id:DBInstanceIdentifier,engine:Engine,version:EngineVersion,class:DBInstanceClass,multiAZ:MultiAZ,backupRetentionDays:BackupRetentionPeriod,encrypted:StorageEncrypted,publiclyAccessible:PubliclyAccessible,deletionProtection:DeletionProtection,securityGroups:VpcSecurityGroups[].VpcSecurityGroupId}' > "$d/rds-instances.json" 2>/dev/null
  aws_r rds describe-db-clusters --query 'DBClusters[].{id:DBClusterIdentifier,engine:Engine,backupRetentionDays:BackupRetentionPeriod,encrypted:StorageEncrypted,deletionProtection:DeletionProtection}' > "$d/rds-clusters.json" 2>/dev/null
  # Security groups: ingress rules with open CIDRs
  aws_r ec2 describe-security-groups --query 'SecurityGroups[].{id:GroupId,name:GroupName,ingress:IpPermissions[].{proto:IpProtocol,from:FromPort,to:ToPort,cidrs:IpRanges[].CidrIp,groups:UserIdGroupPairs[].GroupId}}' > "$d/ec2-security-groups.json" 2>/dev/null
  # Load balancers, WAF, alarms, trails, backup plans, secret NAMES only
  aws_r elbv2 describe-load-balancers --query 'LoadBalancers[].{name:LoadBalancerName,scheme:Scheme,type:Type}' > "$d/elbv2.json" 2>/dev/null
  aws_r wafv2 list-web-acls --scope REGIONAL --query 'WebACLs[].Name' > "$d/wafv2.json" 2>/dev/null
  aws_r cloudwatch describe-alarms --query 'MetricAlarms[].{name:AlarmName,state:StateValue}' > "$d/cloudwatch-alarms.json" 2>/dev/null
  aws_r cloudtrail describe-trails --query 'trailList[].{name:Name,multiRegion:IsMultiRegionTrail}' > "$d/cloudtrail.json" 2>/dev/null
  aws_r backup list-backup-plans --query 'BackupPlansList[].BackupPlanName' > "$d/backup-plans.json" 2>/dev/null
  aws_r secretsmanager list-secrets --query 'SecretList[].Name' > "$d/secretsmanager-names.json" 2>/dev/null
}

# Identity (account id stays in the local output folder only)
aws_ro sts get-caller-identity > "$OUT/identity.json" 2>/dev/null || echo '{"error":"identity call failed"}' > "$OUT/identity.json"

inventory_region "$REGION"
for r in $(echo "$EXTRA_REGIONS" | tr ',' ' '); do [ -n "$r" ] && inventory_region "$r"; done

# Global S3: bucket names, public-access blocks, policy status, versioning, encryption (no object listing, no policy text)
aws_ro s3api list-buckets --query 'Buckets[].Name' > "$OUT/s3-buckets.json" 2>/dev/null
for b in $(python3 -c 'import json,sys;print(" ".join(json.load(open(sys.argv[1]))))' "$OUT/s3-buckets.json" 2>/dev/null); do
  mkdir -p "$OUT/s3"
  {
    printf '{"bucket":"%s",' "$b"
    printf '"publicAccessBlock":%s,' "$(aws_ro s3api get-public-access-block --bucket "$b" --query PublicAccessBlockConfiguration 2>/dev/null || echo null)"
    printf '"policyIsPublic":%s,' "$(aws_ro s3api get-bucket-policy-status --bucket "$b" --query PolicyStatus.IsPublic 2>/dev/null || echo null)"
    printf '"versioning":%s,' "$(aws_ro s3api get-bucket-versioning --bucket "$b" --query Status 2>/dev/null || echo null)"
    printf '"encryption":%s}\n' "$(aws_ro s3api get-bucket-encryption --bucket "$b" --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' 2>/dev/null || echo null)"
  } > "$OUT/s3/$b.json"
done
echo "Inventory written to $OUT (metadata only; contains account and resource identifiers, keep it local)."
