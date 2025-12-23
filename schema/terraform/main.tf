terraform {
  required_providers {
    proxmox = {
      source = "telmate/proxmox"
      version = "3.0.2-rc07"
    }
  }
}

provider "proxmox" {
  # Proxmox API configuration
  pm_api_url = var.api_url
  # Proxmox API token configuration
  pm_api_token_id = var.token_id
  # Proxmox API token secret
  pm_api_token_secret = var.token_secret
  # Proxmox TLS insecure configuration
  pm_tls_insecure = true
}

#Define the resource
resource "proxmox_vm_qemu" "tyre01" {
    name = "tyre01"
    target_node = var.proxmox_host
    count = 1
    vmid = "600"

    clone = var.template_name
    full_clone = true
    
    #Assign the VM to a resource pool
    pool = "Development"

    # VM settings `agent-1` enables the qemu guest agent for ssh access
    agent = 1
    os_type = "cloud-init"
    memory = 4096
    scsihw = "virtio-scsi-pci"
    boot = "order=scsi0"
    bootdisk = "scsi0"

    #SSH Settings
    ssh_user = "taylor"
    ssh_private_key = var.ssh_private_key
    sshkeys = var.ssh_key

    # Assign static IP for the VM/s
    ipconfig0 = "ip=192.168.40.40/24,gw=192.168.40.1"

    # Set username and password for the VM
    ciuser = var.ciuser
    cipassword = var.cipassword

    cpu {
        cores = 2
        sockets = 1
        type = "host"
    }

    disk {
        slot = "scsi0"
        size = "35G"
        type = "disk"
        storage = "CephFS" # Name of the storage to the host that will be used for the VM's boot disk
        #Enables thin provisioning for better performance
        discard = true
        #Don't backup the VM
        backup = false
    }

    # Cloud-init drive - keeps the cloud-init drive attached after VM creation
    disk {
        slot = "ide2"
        type = "cloudinit"
        storage = "local-lvm"
        backup = false
    }

    network {
        id = 0
        bridge = "vmbr0"
        model = "virtio"
        tag = var.vlan_num
    }

    lifecycle {
        ignore_changes = [
            network,
        ]
    }

    #Display
    serial {
        id = 0
        type = "socket"
    }
}

#Define the resource
resource "proxmox_vm_qemu" "tyresql01" {
    name = "tyresql01"
    target_node = var.proxmox_host
    count = 1
    vmid = "601"

    clone = var.template_name
    full_clone = true
    
    #Assign the VM to a resource pool
    pool = "Development"

    # VM settings `agent-1` enables the qemu guest agent for ssh access
    agent = 1
    os_type = "cloud-init"
    memory = 4096
    scsihw = "virtio-scsi-pci"
    boot = "order=scsi0"
    bootdisk = "scsi0"

    #SSH Settings
    ssh_user = "taylor"
    ssh_private_key = var.ssh_private_key
    sshkeys = var.ssh_key

    # Assign static IP for the VM/s
    ipconfig0 = "ip=192.168.40.41/24,gw=192.168.40.1"

    # Set username and password for the VM
    ciuser = var.ciuser
    cipassword = var.cipassword

    cpu {
        cores = 2
        sockets = 1
        type = "host"
    }

    disk {
        slot = "scsi0"
        size = "35G"
        type = "disk"
        storage = "CephFS" # Name of the storage to the host that will be used for the VM's boot disk
        #Enables thin provisioning for better performance
        discard = true
        #Don't backup the VM
        backup = false
    }

    # Cloud-init drive - keeps the cloud-init drive attached after VM creation
    disk {
        slot = "ide2"
        type = "cloudinit"
        storage = "local-lvm"
        backup = false
    }

    network {
        id = 0
        bridge = "vmbr0"
        model = "virtio"
        tag = var.vlan_num
    }

    lifecycle {
        ignore_changes = [
            network,
        ]
    }

    #Display
    serial {
        id = 0
        type = "socket"
    }
}