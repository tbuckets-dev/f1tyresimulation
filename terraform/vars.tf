variable "proxmox_host" {
    default = "pve3"
}

variable "proxmox_hosts" {
    description = "List of Proxmox hosts for distributing VMs"
    type = list(string)
    default = ["pve2", "pve3"]
}

variable "template_name" {
    default = "ubuntu-init"
}

variable "nic_name" {
    default = "vmbr0"
}

variable "vlan_num" {
    default = "40"
}

variable "api_url" {
    default = "https://192.168.50.62:8006/api2/json"
}

variable "token_secret" {
}

variable "token_id" {
}

variable "ciuser" {
    description = "Cloud-init username"
}

variable "cipassword" {
    description = "Cloud-init password"
    sensitive = true
}

variable "ssh_private_key" {
}

variable "ssh_key" {
}