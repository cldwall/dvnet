VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "fedora/36-cloud-base"
  config.ssh.forward_agent = true
  config.ssh.forward_x11 = true
  config.vm.synced_folder "/Users/collado/Repos/stuff/docker-virt-net",
    "/docker-virt-net", "nfs" => { :mount_options => ['dmode=777', 'fmode=777'] }

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--memory", 1024]
  end

  config.vm.define "testvm" do |testvm|
    testvm.vm.hostname = 'testvm'
    testvm.vm.network :private_network, ip: "10.0.123.2"
  end
end
