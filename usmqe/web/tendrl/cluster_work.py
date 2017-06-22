"""
Description: Simple cluster auxiliary methods

Author: ltrilety
"""

import pytest

from webstr.selenium.ui.support import WebDriverUtils
from usmqe.web.tendrl.mainpage.navpage.pages import NavMenuBars
from usmqe.web.tendrl.mainpage.clusters.cluster_list.pages import\
    ClustersList, ClustersMenu
from usmqe.web.tendrl.landing_page.pages import get_landing_page
from usmqe.web.tendrl.auxiliary.pages import UpperMenu
from usmqe.web.tendrl.mainpage.clusters.import_cluster_wizard.pages\
    import ImportCluster
from usmqe.web.tendrl.mainpage.clusters.cluster.pages import ClusterMenu
from usmqe.web.tendrl.task_wait import task_wait
from usmqe.web.tendrl.clusters import check_hosts


IMPORT_TIMEOUT = 3600


def import_cluster_wait(driver):
    """
    wait till the import cluster task is finished

    Parameters:
        driver: selenium driver
        ttl (int): how long it waits till the tasks is finished
                   in seconds

    Returns:
        list of cluster objects
    """
    # Wait till the cluster is imported
    task_wait(ttl=IMPORT_TIMEOUT)

    NavMenuBars(driver).open_clusters(click_only=True)

    # TODO remove following sleep
    # sleep a while because of https://github.com/Tendrl/api/issues/159
    WebDriverUtils.wait_a_while(90, driver)

    cluster_list = ClustersList(driver)
    return cluster_list


def import_selected_cluster(driver, import_page, clusters_nr=0,
                            cluster_name=None, hosts=None):
    """
    import SELECTED cluster

    Parameters:
        driver: selenium driver
        import_page: instance of ImportCluster
        clusters_nr (int): number of clusters in clusters list
        cluster_name (str): name of the cluster
                            TODO: Not used for now
                                  https://github.com/Tendrl/api/issues/70
        hosts (list): list of dictionaries
                      {'hostname': <hostname>, 'release': <release>, ...
                      for check only

    Returns:
        cluster name or id
    """
    (cluster_ident, hosts_list) = import_page.import_cluster(
        name=cluster_name, hosts=hosts)

    cluster_list = import_cluster_wait(driver)

    # Check that cluster is present in the list
    pytest.check(len(cluster_list) == clusters_nr + 1,
                 'There should be one additional cluster in tendrl')
    # open cluster details for the imported cluster
    present = False
    for cluster in cluster_list:
        if cluster_ident.lower() in cluster.name.lower():
            cluster.open_details()
            present = True
            break
    pytest.check(present,
                 'The imported cluster should be present in the cluster list')

    # check hosts
    if present:
        page_hosts_list = ClusterMenu(driver).open_hosts()
        check_hosts(hosts_list, page_hosts_list)
    return cluster_ident


def choose_cluster(driver, cluster_type=None):
    """
    select a cluster which should be imported

    Parameters:
        driver: selenium driver
        cluster_type (str): which type of cluster should be imported
                                'ceph' or 'gluster'
                            None means that cluster type doesn't matter

    Returns:
        ImportCluster instance
    """
    # Choose which cluster should be imported
    import_page = ImportCluster(driver)
    if cluster_type is None:
        pytest.check(len(import_page.avail_clusters) > 0,
                     'There should be some cluster available',
                     hard=True)
    elif cluster_type.lower() == 'gluster':
        # Select first gluster cluster in the list of available clusters
        for cluster in import_page.avail_clusters:
            cluster.click()
            release = import_page.storage_service.lower()
            if 'gluster' in release:
                break
            pytest.check('gluster' in release,
                         'There should be some gluster cluster available',
                         hard=True)
    elif cluster_type.lower() == 'ceph':
        # Select first ceph cluster in the list of available clusters
        for cluster in import_page.avail_clusters:
            cluster.click()
            release = import_page.storage_service.lower()
            if 'ceph' in release:
                break
        pytest.check('ceph' in release,
                     'There should be some ceph cluster available',
                     hard=True)
    else:
        pytest.check(False, 'Unknown cluster type - {}'.format(cluster_type),
                     hard=True)

    return import_page


def initial_import_cluster(driver, init_object, login_page,
                           cluster_type=None):
    """
    positive import cluster test

    NOTE: 1. No cluster has to be imported
          2. There has to be at least one cluster which could be imported

    Parameters:
        driver: selenium driver
        init_object: WebstrPage instance of page which is loaded after log in
        login_page: LoginPage instance
        cluster_type (str): which type of cluster should be imported
                                'ceph' or 'gluster'
                            None means that cluster type doesn't matter
    """
    pytest.check(init_object._label == 'home page',
                 'Tendrl should route to home page'
                 ' if there is no cluster present',
                 hard=True)

    init_object.start_import_cluster()

    import_page = choose_cluster(driver, cluster_type)

    cluster_ident = import_selected_cluster(driver, import_page)

    # log out and log in again
    upper_menu = UpperMenu(driver)
    upper_menu.open_user_menu().logout()
    login_page.login_user(
        pytest.config.getini("usm_username"),
        pytest.config.getini("usm_password"))
    # or just go to the default URL
    # driver.get(pytest.config.getini("usm_web_url"))
    home_page = get_landing_page(driver)

    pytest.check(home_page._label == 'main page - menu bar',
                 'Tendrl should not route to home page any more',
                 hard=True)

    # Check that cluster is present in the list
    NavMenuBars(driver).open_clusters(click_only=True)
    clusters_list = ClustersList(driver)

    pytest.check(len(clusters_list) == 1,
                 'There should be exactly one cluster in tendrl')
    present = False
    for cluster in clusters_list:
        if cluster_ident.lower() in cluster.name.lower():
            present = True
            break
    pytest.check(present,
                 'The imported cluster should be present in the cluster list')


def import_cluster(driver, init_object, cluster_type=None):
    """
    positive import cluster test

    NOTE: 1. Some cluster has to be already present in the list
          2. There has to be at least one cluster which could be imported

    Parameters:
        driver: selenium driver
        init_object: WebstrPage instance of page which is loaded after log in
        cluster_type (str): which type of cluster should be imported
                                'ceph' or 'gluster'
                            None means that cluster type doesn't matter
    """
    pytest.check(init_object._label == 'main page - menu bar',
                 'Tendrl should route to dashboard page',
                 hard=True)
    clusters_list = init_object.open_clusters()
    clusters_nr = len(clusters_list)
    cluster_menu = ClustersMenu(driver)

    cluster_menu.start_import_cluster()

    import_page = choose_cluster(driver, cluster_type)

    import_selected_cluster(driver, import_page, clusters_nr)


def import_cluster_x(driver, init_object, login_page, cluster_type=None):
    """
    positive import cluster test

    NOTE: There has to be at least one cluster which could be imported

    Parameters:
        driver: selenium driver
        init_object: WebstrPage instance of page which is loaded after log in
        login_page: LoginPage instance
        cluster_type (str): which type of cluster should be imported
                                'ceph' or 'gluster'
                            None means that cluster type doesn't matter
    """
    if init_object._label == 'home page':
        initial_import_cluster(driver, init_object, login_page, cluster_type)
    else:
        import_cluster(driver, init_object, cluster_type)


# TODO create
#   def create_cluster(...