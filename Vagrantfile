# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'

# puts File.expand_path(File.dirname(__FILE__)) + '/cluster.yaml'
# abort()

class ::Hash
  def deep_merge(second)
    merger = proc { |key, v1, v2| Hash === v1 && Hash === v2 ? 
      v1.merge(v2, &merger) : v2 }
    self.merge(second, &merger)
  end
end

cluster = YAML::load(open(File.expand_path(File.dirname(__FILE__)) + 
                     '/cluster.yaml'))
cluster['nodes'].each { |k,v| cluster['nodes'][k] =
    Marshal.load(Marshal.dump(cluster['defaults'])).deep_merge(v) }
cluster = cluster['nodes']

ANSIBLE_GROUPS = Hash.new
cluster.each do |n, ps|
  unless ps['net']['ip'].nil?
    ps['ansible_groups'] << 'multicast'
  end
  ps['ansible_groups'].each do |group|
    unless ANSIBLE_GROUPS.key?(group)
      ANSIBLE_GROUPS[group] = Array.new
    end
    ANSIBLE_GROUPS[group] << n
  end
end

# puts cluster
# puts ANSIBLE_GROUPS

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.ssh.forward_agent = true
  config.ssh.insert_key = false

  cluster.each_with_index do |(name, props), index|
    config.vm.define name do |member|
      member.vm.box = 'base'

      # Network basics
      if props['net']['ip']
        member.vm.hostname = name + props['net']['tld']
        member.vm.network props['net']['type'], ip: props['net']['ip'],
            auto_configure: props['net']['auto']
      end

      props['ports'].each do |guestp, hostp|
        member.vm.network "forwarded_port", guest: guestp, host: hostp
      end

      props['volumes'].each do |guestv, hostv|
        member.vm.synced_folder hostv, guestv
      end

      member.vm.provider 'virtualbox' do |v, override|
        v.gui = props['gui']
        override.vm.box = props['box']['virtualbox']
        v.memory = props['memory']
        v.customize ['modifyvm', :id, '--natdnshostresolver1', 'on']
        v.customize ['modifyvm', :id, '--natdnsproxy1', 'on']
      end

      member.vm.provider 'vmware_fusion' do |v, override|
        v.gui = props['gui']
        override.vm.box = props['box']['vmware_fusion']
        v.vmx['memsize'] = props['memory']
        v.vmx['numvcpus'] = props['cpu']
        v.vmx['vhv.enable'] = 'TRUE'
      end

      # Provision on last box
      if index == cluster.length - 1
        member.vm.provision 'ansible' do |ansible|
          # ansible.verbose = 'vvvv'
          ansible.groups = ANSIBLE_GROUPS
          ansible.playbook = 'ansible/site.yaml'
          ansible.sudo = true
          ansible.limit = 'all'
          ansible.extra_vars = {
            multicast: props['net']['multicast']
          }
        end
      end
    end
  end
end
