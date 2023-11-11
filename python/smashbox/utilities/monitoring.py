from smashbox.utilities import reflection, config, os
import smashbox.utilities

def push_to_local_monitor(metric, value):
    print metric, value

def commit_to_monitoring(metric,value,timestamp=None):
    shared = reflection.getSharedObject()
    if not 'monitoring_points' in shared.keys():
        shared['monitoring_points'] = []

    # Create monitoring metric point
    monitoring_point = dict()
    monitoring_point['metric'] = metric
    monitoring_point['value'] = value
    monitoring_point['timestamp'] = timestamp

    # Append metric to shared object
    monitoring_points = shared['monitoring_points']
    monitoring_points.append(monitoring_point)
    shared['monitoring_points'] = monitoring_points

def handle_local_push(returncode, total_duration, monitoring_points):
    for monitoring_point in monitoring_points:
        push_to_local_monitor(monitoring_point['metric'], monitoring_point['value'])
    push_to_local_monitor("returncode", returncode)
    push_to_local_monitor("elapsed", total_duration)

def handle_prometheus_push(returncode, total_duration, monitoring_points):
    monitoring_endpoint = config.get('endpoint', None)
    release = config.get('owncloud', None)
    client = config.get('client', None)
    suite = config.get('suite', None)
    build = config.get('build', None)
    duration_label = config.get('duration_label', None)
    queries_label = config.get('queries_label', None)

    points_to_push = []

    # total duration is default for jenkins if given
    if duration_label is not None:
        points_to_push.append('# TYPE %s gauge' % (duration_label))
        points_to_push.append('%s{owncloud=\\"%s\\",client=\\"%s\\",suite=\\"%s\\",build=\\"%s\\",exit=\\"%s\\"} %s' % (
            duration_label,
            release,
            client,
            suite,
            build,
            returncode,
            total_duration))

    # No. queries is default for jenkins if given
    if queries_label is not None:
        no_queries = 0
        res_diagnostic_logs = smashbox.utilities.get_diagnostic_log()
        for diagnostic_log in res_diagnostic_logs:
            if 'diagnostics' in diagnostic_log and 'totalSQLQueries' in diagnostic_log['diagnostics']:
                no_queries += int(diagnostic_log['diagnostics']['totalSQLQueries'])

        points_to_push.append('# TYPE %s gauge' % (queries_label))
        points_to_push.append('%s{owncloud=\\"%s\\",client=\\"%s\\",suite=\\"%s\\",build=\\"%s\\",exit=\\"%s\\"} %s' % (
            queries_label,
            release,
            client,
            suite,
            build,
            returncode,
            no_queries))

    # Export all commited monitoring points
    for monitoring_point in monitoring_points:
        points_to_push.append('# TYPE %s gauge' % (monitoring_point['metric']))
        points_to_push.append('%s{owncloud=\\"%s\\",client=\\"%s\\",suite=\\"%s\\",build=\\"%s\\",exit=\\"%s\\"} %s' % (
            monitoring_point['metric'],
            release,
            client,
            suite,
            build,
            returncode,
            monitoring_point['value']))

    # Push to monitoring all points to be pushed
    cmd = ''
    for point_to_push in points_to_push:
        cmd += point_to_push + '\n'

    monitoring_cmd = 'echo "%s" | curl --data-binary @- %s\n' % (cmd, monitoring_endpoint)
    os.system(monitoring_cmd)
    smashbox.utilities.log_info('Pushing to monitoring: %s' % monitoring_cmd)

def push_to_monitoring(returncode, total_duration):
    monitoring_points = []
    shared = reflection.getSharedObject()
    if 'monitoring_points' in shared.keys():
        monitoring_points = shared['monitoring_points']

    monitoring_type = config.get('monitoring_type', None)
    if monitoring_type == 'prometheus':
        handle_prometheus_push(returncode, total_duration, monitoring_points)
    elif monitoring_type == 'local':
        handle_local_push(returncode, total_duration, monitoring_points)