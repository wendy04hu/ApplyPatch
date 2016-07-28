from fabric.api import *
from fabric.context_managers import *
from fabric.contrib.files import exists


env.hosts=['slce30cn17']
env.user='oracle'
env.password='oracle123'
remote_patch_dir='/home/oracle/installer'
local_patch_dir="./download_patch"

def init_dir(release, component):
    if exists('%s/%s' % (remote_patch_dir,release)):
       print 'dir %s has already existed' % release
    else:
       print 'creating folder %s' % release
       run("mkdir -p %s/%s" %(remote_patch_dir, release))
    local("mkdir -p %s/%s" %(local_patch_dir,component))


def put_patch_to_local(local_patch_dir, remote_patch_dir, patch_name):
  get(("%s/%s" %(remote_patch_dir, patch_name)), local_patch_dir)

#copy patch from rm wiki to dst_patch_dir/release and unzip it to folder with
#name component
#patch: where to get upgrading patch
#dst_patch_dir: where to save patch in host
#release: the upgrading version
def get_patch_from_rm(patch, release, component):
    print "copy patch from rmwiki to host aaaaaaaaaa"
    with cd('%s/%s' % (remote_patch_dir, release)):
        print("downloading patch from rm wiki")
        if(patch.find("http") != -1):
            print("downloading .................")
            run('wget %s' %(patch))
        else:
            run("cp %s ." %(patch))
        patch_name=patch.rsplit('/', 1)[-1]
        put_patch_to_local(local_patch_dir+"/"+component, remote_patch_dir+"/"+release, patch_name)

def get_patchlist_from_rm(patchlist, release, component):
    print "copy patchlist from rmwiki to host"
#    print("%s" %(patchlist))
    with cd('%s/%s' % (remote_patch_dir, release)):
        for patch in patchlist:
            if(patch.find("http") != -1):
                run('wget %s' %(patch))
            else:
                run("cp %s ." %(patch))
            patch_name=patch.rsplit('/', 1)[-1]
            put_patch_to_local(local_patch_dir+"/"+component, remote_patch_dir+"/"+release, patch_name)

def excute_download(patchlist, release, component):
    init_dir(release, component)
    patchlist=patchlist .split("#")
    print("%s" %(patchlist))
    if len(patchlist) == 1:
        get_patch_from_rm(patchlist[0], release, component)
    else:
        get_patchlist_from_rm(patchlist, release, component)

