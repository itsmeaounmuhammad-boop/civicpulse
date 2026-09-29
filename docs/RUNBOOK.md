# CivicPulse Runbook

## Deploy

## Cluster prerequisites (for local dev/testing)

- `kind` or `k3d` installed
- `kubectl` installed

### metrics-server (required for HPA)

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml


On `kind` specifically, the default install fails its readiness check because
`kind` nodes use self-signed kubelet certificates that don't validate against
the standard CA chain. Patch it to skip TLS verification (acceptable for a
local dev cluster only — never do this against a real production cluster):

kubectl patch deployment metrics-server -n kube-system --type=json --patch-file=metrics-server-patch.json


where `metrics-server-patch.json` contains:
```json
[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]
```

Confirm it's actually healthy before relying on it:

kubectl get pods -n kube-system | grep metrics-server # want 1/1 Running
kubectl top pods -n civicpulse


### VPA (not a built-in Kubernetes API)

The install script is bash, so on Windows run it inside WSL, Git Bash, or a
Linux CI runner — it will not run directly in PowerShell.

git clone https://github.com/kubernetes autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh


### Windows/PowerShell notes

- `kubectl patch` with inline JSON via `-p="[{...}]"` is unreliable in
  PowerShell due to quoting differences from bash — the server rejects it
  with a generic "invalid request" error that doesn't explain why. Use
  `--patch-file=<path>.json` instead; it sidesteps quoting entirely.
- `kubectl edit` opens the resource in whatever `$env:KUBE_EDITOR` is set to.
  Avoid Notepad for YAML edits — it can silently insert a tab character
  where a YAML list expects spaces, which fails validation with an
  unhelpful-looking error until you read the line number in the message
  carefully (`yaml: line N: found a tab character that violates indentation`).
  Use VS Code instead, which shows whitespace and won't do this.