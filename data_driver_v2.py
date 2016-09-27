#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#       Filename: data-driver.py
#
#         Author: xwisen 1031649164@qq.com
#    Description: ---
#         Create: 2016-08-26 08:52:11
#  Last Modified: 2016-08-26 08:52:11
# ***********************************************

import os
import httplib2
import json

# marathon_name 信息
marathon_name = os.environ.get("MARATHON_NAME", "marathon")

# prometheus config 苏研
promethus_ip_addr = os.environ.get("PROMETHEUS_IP_ADDR", "10.254.10.18")
promethus_port = os.environ.get("PROMETHEUS_PORT", "9092")
promethus_group = os.environ.get("PROMETHEUS_GROUP", "slave")
promethus_job = os.environ.get("PROMETHEUS_JOB", "dcos")

# prometheus config 移动
# promethus_ip_addr = os.environ.get("PROMETHEUS_IP_ADDR", "20.26.25.148")
# promethus_port = os.environ.get("PROMETHEUS_PORT", "9090")
# promethus_group = os.environ.get("PROMETHEUS_GROUP", "slave")
# promethus_job = os.environ.get("PROMETHEUS_JOB", "cadvisor")

error_status = {"succeed": 0,
                "mem_error": 1,
                "cpu_error": 2,
                "haproxy_error": 3,
                "thread_error": 4,
                "other_error": 9}


def data_driver(driver_type, marathon_info, app_id, quotas):
    """
    data_driver return specified application information
    application information is a dict, include:
    :param driver_type: eg:influxdb or prometheus
    :param marathon_info: eg:10.254.9.57
    :param app_id: eg:nginx
    :return:
    """
    err_info = {"marathon_info": marathon_info,
                "app_id": app_id,
                "status": error_status["other_error"],
                "error": "driver not support!"}

    if driver_type == "prometheus":
        return prometheus_driver(marathon_info, app_id, quotas)
    else:
        print(driver_type, "driver_type is not support,\
         only influxdb and prometheus support!")
        return err_info

