patchurl=http://almrepo.us.oracle.com/artifactory/opc-woodhouse-release/com/oracle/dbcloud/pod/16.3.2-20160618-3148/pod-16.3.2-20160618-3148.zip
release=16.3.2
component=cloud_pod
env=HAGA
fab -f download_patch.py excute_download:patchlist=$patchurl,release=$release,component=$component 2>&1 | tee -a ./logs/${env}_${component}_${release}.log
fab -f deploy_patch_addlog_addrestart.py set_hosts:component=$component,envname=$env excute_upgrade:component=$component,envname=$env,release=$release,patch=$patchurl 2>&1 | tee -a ./logs/${env}_${component}_${release}.log
