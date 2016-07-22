# -*- mode: ruby -*-
# vi: set ft=ruby :

# Script to run Salt provisioning.  Pass the minion id from top.sls for the
# type of instance you want to build.
$salt = <<SCRIPT
sudo salt-call --local state.highstate --file-root=/vagrant/salt_stack/salt --pillar-root=/vagrant/salt_stack/pillar --id=$1
SCRIPT

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.

  config.vm.define "vault" do |vault|
    vault.vm.box = "packer/output/vagrant-virtualbox-vault.box"
  end

  config.vm.define "endpoint" do |endpoint|
    endpoint.vm.box = "packer/output/vagrant-virtualbox-endpoint.box"
  end

  config.vm.define "epj" do |epj|
    epj.vm.box = "packer/output/vagrant-virtualbox-pr-jenkins.box"
    epj.vm.network "forwarded_port", guest: 8080, host: 8080
    epj.vm.network "forwarded_port", guest: 8888, host: 8888
    epj.vm.synced_folder "../boss", "/boss"
    epj.vm.synced_folder "../spdb", "/spdb"
    epj.vm.synced_folder "../boss-tools", "/boss-tools"
    epj.vm.synced_folder "../ndio", "/ndio"
    epj.vm.provision "shell" do |s|
      s.inline = $salt
      s.args = ["ep-jenkins"]
    end
  end

  config.vm.define "proofreader" do |proofreader|
    proofreader.vm.box = "packer/output/vagrant-virtualbox-proofreader-web.box"
    proofreader.vm.network "forwarded_port", guest: 8080, host: 8080
  end

  config.vm.define "prj" do |prj|
    prj.vm.box = "packer/output/vagrant-virtualbox-pr-jenkins.box"
    prj.vm.network "forwarded_port", guest: 8080, host: 8080
    prj.vm.synced_folder "../proofread", "/proofread"
    prj.vm.provision "shell" do |s|
      s.inline = $salt
      s.args = ["pr-jenkins"]
    end
  end

  config.vm.define "desktop" do |desktop|
    desktop.vm.box = "virtualbox_ubuntu_desktop.box"
    desktop.vm.synced_folder "../boss-tools", "/boss-tools"
  end

  # We use the microns account instead of vagrant for login.
  # We use the microns account instead of vagrant for login.
  config.ssh.username = "microns"
  config.ssh.password = "microns"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  # config.vm.provision "shell", inline: <<-SHELL
  #   sudo apt-get update
  #   sudo apt-get install -y apache2
  # SHELL
end
