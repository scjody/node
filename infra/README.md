# NODE BBS infrastructure

Our work in progress reimplementation of the NODE Computing BBS is cloud-based (mostly GCP), and is managed via [Pulumi](https://www.pulumi.com/).

## Planned architecture
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

## Free tier services and limitations
The intention is to use free tier services whenever possible.
GKE has a [reasonable free tier](https://cloud.google.com/kubernetes-engine/pricing#cluster_management_fee_and_free_tier) that includes most of what we need.
It's missing a reasonable database though, so we plan on using the [free tier of CockroachDB Serverless](https://www.cockroachlabs.com/blog/serverless-free/).

We may need to pay for artifact (Docker image) and model storage, but hopefully we'll be able to leverage existing stores (e.g. the base Llama 2 models are already on GCS).

The LLM pod(s) are billable, but they're running on GKE with Autopilot, which scales to zero.
Therefore, we can avoid paying for them when we don't need them (unlike with Vertex AI, which can't scale to zero as of this writing).
