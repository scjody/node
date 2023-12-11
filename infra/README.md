# NODE BBS infrastructure

Our reimplementation of the NODE Computing BBS is cloud-based (mostly GCP), and is managed via [Pulumi](https://www.pulumi.com/).

```plantuml
card LLM {
  component gce [
    GCE builder
    e2_micro
    30 GB disk
  ]

  database gar [
    GAR
    0.5 GB + 💸
  ]

  component gke [
    GKE
    Autopilot
  ]

  collections llm [
    LLM pods
    💸 (when running)
  ]

  database gcs [
    GCS model storage
    5 GB + 💸
  ]
}

gke -d-> llm
gce -d-> gar
gce -d-> gcs
llm -r-> gcs

card "BBS and Game" {
  component bbs [
    BBS
    Cloud Run
    Rust
  ]

  database cockroach [
    CockroachDB
  ]

  component game [
    game controller
    Tech stack TBD
  ]

  database tbd [
    Game state
    TBD
  ]

  queue events [
    Cloud PubSub events
    10 GB / month
  ]
}

bbs -l-> cockroach
bbs -d-> events : events
events -> game
game -> bbs : "messages to users &\nspecial commands\n(via REST API)"
game -> llm : "Rest API"
game -> tbd

cloud tailscale

collections terminals [
  NODE Computing
  Terminals
]

terminals -> tailscale
tailscale -l-> bbs
```
