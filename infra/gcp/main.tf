locals {
  required_services = toset(["run.googleapis.com", "artifactregistry.googleapis.com", "iam.googleapis.com"])
  api_instances = {
    for pair in setproduct(keys(var.environments), local.required_services) :
    "${pair[0]}/${pair[1]}" => { environment = pair[0], service = pair[1] }
  }
}

resource "google_project_service" "required" {
  for_each           = local.api_instances
  project            = var.environments[each.value.environment].project_id
  service            = each.value.service
  disable_on_destroy = false
}

resource "google_service_account" "runtime" {
  for_each     = var.environments
  project      = each.value.project_id
  account_id   = "anderzilla-web-runtime"
  display_name = "AnderZilla web runtime (${each.key})"
  depends_on   = [google_project_service.required]
}

resource "google_artifact_registry_repository" "web" {
  for_each      = var.environments
  project       = each.value.project_id
  location      = each.value.region
  repository_id = "anderzilla"
  format        = "DOCKER"
  description   = "AnderZilla web images (${each.key})"

  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions { keep_count = 10 }
  }
  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "2592000s"
    }
  }
  lifecycle { prevent_destroy = true }
  depends_on = [google_project_service.required]
}

resource "google_cloud_run_v2_service" "web" {
  for_each            = var.environments
  project             = each.value.project_id
  location            = each.value.region
  name                = "anderzilla-web-${each.key}"
  deletion_protection = true
  ingress             = "INGRESS_TRAFFIC_ALL"
  labels              = { brand = "anderzilla", environment = each.key }

  scaling {
    min_instance_count = 0
    max_instance_count = 1
  }
  template {
    service_account                  = google_service_account.runtime[each.key].email
    max_instance_request_concurrency = 40
    timeout                          = "60s"
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
    containers {
      image = each.value.image
      ports { container_port = 8080 }
      resources {
        limits            = { cpu = "1", memory = "512Mi" }
        cpu_idle          = true
        startup_cpu_boost = false
      }
    }
  }
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  lifecycle {
    # Terraform owns service settings; the release workflow owns image revisions.
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }
  depends_on = [google_project_service.required, google_artifact_registry_repository.web]
}

resource "google_cloud_run_v2_service_iam_member" "production_public" {
  count    = var.production_public ? 1 : 0
  project  = var.environments["production"].project_id
  location = var.environments["production"].region
  name     = google_cloud_run_v2_service.web["production"].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