def prometheus_driver(marathon_info, app_id, quotas):
    # marathon_info like :
    # 10.254.9.57 or www.marathon.com

    conn = httplib2.Http()
    headers = {"Content-type": "application/json"}
    marathon_app_url = "http://" + marathon_info + ":8080/v2/apps/" + app_id
    prometheus_url = "http://" + promethus_ip_addr + \
                     ":" + promethus_port + "/api/v1/query?"
    #cpu_query = "query=avg+by+(marathonName%2Cmarathon_app_id)+(irate(container_cpu_system_seconds_total%7BmarathonName%3D%27"+ marathon_name + "%27%2Cmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%5B5m%5D))+%2B+avg+by+(marathonName%2Cmarathon_app_id)+(irate(container_cpu_user_seconds_total%7BmarathonName%3D%27"+ marathon_name + "%27%2Cmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%5B5m%5D))"

    #mem_query = "query=avg+by+(marathonName%2Cmarathon_app_id)(container_memory_usage_bytes%7BmarathonName%3D%27"+ marathon_name + "%27%2Cmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%2Fcontainer_spec_memory_limit_bytes%7BmarathonName%3D%27"+ marathon_name + "%27%2Cmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D)%0A"

    #haproxy_backend_current_queue_query = "query=haproxy_server_current_queue%7Bbackend%3D~%22%5E" + app_id + "_"+ marathon_name + "_.*%22%7D"

   # thread_query = "query=tomcat_threadRunning%7BmarathonName%3D%22" + marathon_name + "%22%2CappId%3D%22" + app_id + "%22%7D"
    cpu_query = "query=avg+by+(marathon_app_id)+(irate(container_cpu_system_seconds_total%7Bmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%5B3m%5D))+%2B+avg+by+(marathon_app_id)+(irate(container_cpu_user_seconds_total%7Bmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%5B3m%5D))"

    mem_query = "query=avg+by+(marathon_app_id)(container_memory_usage_bytes%7Bmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D%2Fcontainer_spec_memory_limit_bytes%7Bmarathon_app_id%3D%27%2F" + app_id + "%27%2Cid%3D~%27%5E%2Fdocker.*%27%7D)"

    haproxy_backend_current_queue_query = "query=haproxy_server_current_queue%7Bbackend%3D~%27%5E" + app_id + ".*%27%7D"

    thread_query = "query=tomcat_threadRunning%7BappId%3D%22 + app_id + %22%7D"


    task_num =-1
    avg_cpu=-1
    avg_mem=-1
    ha_queue=-1
    haproxy_backend_current_queue=-1
    thread=-1
    #if "app_task_num" in quotas:
        # try to get tasks number
    try:
        print (marathon_app_url)
        response, content = conn.request(marathon_app_url,
                                         "GET", headers=headers)
    except Exception as e:
        print (Exception, ":", e)
        return e
    else:
        # print(response.status)
        if response.status != 200:
            return {"marathon_info": marathon_info,
                    "app_id": app_id,
                    "status": error_status["other_error"],
                    "error": "get app task number response code " + str(response.status) + " found!"}
        else:
            resp_json = json.loads(content)
            # print(resp_json)
            task_num = len(resp_json["app"]["tasks"])
            # print (task_num)
    if "cpu" in quotas:
        # try to get average cpu if need
        try:
            #print (prometheus_url + cpu_query)
            response, content = conn.request(prometheus_url + cpu_query,
                                             "GET", headers=headers)
        except Exception as e:
            print (Exception, ":", e)
            return e
        else:
            # print(response.status)
            if response.status != 200:
                return {"marathon_info": marathon_info,
                        "app_id": app_id,
                        "status": error_status["cpu_error"],
                        "error": "get average cpu response code " \
                                 + str(response.status) + " found!"}
            else:
                resp_json = json.loads(content)
                # print(resp_json)
                if resp_json["data"]["result"] == []:
                    return {"marathon_info": marathon_info,
                            "app_id": app_id,
                            "status": error_status["cpu_error"],
                            "error": "prometheus average cpu response\
                             .data.result don't have value, please check"}
                avg_cpu = resp_json["data"]["result"][0]["value"][1]
    if "memory" in quotas:
        # try to get average memory if need
        try:
            #print (prometheus_url + mem_query)
            response, content = conn.request(prometheus_url + mem_query,
                                             "GET", headers=headers)
        except Exception as e:
            print (Exception, ":", e)
            return e
        else:
            # print(response.status)
            if response.status != 200:
                return {"marathon_info": marathon_info,
                        "app_id": app_id,
                        "status": error_status["mem_error"],
                        "error": "get average memory response code "
                                 + str(response.status) + " found!"}
            else:
                resp_json = json.loads(content)
                # print(resp_json)
                if resp_json["data"]["result"] == []:
                    return {"marathon_info": marathon_info,
                            "app_id": app_id,
                            "status": error_status["mem_error"],
                            "error": "prometheus average mem response\
                             .data.result don't have value, please check"}
                avg_mem = resp_json["data"]["result"][0]["value"][1]

    if "ha_queue" in quotas:
        # try to get app haproxy_backend_current_queue if need

        try:
            #print (prometheus_url + haproxy_backend_current_queue_query)
            response, content = conn.request(prometheus_url +
                                             haproxy_backend_current_queue_query,
                                             "GET", headers=headers)
        except Exception as e:
            print (Exception, ":", e)
            return e
        else:
            # print(response.status)
            if response.status != 200:
                return {"marathon_info": marathon_info,
                        "app_id": app_id,
                        "status": error_status["haproxy_error"],
                        "error": "get haproxy_backend_current_queue response code "
                                 + str(response.status) + " found!"}
            else:
                resp_json = json.loads(content)
                # print(resp_json)
                if resp_json["data"]["result"] == []:
                    return {"marathon_info": marathon_info,
                            "app_id": app_id,
                            "status": error_status["mem_error"],
                            "error": "prometheus haproxy_backend_current_queue\
                             .data.result don't have value, please check"}
                haproxy_backend_current_queue = resp_json["data"]["result"][0]["value"][1]
    if "thread" in quotas:
        # try to get app thread if need
        try:
            #print (prometheus_url + thread_query)
            response, content = conn.request(prometheus_url +
                                             thread_query, "GET", headers=headers)
        except Exception as e:
            print (Exception, ":", e)
            return e
        else:
            # print(response.status)
            if response.status != 200:
                return {"marathon_info": marathon_info,
                        "app_id": app_id,
                        "status": error_status["thread_error"],
                        "error": "get thread response code "
                                 + str(response.status) + " found!"}
            else:
                resp_json = json.loads(content)
                # print(resp_json)
                if resp_json["data"]["result"] == []:
                    return {"marathon_info": marathon_info,
                            "app_id": app_id,
                            "status": error_status["mem_error"],
                            "error": "prometheus thread\
                             .data.result don't have value, please check"}
                thread = resp_json["data"]["result"][0]["value"][1]

    return {"marathon_info": marathon_info,
            "app_id": app_id,
            "status": error_status["succeed"],
            "app_task_num": task_num,
            "cpu": int(float(avg_cpu) * 100),
            "memory": int(float(avg_mem) * 100),
            "ha_queue": int(haproxy_backend_current_queue),
            "thread":int(thread)
            }


if __name__ == "__main__":
    # print (data_driver("prometheus", "10.254.9.57", "wz-app" ,["app_task_num","cpu","memory","ha_queue","thread"]))
    print (data_driver("prometheus", "10.254.9.57", "jenkins" ,["cpu"]))
