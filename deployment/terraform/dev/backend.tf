terraform {
  backend "gcs" {
    bucket = "dw-genai-pre-prod-terraform-state"
    prefix = "agent-solution-ops/dev"
  }
}
