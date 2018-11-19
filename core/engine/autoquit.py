def autoquit_run(tapi):
    for user in tapi.db_shell.get_ready_for_autoquit():
        pers_id = int(user['pers_id'])
        for worker in tapi.workers_list:
            worker.quit(pers_id, pers_id, "You was inactive for a long time.\n")

#TODO: It is just an example of the autoquit system.
