terraform {
  backend "gcs" {
    # Update this bucket name to your own Terraform state bucket before running.
    # The bucket must exist: gsutil mb -p YOUR_PROJECT gs://YOUR_PROJECT-terraform-state
    bucket = "dw-genai-dev-terraform-state"
    prefix = "agent-solution-ops/prod"
  }
}
