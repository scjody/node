import pulumi
import pulumi_gcp as gcp

provider_cfg = pulumi.Config("gcp")
gcp_project = provider_cfg.require("project")
gcp_region = provider_cfg.get("region", "us-central1")
config = pulumi.Config()

apis = {}
for api in [
    "container.googleapis.com",
    "compute.googleapis.com",
]:
    apis[api] = gcp.projects.Service(api, project=gcp_project, service=api)

gke_network = gcp.compute.Network(
    "gke-network",
    auto_create_subnetworks=False,
    description="Virtual network for GKE cluster(s)",
)

gke_subnet = gcp.compute.Subnetwork(
    "gke-subnet",
    ip_cidr_range="10.128.0.0/12",
    network=gke_network.id,
    private_ip_google_access=True,
)

gke_cluster = gcp.container.Cluster(
    "machine-learning",
    opts=pulumi.ResourceOptions(ignore_changes=["nodePoolDefaults"]),
    binary_authorization=gcp.container.ClusterBinaryAuthorizationArgs(
        evaluation_mode="PROJECT_SINGLETON_POLICY_ENFORCE"
    ),
    datapath_provider="ADVANCED_DATAPATH",
    description="Machine Learning",
    dns_config=gcp.container.ClusterDnsConfigArgs(
        cluster_dns="CLOUD_DNS",
        cluster_dns_domain="cluster.local",
        cluster_dns_scope="CLUSTER_SCOPE",
    ),
    enable_autopilot=True,
    initial_node_count=0,
    ip_allocation_policy=gcp.container.ClusterIpAllocationPolicyArgs(
        cluster_ipv4_cidr_block="/14", services_ipv4_cidr_block="/20"
    ),
    location=gcp_region,
    master_authorized_networks_config=gcp.container.ClusterMasterAuthorizedNetworksConfigArgs(
        cidr_blocks=[
            gcp.container.ClusterMasterAuthorizedNetworksConfigCidrBlockArgs(
                cidr_block="0.0.0.0/0", display_name="All networks"
            )
        ]
    ),
    network=gke_network.name,
    networking_mode="VPC_NATIVE",
    private_cluster_config=gcp.container.ClusterPrivateClusterConfigArgs(
        enable_private_nodes=True,
        enable_private_endpoint=False,
        master_ipv4_cidr_block="10.100.0.0/28",
    ),
    release_channel=gcp.container.ClusterReleaseChannelArgs(channel="STABLE"),
    subnetwork=gke_subnet.name,
)

cluster_kubeconfig = pulumi.Output.all(
    gke_cluster.master_auth.cluster_ca_certificate,
    gke_cluster.endpoint,
    gke_cluster.name,
).apply(
    lambda l: f"""apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {l[0]}
    server: https://{l[1]}
  name: {l[2]}
contexts:
- context:
    cluster: {l[2]}
    user: {l[2]}
  name: {l[2]}
current-context: {l[2]}
kind: Config
preferences: {{}}
users:
- name: {l[2]}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
"""
)

pulumi.export("networkName", gke_network.name)
pulumi.export("networkId", gke_network.id)
pulumi.export("clusterName", gke_cluster.name)
pulumi.export("clusterId", gke_cluster.id)
pulumi.export("kubeconfig", cluster_kubeconfig)

instance = gcp.compute.Instance(
    "build",
    machine_type="e2-micro",
    boot_disk=gcp.compute.InstanceBootDiskArgs(
        initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
            image="ubuntu-2204-jammy-v20231201",
            size=30,
        ),
    ),
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network="default",
            access_configs=[
                gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()
            ],  # Creates a public IP
        )
    ],
    zone="us-central1-c",
)

pulumi.export("instance_name", instance.name)
pulumi.export("instance_machine_type", instance.machine_type)
pulumi.export("instance_zone", instance.zone)
