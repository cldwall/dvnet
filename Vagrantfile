VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/focal64"
  # config.ssh.forward_agent = true
  # config.ssh.forward_x11 = true
  config.vm.provider "virtualbox" do |v|
  v.customize ["modifyvm", :id, "--memory", 1024]
  end

  config.vm.define "testvm" do |testvm|
    testvm.vm.hostname = 'testvm'
    testvm.vm.network :private_network, ip: "10.0.123.2"
  end
end
