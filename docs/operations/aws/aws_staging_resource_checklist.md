# GrassRoots AWS Staging Resource Checklist

This checklist breaks Milestone 1 into concrete AWS resources and the order to create them.

## 1) Account and region decisions
- [ ] Pick the AWS region.
- [ ] Confirm the AWS account/environment name for staging.
- [ ] Confirm the naming convention for resources.
- [ ] Confirm tagging standard (`app`, `env`, `owner`, `cost-center`, `managed-by`).

## 2) Networking foundation
- [ ] Create a VPC.
- [ ] Create a public subnet for the EC2 instance.
- [ ] Create a private subnet for RDS.
- [ ] Create an internet gateway.
- [ ] Create route tables and associations.
- [ ] Create security groups:
  - [ ] EC2 app security group
  - [ ] RDS security group
  - [ ] CloudFront/S3 access policy as needed
- [ ] Confirm SSH access is restricted to admin IPs or replaced with SSM.

## 3) IAM and access
- [ ] Create an EC2 instance role.
- [ ] Attach permissions for:
  - [ ] S3 static/media access
  - [ ] SSM Parameter Store reads
  - [ ] CloudWatch logs writes
- [ ] Create a CI/CD role or GitHub OIDC role.
- [ ] Attach permissions for:
  - [ ] S3 static upload
  - [ ] ECR push if containers are introduced later
  - [ ] EC2 or Systems Manager deployment access if needed
- [ ] Verify no long-lived root credentials are used.

## 4) Staging compute
- [ ] Launch an EC2 instance for staging.
- [ ] Choose a small Graviton-based instance where compatible.
- [ ] Attach the EC2 role.
- [ ] Attach the correct security group.
- [ ] Allocate storage volume size appropriately.
- [ ] Install Nginx and Gunicorn prerequisites.

## 5) Staging database
- [ ] Create an RDS PostgreSQL instance.
- [ ] Use single-AZ for staging.
- [ ] Use a small class appropriate for staging.
- [ ] Set automated backups.
- [ ] Place RDS in private subnets.
- [ ] Restrict access to the app security group only.
- [ ] Save DB credentials in SSM or Secrets Manager.

## 6) Static and media storage
- [ ] Create S3 bucket for static assets.
- [ ] Create S3 bucket for media uploads.
- [ ] Enable versioning on buckets if desired.
- [ ] Configure lifecycle rules for old static releases.
- [ ] Set bucket policies to match the access model.
- [ ] Keep static and media in separate prefixes/buckets.

## 7) CDN and TLS
- [ ] Create CloudFront distribution for static assets.
- [ ] Set the origin to the static S3 bucket.
- [ ] Configure cache behavior for hashed static files.
- [ ] Request ACM certificate for the staging hostname if needed.
- [ ] Configure HTTPS-only access.
- [ ] Verify CloudFront domain works before linking the app.

## 8) Secrets and runtime configuration
- [ ] Store `DJANGO_SECRET_KEY` in SSM Parameter Store or Secrets Manager.
- [ ] Store `DJANGO_ALLOWED_HOSTS`.
- [ ] Store `DJANGO_CORS_ALLOWED_ORIGINS`.
- [ ] Store `DJANGO_CSRF_TRUSTED_ORIGINS`.
- [ ] Store database connection values.
- [ ] Store `DJANGO_STATIC_URL` and `DJANGO_MEDIA_URL`.

## 9) Observability
- [ ] Enable CloudWatch logs for the app.
- [ ] Enable basic EC2 metrics monitoring.
- [ ] Enable RDS monitoring and alarms.
- [ ] Create an alarm for failed health checks.
- [ ] Create an alarm for high RDS CPU/connection usage.

## 10) Provisioning order
1. Pick region and naming/tagging standards.
2. Create VPC, subnets, routing, and security groups.
3. Create IAM roles and secret storage.
4. Create RDS PostgreSQL.
5. Create S3 buckets for static and media.
6. Create CloudFront distribution and ACM certificate.
7. Launch EC2 and connect runtime roles.
8. Configure logs and alarms.
9. Wire the app settings to staging values.
10. Run staging smoke tests.

## 11) Exit criteria for resource provisioning
- [ ] All required AWS resources exist.
- [ ] Network boundaries are correct.
- [ ] The EC2 instance can reach RDS.
- [ ] The app can reach S3 for static/media.
- [ ] CloudFront can serve static content.
- [ ] Secrets are not stored in plain text on disk.
