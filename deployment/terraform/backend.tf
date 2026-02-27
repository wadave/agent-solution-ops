terraform {
  backend "gcs" {
    bucket = "dw-genai-dev-terraform-state"
    prefix = "agent-solution-ops/prod"
  }
}
