resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = "0.27.0"

  set {
    name  = "server.extraEnvironmentVars.VAULT_TOKEN_TTL"
    value = "15m"
  }
}
