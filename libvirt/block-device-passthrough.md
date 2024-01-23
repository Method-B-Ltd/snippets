This is a brief guide to passing through a block device to a VM using libvirt. I assume the reader has a good reason to do this. If you don't need to do this, consider whether using qcow2 files or storage pools would be easier to manage.

You want to pass through a block device that's available on the host for the exclusive use for the guest. You know that there is a risk of data loss if you get this wrong. You've checked that you have backups of any important data on the block device.

It appears that there is no user-friendly way to do this in virt-manager's GUI, but you can edit the XML in virt-manager or using `virsh edit`.

The host must not use the block device. The expected use case is a dedicated disk for the VM, a dedicated logical volume (an LVM LV), etc. The block device needs to be visible to the host, but it must not be mounted. You probably shouldn't do this with a partition, even though it's possible.

In this example, the device on the host is /dev/disk/by-uuid/f380535a-ef20-4d54-8b79-f2b62834ec33 and is made available as /dev/sdb in the guest. Use stable references to block devices (e.g. in /dev/disk/by-uuid or /dev/mapper) when defining your source.

You'll need to add XML like this inside the devices element of the XML. 

```xml    
<!-- Each disk has its own element. -->
<!-- The type attribute is always block where the source is a block device. -->
<!-- The device attribute will usually be disk and controls how it is presented to the guest. -->
<disk type='block' device='disk'>
  <!-- It's a raw block device, no other type makes sense here. -->
  <driver name='qemu' type='raw'/>
  <!-- The source element is where you define the block device on the host. -->
  <source dev='/dev/disk/by-uuid/f380535a-ef20-4d54-8b79-f2b62834ec33'/>
  <!-- The target element is where you define the block device in the guest. -->
  <target dev='sdb' bus='sata'/>
</disk>
```

This example uses the SATA bus, your VM will require a SATA controller, which you can set up in virt-manager if it hasn't been created by default. It will look something like this in the XML.

```xml
<controller type='sata' index='0'>
  <address type='pci' domain='0x0000' bus='0x00' slot='0x1f' function='0x2'/>
</controller>
```

Once you've applied your XML, you'll be able to edit the boot order and certain other settings inside virt-manager.

Tried on Ubuntu 22.04 (Jammy), libvirt 8.0.0, virt-manager 4.0.0. Tested as system VM, not as a user VM. 