variable "owner_identity" {
  type        = string
  description = "Declared project owner; this guard does not grant or verify IAM ownership."
  validation {
    condition     = var.owner_identity == "player.one@anderzilla.com"
    error_message = "Use the explicitly authorized AnderZilla Google identity."
  }
}

variable "environments" {
  description = "Two existing, separately approved GCP projects. Image must already exist in each project registry."
  type = map(object({
    project_id = string
    region     = string
    image      = string
  }))
  validation {
    condition     = toset(keys(var.environments)) == toset(["homolog", "production"])
    error_message = "Supply exactly homolog and production."
  }
  validation {
    condition = (
      length(distinct([for env in values(var.environments) : env.project_id])) == 2 &&
      alltrue([for env in values(var.environments) : can(regex("^anderzilla-[a-z0-9-]+[a-z0-9]$", env.project_id))])
    )
    error_message = "Use two different existing project IDs prefixed anderzilla-."
  }
  validation {
    condition = alltrue([
      for env in values(var.environments) :
      can(regex("^[a-z]+-[a-z]+[0-9]+$", env.region)) &&
      startswith(env.image, "${env.region}-docker.pkg.dev/${env.project_id}/anderzilla/web@sha256:") &&
      can(regex("@sha256:[a-f0-9]{64}$", env.image))
    ])
    error_message = "Use a region and immutable web image digest in that project's anderzilla repository."
  }
}

variable "production_public" {
  description = "Explicit opt-in to unauthenticated production access. Homolog never receives allUsers."
  type        = bool
  default     = false
}
