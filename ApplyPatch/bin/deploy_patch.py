from fabric.colors import green,red,blue,cyan,yellow

#which hosts needs applied this patch
#component: cloud_pod/cloud_dc/cloud_central
#env: which env needs to be copied
#return hosts_list


def initLoggerWithRotate():
    logname=''.join(env.host.split('.'))+'.log'
    logFileName="logs/%s"%logname
    logger = logging.getLogger("fabric")
    formater = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s","%Y-%m-%d %H:%M:%S")
    file_handler = logging.handlers.RotatingFileHandler(logFileName, maxBytes=104857600, backupCount=5)
    file_handler.setFormatter(formater)
    stream_handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    return logger

def get_hosts_list(component, envname):
    hosts_map={}
    f = open(("./config/prop/%s" % envname), "r")
    for line in f:
        line=line.split()
        if(len(line) != 0):
            if(line[0].find(component) != -1):
                hosts_map[line[1]] = line
    f.close()
    return hosts_map

def set_hosts(component, envname):
    env.hosts=[]
    env.passwords={}
    hosts_map=get_hosts_list(component, envname)
    for each_host_name in hosts_map:
        hosts_list = hosts_map[each_host_name]
        host_name=hosts_list[1]
        host_user=hosts_list[2]
        host_password=hosts_list[3]
        login_host=host_user+"@"+host_name+":22"
        env.hosts.append(login_host)
        env.passwords[login_host]=host_password


def put_patch_to_remote(local_patch_dir, remote_patch_dir, patch):
#    hosts_map=get_hosts_list(component, envname)
#    hosts_list = hosts_map[env.host]
#    print("%s" % hosts_list)
#    host_patch_dir = hosts_list[4]
    if exists("%s" % (remote_patch_dir)):
        pass
    else:
        print("create dir %s" %(remote_patch_dir))
        run("mkdir -p %s" % (remote_patch_dir))
    patch_name=patch.rsplit("/", 1)[-1]
    put(local_patch_dir+"/"+patch_name, remote_patch_dir)
    with cd("%s" %(remote_patch_dir)):
        run("unzip -o -q %s" %(patch_name))

def put_patchlist_to_remote( local_patch_dir, remote_patch_dir, patchlist):
    prev_jar_list=[]
    #for .jar file
    with cd("%s" %(remote_patch_dir)):
        for patch in patchlist:
            patch_name=patch.rsplit("/", 1)[-1]
            put(local_patch_dir+"/"+patch_name, remote_patch_dir)
            run("unzip -o %s" %(patch_name))
            run("unzip -o %s -d ./tmp" %(patch_name))
            curr_jar_list=run("ls ./tmp | grep .*.jar").split()
            prev_jar_list.extend(list(set(curr_jar_list).difference(set(prev_jar_list))))
    run("rm -rf %s/tmp" %(remote_patch_dir))
    return prev_jar_list

def restart_ohs(ohs_name):
    with cd('/u01/wls/Oracle_WT1/instances/%s/bin' %(ohs_name)):
        ohs_status=run("./opmnctl status")
        if(ohs_status.find('Alive') != -1):
           run("./opmnctl stopall")
        run("./opmnctl startall")
        run("./opmnctl status")

#release: upgrade version
#patch: where to get upgrading patch
#component: option like cloud_pod/cloud_central/cloud_dc
#db_config_dir: the upgrading config file
#patch_dir where to save upgrading patch/home/oracle/installer
def upgrade_process(patch_dir, release, component, db_config_dir, logger, hosts_list):
    with cd('%s' % (patch_dir)):
          logger.info( green(run('cp -r %s/%s/*.txt install/' % (db_config_dir, component))))
          result = run('ls %s/%s/ | grep txt' % (db_config_dir, component))
          config_file=result.split()
          for i in range(len(config_file)):
              if(config_file[i].endswith(".txt")):
                  logger.info(green( "upgrading db of %s pod" %(config_file[i])))
                  with settings(warn_only=True):
                      run('./apply_patch.sh install/%s 2>&1|tee -a pod.log' % (config_file[i]))
    print("%s" %(hosts_list))
    if(hosts_list[0].find("ohs") != -1):
        restart_ohs(hosts_list[6])

def format_jarlist(jar_list):
   jar_str=''
   for jarname in jar_list:
      if(jarname.endswith('.jar')):
          jar_str += jarname.split('.')[0] + ','
   return jar_str[0:len(jar_str)-1]


def upgrade_process_mwls(app_patch_dir, release, jar_patch_dir, jarname_list):
    with shell_env(suwrapper_path=("%s/%s" %(app_patch_dir, release)),OracleHome=("%s" %(jar_patch_dir))):
        run("echo $suwrapper_path $OracleHome")
        jar_str=format_jarlist(jarname_list)
        run(("java -jar $suwrapper_path/bsu-wrapper.jar -meta=$suwrapper_path/suw_metadata.txt "
             "-bsu_home=$OracleHome/utils/bsu -install -verbose -patchlist=%s "
              "-patch_download_dir=$OracleHome/utils/bsu/cache_dir -prod_dir=$OracleHome/wlserver_10.3 "
              "-out=$suwrapper_path/suwrapper.out") %(jar_str))

def excute_upgrade(component, envname, release, patch):
    hosts_map = get_hosts_list(component, envname)
    hosts_list = hosts_map[env.host]
    host_prop_name=hosts_list[0]
    app_patch_dir=hosts_list[4]
    jar_patch_dir=hosts_list[5]
    patchlist=patch.split("#")
    local_patch_dir="./download_patch/%s" %(component)
    remote_patch_dir="%s/%s" %(app_patch_dir, release)
    logger=initLoggerWithRotate()
    if (len(patchlist)== 1) :
        logger.info(green("put patch from local to remote %s" %(env.host)))
        put_patch_to_remote(local_patch_dir, remote_patch_dir, patch)
        app_patch_dir="%s/%s/%s" %(app_patch_dir,release, component)
        logger.info(green("[start] upgrading process on host %s" %(env.host)))
        upgrade_process(app_patch_dir, release, component, jar_patch_dir, logger, hosts_list)
        logger.info(green("[end] upgrading process on host %s" %(env.host)))

    else:
        put_patch_to_remote(local_patch_dir, remote_patch_dir, patchlist[0])
        patchlist.remove(patchlist[0])
        jarname_list=put_patchlist_to_remote(local_patch_dir, jar_patch_dir+"/utils/bsu/cache_dir/",patchlist)
        upgrade_process_mwls(app_patch_dir, release, jar_patch_dir, jarname_list)
