output "services" {
  value = {
    for name, service in google_cloud_run_v2_service.web : name => {
      project         = service.project
      region          = service.location
      name            = service.name
      uri             = service.uri
      runtime_account = google_service_account.runtime[name].email
      image           = service.template[0].containers[0].image
    }
  }
}
